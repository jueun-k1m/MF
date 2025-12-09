import os
import sys
import time
import django
from datetime import datetime

current_dir = os.path.dirname(os.path.abspath(__file__)) # service 폴더
root_dir = os.path.dirname(current_dir) # 한 단계 위 dir

sys.path.append(root_dir) # 루트 경로를 추가해야 'devices'와 'omnitor'를 찾음

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "omnitor.settings")
django.setup()

from omnitor.models import RawData, CalibrationSettings, FinalData # DB 모델
from django.db import connection, close_old_connections # DB 연결 관리용
from devices.arduino import SerialSingleton
from devices.soil import SoilSensorSingleton
from filter import maf_all

tip_capacity = 5


def save_data_loop():

    """
    자동 실행할 센서 데이터 저장하는 루프 함수
    arduino + soil sensor data = RawData 저장
    RawData -> 이평필 -> 보정 = FinalData 저장
    """


    # ====== RawData 저장 =======
    arduino = SerialSingleton.instance()
    soil = SoilSensorSingleton.instance()

    arduino.start()
    soil.start()


    while True:
        try:
            close_old_connections()
            
            arduino_data = arduino.get_current_data()
            soil_data = soil.get_current_data()

            if arduino_data and soil_data:
                start_time = time.time()
                
                now = datetime.now()

                raw_data = RawData.objects.create(
                    timestamp=now,
                    air_temperature=arduino_data.air_temperature,
                    air_humidity=arduino_data.air_humidity,
                    co2=int(arduino_data.co2),
                    insolation=arduino_data.insolation,
                    weight=int(arduino_data.weight_raw),
                    ph=arduino_data.ph_voltage,
                    ec=arduino_data.ec_voltage,
                    water_temperature=arduino_data.water_temperature,
                    tip_count=int(arduino_data.tip_count),
                    soil_temperature=soil_data.soil_temperature,
                    soil_humidity=soil_data.soil_humidity,
                    soil_ec=soil_data.soil_ec,
                    soil_ph=soil_data.soil_ph
                )
                

                # ======= FinalData 저장 =======

                filtered_data = maf_all()

                if filtered_data:
                    
                    cal_settings = CalibrationSettings.objects.last()

                    if not cal_settings:
                        print("보정 설정이 없습니다..")
                        class DefaultSettings:
                            weight_slope = 1; weight_intercept = 0
                            ph_slope = 1; ph_intercept = 0
                            ec_slope = 1; ec_intercept = 0
                        
                        cal_settings = DefaultSettings()
                        
                    FinalData.objects.create(
                        timestamp=raw_data.timestamp,
                        air_temperature=filtered_data['air_temperature'],
                        air_humidity=filtered_data['air_humidity'],
                        co2=filtered_data['co2'],
                        insolation=filtered_data['insolation'],
                        water_temperature=filtered_data['water_temperature'],

                        weight=cal_settings.weight_slope * filtered_data['weight'] + cal_settings.weight_intercept,
                        ph=(cal_settings.ph_slope * filtered_data['ph']) + cal_settings.ph_intercept,
                        ec=(cal_settings.ec_slope * filtered_data['ec']) + cal_settings.ec_intercept,

                        tip_total=raw_data.tip_count * tip_capacity,
                        soil_temperature=filtered_data['soil_temperature'],
                        soil_humidity=filtered_data['soil_humidity'],
                        soil_ec=filtered_data['soil_ec'],
                        soil_ph=filtered_data['soil_ph']
                    )
                end_time = time.time()
                elapsed_time = end_time - start_time
                
                print(f"소요 시간: {elapsed_time:.4f}초")
            else:
                print("센서 대기 중..")
            time.sleep(0.1)
        except KeyboardInterrupt:
            print("프로그램 종료")
            break
        except Exception as e:
            print(f" 에러: {e}")
            time.sleep(1)

    arduino.stop()
    soil.stop()

if __name__ == '__main__':
    save_data_loop()
