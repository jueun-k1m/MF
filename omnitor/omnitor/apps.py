from django.apps import AppConfig
import os
import threading
from .devices.arduino import SerialSingleton
from .devices.soil import SoilSensorSingleton
from .services import schedule, save_data
from .devices import camera

class OmnitorConfig(AppConfig):
    name = "omnitor"

    def ready(self):
        # runserver autoreload 2번 실행 방지
        if os.environ.get("RUN_MAIN") != "true":
            return

        # 아두이노 & 토양 센서 연결
        serial = SerialSingleton.instance()
        soil = SoilSensorSingleton.instance()
        serial.start()
        soil.start()

        # rawdata & finaldata 저장하기 (schedule로)
        schedule.add_time_interval_schedule("save_rawdata", 1, lambda: save_data.save_rawdata(serial, soil))
        schedule.add_time_interval_schedule("save_finaldata", 57, save_data.save_finaldata)
        

        # 카메라 쓰레드로 실행      
        camera_thread = threading.Thread(target=camera.run_scheduler, daemon=True)
        camera_thread.start()
