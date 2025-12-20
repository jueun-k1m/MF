from django.apps import AppConfig
import os
import threading
import time
import schedule 

from .devices.arduino import SerialSingleton
from .devices.soil import SoilSensorSingleton

def run_scheduler_loop():
    print("[Debug] Run Scheduler Loop", flush=True)
    while True:
        schedule.run_pending()
        time.sleep(1)

class OmnitorConfig(AppConfig):
    name = "omnitor"

    def ready(self):
        if os.environ.get("RUN_MAIN") != "true":
            return

        serial = SerialSingleton.instance()
        soil = SoilSensorSingleton.instance()
        serial.start()
        soil.start()

        from .services import schedule as my_schedule_service, save_data
        
        my_schedule_service.add_time_interval_schedule(
            "save_rawdata", 
            1, 
            lambda: save_data.save_rawdata(serial, soil)
        )
        
        my_schedule_service.add_time_interval_schedule(
            "save_finaldata", 
            60, 
            save_data.save_finaldata
        )
        
        scheduler_thread = threading.Thread(target=run_scheduler_loop, daemon=True)
        scheduler_thread.start()
        print(">>> [System] Data Collector Scheduler Started!")

        #rom .devices import camera
        #camera_thread = threading.Thread(target=camera.run_scheduler, daemon=True)
        #camera_thread.start()
