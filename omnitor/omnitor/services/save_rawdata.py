import os
import sys
import time
import django
import threading
from datetime import datetime

current_dir = os.path.dirname(os.path.abspath(__file__)) # service 폴더
root_dir = os.path.dirname(current_dir) # 한 단계 위 dir

sys.path.append(root_dir) # ★ 루트 경로를 추가해야 'devices'와 'omnitor'를 찾음

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "omnitor.settings")
django.setup()

from omnitor.models import RawData # DB 모델
from django.db import connection   # DB 연결 관리용
from devices.arduino import SerialSingleton
from devices.soil import SoilSensorSingleton

def sensor_loop():
    arduino = SerialSingleton.instance()

    arduino.start()

    soil = SoilSensorSingleton.instance()
    soil.start()


    while True:
        try:
            arduino_data = arduino.get_current_data()
            soil_data = soil.read()

            if arduino_data and soil_data:
                RawData.objects.create(
                    timestamp=datetime.now(),
                    air_temperature=arduino_data.air_temperature,
                    air_humidity=arduino_data.air_humidity,
                    co2=int(arduino_data.co2),
                    insolation=arduino_data.insolation,
                    weight_raw=int(arduino_data.weight_raw),
                    ph_voltage=arduino_data.ph_voltage,
                    ec_voltage=arduino_data.ec_voltage,
                    water_temperature=arduino_data.water_temperature,
                    tip_count=int(arduino_data.tip_count),
                    soil_temperature=soil_data.soil_temperature,
                    soil_humidity=soil_data.soil_humidity,
                    soil_ec=soil_data.soil_ec,
                    soil_ph=soil_data.soil_ph
                )

                connection.close()
            else:
                pass
            time.sleep(1)
        
        except Exception as e:
            print(f"[Arduino Service] 오류 발생: {e}")
            time.sleep(1)

        except KeyboardInterrupt:
            break
    arduino.stop()
    soil.stop()

if __name__ == '__main__':
    sensor_loop()
