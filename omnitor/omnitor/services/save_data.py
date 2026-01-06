import os
import sys
import time
import django

from django.db import connection, close_old_connections
from django.db.models import Sum
from django.utils import timezone

from .filtering import maf_all

# 전역 변수
tip_capacity = 5  # 티핑 게이지 한번 당 배액량 = 5 ml
prev_weight = 0.0  # 이전 무게 값 (관수량 계산용)

def save_rawdata(gpio, soil, water):

    """
    센서 데이터를 읽어 RawData에 저장
    """

    print(f"[rawdata] save_rawdata start {timezone.now()}", flush=True)

    from omnitor.models import RawData

    try:
        # close_old_connections()

        try:
            rpi_data = gpio.get_current_data()
        except Exception:
            rpi_data = None
            print("[rawdata] GPIO Read Error", flush=True)

        try:
            soil_data = soil.get_current_data()
        except Exception:
            soil_data = None
            print("[rawdata] Soil Read Error", flush=True)

        try:
            water_data = water.get_current_data()
        except Exception:
            water_data = None
            print("[rawdata] Water Read Error", flush=True)

        if not any([rpi_data, soil_data, water_data]):
            print("[rawdata] All sensors are offline. Skip DB save.", flush=True)
            return
                
        RawData.objects.create(
            timestamp=timezone.now(),
            air_temperature=rpi_data.get('temperature') if rpi_data else None,
            air_humidity=rpi_data.get('humidity') if rpi_data else None,
            co2=rpi_data.get('co2') if rpi_data else None,
            insolation=rpi_data.get('insolation') if rpi_data else None,
            weight=rpi_data.get('weight') if rpi_data else None,
            tip_count=rpi_data.get('tip_count') if rpi_data else None,
            water_ph=water_data.water_ph if water_data else None,
            water_ec=water_data.water_ec if water_data else None,
            water_temperature=water_data.water_temperature if water_data else None,
            soil_temperature=soil_data.soil_temperature if soil_data else None,
            soil_humidity=soil_data.soil_humidity if soil_data else None,
            soil_ec=soil_data.soil_ec if soil_data else None,
            soil_ph=soil_data.soil_ph if soil_data else None
        )

        # raw_data=RawData.objects.latest('timestamp')

        # print(f"[DEBUG] RawData DB save at {now.strftime('%H:%M:%S')}: {raw_data}", flush=True)
            
    except Exception as e:
        print(f"[RawData Error] {e}")

def save_finaldata():
    """
    RawData -> 필터링 & 보정 -> FinalData
    설정이 없으면(Raw=Final) 기울기 1, 절편 0 적용
    """

    # print(f"[save_final] save_finaldata start {timezone.now()}", flush=True)

    global prev_weight
    from omnitor.models import RawData, CalibrationSettings, FinalData
    from . import save_calibrationsettings

    try:
        close_old_connections() 
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        # RawData 가져오기
        try:
            raw_latest = RawData.objects.latest('timestamp')
        except RawData.DoesNotExist:
            print("[finaldata] RawData does not exist.")
            return

        # 필터링 (최근 데이터 이동 평균 필터)
        filtered_data = maf_all()

        # 필터링 데이터가 없으면 최신 RawData 사용
        if not filtered_data:
            filtered_data = {
                'air_temperature': raw_latest.air_temperature,
                'air_humidity': raw_latest.air_humidity,
                'co2': raw_latest.co2,
                'insolation': raw_latest.insolation,
                'weight': raw_latest.weight,
                'water_temperature': raw_latest.water_temperature,
                'water_ph': raw_latest.water_ph,
                'water_ec': raw_latest.water_ec,
                'soil_temperature': raw_latest.soil_temperature,
                'soil_humidity': raw_latest.soil_humidity,
                'soil_ec': raw_latest.soil_ec,
                'soil_ph': raw_latest.soil_ph
            }

        # 보정 설정 가져오기
        try:
            cal_settings = CalibrationSettings.objects.get(id=1)
            # print(f"[finaldata] DB Settings Loaded: {cal_settings.__dict__}")
        except CalibrationSettings.DoesNotExist:
            cal_settings = None

        # DB에 설정이 없으면 '기울기 1, 절편 0'인 가짜 객체 생성
        if not cal_settings:
            print("[finaldata] No settings in DB. Using RAW values (slope=1, intercept=0).")
            class DefaultSettings:
                weight_slope = 1.0
                weight_intercept = 0.0
                ph_slope = 1.0
                ph_intercept = 0.0
                ec_slope = 1.0
                ec_intercept = 0.0
            cal_settings = DefaultSettings()

        # VPD 계산
        temp = filtered_data.get('air_temperature') or 0
        hum = filtered_data.get('air_humidity') or 0
        
        vpd = 0
        if temp and hum:
             vpd = ((0.6107 * 10 ** (7.5 * temp / (237.3 + temp))) * (1 - (hum / 100)))

        # 관수량 (급수량) 계산
        current_weight = (cal_settings.weight_slope * (filtered_data.get('weight')) + cal_settings.weight_intercept)
        print(f"[FinalData] Current Weight: {current_weight}, Previous Weight: {prev_weight}", flush=True)

        irrigation = 0
        
        if prev_weight > 0 and current_weight > prev_weight + 100:
            irrigation = current_weight - prev_weight
            print(f"[FinalData] Irrigation Detected: {irrigation} ml", flush=True)
            
        # 누적 데이터 계산
        agg_result = FinalData.objects.filter(timestamp__gte=today_start).aggregate(
            sum_insol=Sum('insolation'),
            sum_irrig=Sum('irrigation')
        )
        
        total_insolation = (agg_result['sum_insol'] or 0) + (filtered_data.get('insolation') or 0)
        total_irrigation = (agg_result['sum_irrig'] or 0) + irrigation

        # 최종 저장
        # 수식: y = (x * slope) + intercept
        # 설정이 없으면: (값 * 1.0) + 0.0 = 값 (그대로 저장됨)
        FinalData.objects.create(
            timestamp=now,
            
            air_temperature=temp,
            air_humidity=hum,
            co2=filtered_data.get('co2'),
            insolation=filtered_data.get('insolation'),
            total_insolation=total_insolation,
            vpd=vpd,

            # 무게 보정 적용
            weight=current_weight,
            
            irrigation=irrigation, # 급수량
            total_irrigation=total_irrigation, 
            total_drainage=(raw_latest.tip_count) * tip_capacity, # 배액량

            water_temperature=filtered_data.get('water_temperature'),
            
            # pH 보정 적용
            water_ph=filtered_data.get('water_ph'),
            
            # EC 보정 적용
            water_ec=filtered_data.get('water_ec'),

            soil_temperature=filtered_data.get('soil_temperature'),
            soil_humidity=filtered_data.get('soil_humidity'),
            soil_ec=filtered_data.get('soil_ec'),
            soil_ph=filtered_data.get('soil_ph')
        )

        # final_data=FinalData.objects.latest('timestamp')

        # print(f"[12] FinalData saved at {now.strftime('%H:%M:%S')} : {final_data}", flush = True)
        prev_weight = current_weight
        print(f"prev weight: {prev_weight}", flush=True)

    except Exception as e:
        print(f"[FinalData Error] {e}")
        # import traceback
        # traceback.print_exc()
