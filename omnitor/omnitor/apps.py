from django.apps import AppConfig
import os

class OmnitorConfig(AppConfig):
    name = "omnitor"

    def ready(self):
        # runserver autoreload 2번 실행 방지
        if os.environ.get("RUN_MAIN") != "true":
            return

        from .devices.arduino import SerialSingleton
        from .devices.soil import SoilSensorSingleton

        serial = SerialSingleton.instance()
        serial.start()
        soil = SoilSensorSingleton.instance()
        soil.start()

        # rawdata랑 finaldata 저장하기
        from .services import schedule, save_data
        schedule.add_time_interval_shedule("save_rawdata", 0.1, save_data.save_rawdata(serial, soil))
        schedule.add_time_interval_shedule("save_finaldata", 57, save_data.save_finaldata)
        

        # 카메라
        from .devices import camera
        camera.run_scheduler
