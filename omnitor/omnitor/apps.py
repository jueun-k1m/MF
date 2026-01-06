from django.apps import AppConfig
import os
import threading
import time
import schedule 

from .devices.soil import SoilSensorSingleton
from .devices.water import WaterSensorSingleton
from .devices.gpio import GPIOSensorSingleton


def run_scheduler_loop():
    print("[Debug] Run Scheduler Loop", flush=True)
    time.sleep(2)  # 초기 대기 시간

    while True:
        schedule.run_pending()
        time.sleep(1)

class OmnitorConfig(AppConfig):
    name = "omnitor"

    def ready(self):

        print(f"[Debug] OmnitorConfig ready 진입")
              
        if os.environ.get("RUN_MAIN") != "true":
            return


        gpio = GPIOSensorSingleton.instance()
        gpio.start()

        soil = SoilSensorSingleton.instance()
        soil.start()
   
        water = WaterSensorSingleton.instance()
        water.start()

        def sensor_job():
            # 이 함수는 1초마다 실행됩니다.
            # 실행될 때마다 import를 확인하므로 에러가 나지 않습니다.
            from .services.save_data import save_rawdata
            save_rawdata(gpio, soil, water)

        # 위에서 만든 함수를 스케줄러에 등록
        schedule.every(1).second.do(sensor_job)

        # finaldata도 마찬가지 방식으로 처리 가능
        def final_data_job():
            from .services.save_data import save_finaldata
            save_finaldata()
            
        schedule.every(60).seconds.do(final_data_job)

        def camera_job():
            from .devices.camera import check_capture
            check_capture()

        schedule.every(60).seconds.do(camera_job)


        scheduler_thread = threading.Thread(target=run_scheduler_loop, daemon=True)
        scheduler_thread.start()
