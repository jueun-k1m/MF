import os
import sys
import time
import django

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

    print(f"[rawdata] save_rawdata start {timezone.now()}", flush=True)

    from omnitor.models import RawData

    #print("[DEBUG] imported RawData", flush=True)

    try:
        #print("[DEBUG] trying", flush=True)
        close_old_connections()
        #print("[DEBUG] closed old connections", flush=True)

        arduino_data = arduino.get_current_data()
        #print("[DEBUG] got arduino data", flush=True)
        
        soil_data = soil.get_current_data()

        

        
        #print("[DEBUG] got soil data", flush=True)

        if not arduino_data or not soil_data:
            #print("[DEBUG] no arduino or no soil data", flush=True)
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

        #print(f"[DEBUG] RawData DB save complete: {now.strftime('%H:%M:%S')}", flush=True)
            
    except Exception as e:
        print(f"[RawData Error] {e}")
        time.sleep(1)

def save_finaldata():
    """
    RawData -> 필터링 & 보정 -> FinalData
    """

    print(f"[save_final] save_finaldata start {timezone.now()}", flush=True)

    global prev_weight
    from omnitor.models import RawData, CalibrationSettings, FinalData
    from . import save_calibrationsettings

    try:
        close_old_connections() 
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        try:
            raw_latest = RawData.objects.latest('timestamp')
            print("[finaldata] retrieving raw data.")
        except RawData.DoesNotExist:
            print("[finaldata] RawData does not exist.")
            return

        filtered_data = maf_all()
        print("[finaldata] Filtering data.")


        cal_settings = CalibrationSettings.objects.get(id=1)
        print(f"[5] load calibration settings successful: {cal_settings.__dict__}")
        
        print("[6] saving calib settings")

        if not filtered_data:
            print("[finaldata] No filtered data.")
            filtered_data = {
                'air_temperature': raw_latest.air_temperature,
                'air_humidity': raw_latest.air_humidity,
                'co2': raw_latest.co2,
                'insolation': raw_latest.insolation,
                'weight': raw_latest.weight,
                'water_temperature': raw_latest.water_temperature,
                'ph': raw_latest.ph,
                'ec': raw_latest.ec,
                'soil_temperature': raw_latest.soil_temperature,
                'soil_humidity': raw_latest.soil_humidity,
                'soil_ec': raw_latest.soil_ec,
                'soil_ph': raw_latest.soil_ph
            }

        print(f"filtered ec: {filtered_data.get('ec')}")



        temp = filtered_data.get('air_temperature', 0) or 0
        hum = filtered_data.get('air_humidity', 0) or 0
        
        vpd = 0
        if temp and hum:
             vpd = ((0.6107 * 10 ** (7.5 * temp / (237.3 + temp))) * (1 - (hum / 100)))

        current_weight = filtered_data.get('weight', 0) or 0
        irrigation = 0
        
        if prev_weight > 0 and current_weight > prev_weight + 100:
            irrigation = current_weight - prev_weight
            
        
        if cal_settings:
            print(f"[finaldata] load calibration settings successful: {cal_settings.__dict__}")
        if not cal_settings:
            print("[finaldata] no calibration settings")
            class MockSettings:
                weight_slope = 1
                weight_intercept = 0
                ph_slope = 1
                ph_intercept = 0
                ec_slope = 1
                ec_intercept = 0
            cal_settings = MockSettings


        print(f"calibrated ec: {(cal_settings.ec_slope * (filtered_data.get('ec') or 0)) + cal_settings.ec_intercept}")


        agg_result = FinalData.objects.filter(timestamp__gte=today_start).aggregate(
            sum_insol=Sum('insolation'),
            sum_irrig=Sum('irrigation')
        )
        
        total_insolation = (agg_result['sum_insol'] or 0) + (filtered_data.get('insolation', 0) or 0)
        total_irrigation = (agg_result['sum_irrig'] or 0) + irrigation

        # FinalData
        FinalData.objects.create(
            timestamp=now,
            
            air_temperature=temp,
            air_humidity=hum,
            co2=filtered_data.get('co2'),
            insolation=filtered_data.get('insolation'),
            total_insolation=total_insolation,
            vpd=vpd,

            irrigation=irrigation,
            total_irrigation=total_irrigation,
            total_drainage=(raw_latest.tip_count or 0) * tip_capacity,

            water_temperature=filtered_data.get('water_temperature'),
            ph=(cal_settings.ph_slope * (filtered_data.get('ph'))) + cal_settings.ph_intercept,
            ec=(cal_settings.ec_slope * (filtered_data.get('ec'))) + cal_settings.ec_intercept,

            soil_temperature=filtered_data.get('soil_temperature'),
            soil_humidity=filtered_data.get('soil_humidity'),
            soil_ec=filtered_data.get('soil_ec'),
            soil_ph=filtered_data.get('soil_ph')
        )

        print(f"[12] FinalData saved at {now.strftime('%H:%M:%S')}", flush = True)

        prev_weight = current_weight

    except Exception as e:
        print(f"[FinalData Error] {e}")
        import traceback
        traceback.print_exc()
