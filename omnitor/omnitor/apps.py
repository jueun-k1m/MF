from django.apps import AppConfig
import os
import threading
import time
import schedule 
from datetime import datetime

from .devices.soil import SoilSensorSingleton
from .devices.water import WaterSensorSingleton
from .devices.gpio import GPIOSensorSingleton
from .devices.LCD_display import LCDManager


def run_scheduler_loop():
    #print("[Debug] Run Scheduler Loop", flush=True)
    time.sleep(2)  # 초기 대기 시간

    while True:
        schedule.run_pending()
        time.sleep(1)

class OmnitorConfig(AppConfig):
    name = "omnitor"

    def ready(self):

        #print(f"[Debug] OmnitorConfig ready 진입")
              
        if os.environ.get("RUN_MAIN") != "true":
            return


        gpio = GPIOSensorSingleton.instance()
        gpio.start()

        soil = SoilSensorSingleton.instance()
        soil.start()
   
        water = WaterSensorSingleton.instance()
        water.start()

        lcd_manager = LCDManager()

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
            
        schedule.every().minute.at(":00").do(final_data_job)

        schedule.every().minute.at(":05").do(lcd_manager.update)

        def camera_job():
            from .devices.camera import take_photo
            from .models import FarmJournal
            now = datetime.now()
            current_time_str = now.strftime("%H:%M") # 현재 시간
            today = now.date()
            journal = FarmJournal.objects.filter(date=today).first()

            if journal and journal.cam_time:
                target_time_str = journal.cam_time.strftime("%H:%M") # DB에 저장된 시간

            # 비교: 현재 시간이 설정 시간과 같으면 촬영!
            if current_time_str == target_time_str:
               #print(f"[apps.camera_job] 촬영 시간 도달! ({current_time_str})", flush=True)
                take_photo()
            else:
                # 디버깅용
                #print(f"[apps.camera_job] 대기 중... 현재: {current_time_str} / 목표: {target_time_str}", flush=True)
                pass

        schedule.every(60).seconds.do(camera_job)


        scheduler_thread = threading.Thread(target=run_scheduler_loop, daemon=True)
        scheduler_thread.start()
