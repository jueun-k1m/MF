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

        def raw_data_job():
            " save_data.py에서 로우 데이터 저장하는 함수 "
            from .services.save_data import save_rawdata
            save_rawdata(gpio, soil, water)

        # 1초마다 raw data 함수 실행
        schedule.every(1).second.do(raw_data_job)

        # finaldata도 마찬가지 방식으로 처리
        def final_data_job():
            " save_data.py에서 최종 데이터 저장하는 함수 "
            from .services.save_data import save_finaldata
            save_finaldata()
            
        schedule.every().minute.at(":00").do(final_data_job)

        schedule.every(10).seconds.do(lcd_manager.update)

        def camera_job():
            " camera.py로 카메라 사진 찍는 함수"
            from .devices.camera import take_photo
            from .models import FarmJournal
            now = datetime.now()
            current_time_str = now.strftime("%H:%M") # 현재 시간
            today = now.date()
            journal = FarmJournal.objects.filter(date=today).first()

            if journal and journal.cam_time:
                target_time_str = journal.cam_time.strftime("%H:%M") # DB에 저장된 시간
            else:
                target_time_str = "09:00" # 기본값
                
            # 비교해서 현재 시간이 설정 시간과 같으면 촬영
            if current_time_str == target_time_str:
               #print(f"[apps.camera_job] 촬영 시간 도달: ({current_time_str})", flush=True)
                take_photo()
            else:
                # 디버깅용
                #print(f"[apps.camera_job] 대기 중... 현재: {current_time_str} | 목표: {target_time_str}", flush=True)
                pass

        schedule.every(60).seconds.do(camera_job)


        scheduler_thread = threading.Thread(target=run_scheduler_loop, daemon=True)
        scheduler_thread.start()
