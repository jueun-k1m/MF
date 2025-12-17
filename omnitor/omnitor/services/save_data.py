import os
import sys
import time
import django

from omnitor.models import RawData, CalibrationSettings, FinalData
from django.db import connection, close_old_connections
from django.db.models import Sum
from django.utils import timezone


from .filtering import maf_all

# 전역 변수
prev_weight = 0
tip_capacity = 5

def save_rawdata(arduino, soil):

    """
    센서 데이터를 읽어 RawData에 저장
    """
    try:
        arduino_data = arduino.get_current_data()
        soil_data = soil.get_current_data()

        if not arduino_data and not soil_data:
            return
        
        now = timezone.now()
                
        RawData.objects.create(
            timestamp=now,
            air_temperature=arduino_data.air_temperature,
            air_humidity=arduino_data.air_humidity,
            co2=int(arduino_data.co2),
            insolation=arduino_data.insolation,
            weight=int(arduino_data.weight),
            ph=arduino_data.ph_voltage,
            ec=arduino_data.ec_voltage,
            water_temperature=arduino_data.water_temperature,
            tip_count=int(arduino_data.tip_count),
            
            soil_temperature=soil_data.soil_temperature,
            soil_humidity=soil_data.soil_humidity,
            soil_ec=soil_data.soil_ec,
            soil_ph=soil_data.soil_ph
        )
            
    except Exception as e:
        print(f"[RawData Error] {e}")
        time.sleep(1)

def save_finaldata():

    """
    RawData -> 필터링 -> 보정 -> FinalData
    """
    
    global prev_weight

    try:
        # DB 연결 리셋
        close_old_connections() 
            
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        # ================ DB RawData에서 이동 평균 필터 적용한 데이터 반환=============
        filtered_data = maf_all()
            
        # ================ 계산 ===================
        try:
            raw_latest = RawData.objects.latest('timestamp')
        except RawData.DoesNotExist:
            print("RawData가 없습니다.")
            return

        if filtered_data and raw_latest:
            # VPD 계산
            temp = filtered_data['air_temperature']
            hum = filtered_data['air_humidity']
                
            # ZeroDivisionError 방지
            if temp is None: temp = 0
            if hum is None: hum = 0
                
            vpd = ((0.6107 * 10 ** (7.5 * temp / (237.3 + temp))) * (1 - (hum / 100)))

            # 급수량 계산
            current_weight = filtered_data['weight']
            irrigation = 0
                
            # 이전 무게 있고 && 무게 100g보다 증가 = 관수로 판단
            if prev_weight > 0 and current_weight > prev_weight + 100:
                irrigation = current_weight - prev_weight
                
            # ================= 보정 설정 추가 ================
            cal_settings = CalibrationSettings.objects.last()
            if not cal_settings:
                # 기본값 처리
                cal_settings = type('obj', (object,), {
                    'weight_slope': 1, 'weight_intercept': 0,
                    'ph_slope': 1, 'ph_intercept': 0,
                    'ec_slope': 1, 'ec_intercept': 0
                })

            # ================ 누적 값 계산 ===============
            agg_result = FinalData.objects.filter(timestamp__gte=today_start).aggregate(
                sum_insol=Sum('insolation'),
                sum_irrig=Sum('irrigation')
            )
                
                # 데이터 없으면 0
            total_insolation = (agg_result['sum_insol'] or 0) + filtered_data['insolation']
            total_irrigation = (agg_result['sum_irrig'] or 0) + irrigation

            # ======= FinalData 저장하기 =======
            FinalData.objects.create(
                timestamp=now,
                    
                # 환경
                air_temperature=temp,
                air_humidity=hum,
                co2=filtered_data['co2'],
                insolation=filtered_data['insolation'],
                total_insolation=total_insolation,
                vpd=vpd,

                # 함수율
                total_weight=(cal_settings.weight_slope * current_weight) + cal_settings.weight_intercept,
                irrigation=irrigation,
                total_irrigation=total_irrigation,
                total_drainage=raw_latest.tip_count * tip_capacity,

                # 배액
                water_temperature=filtered_data['water_temperature'],
                ph=(cal_settings.ph_slope * filtered_data['ph']) + cal_settings.ph_intercept,
                ec=(cal_settings.ec_slope * filtered_data['ec']) + cal_settings.ec_intercept,

                # 토양  
                soil_temperature=filtered_data['soil_temperature'],
                soil_humidity=filtered_data['soil_humidity'],
                soil_ec=filtered_data['soil_ec'],
                soil_ph=filtered_data['soil_ph']
            )

            print(f"[Saved] FinalData at {now.strftime('%H:%M:%S')}")
                
            prev_weight = current_weight

    except Exception as e:
        print(f"[FinalData Error] {e}")
