# gemini

from django.apps import AppConfig
import os
import threading

class OmnitorConfig(AppConfig):
    name = "omnitor"

    def ready(self):
        # 1. runserver 자동 재시작으로 인한 중복 실행 방지
        if os.environ.get("RUN_MAIN") != "true":
            return

        # 2. 작성하신 모듈 불러오기 (Import)
        # apps.py 위치 기준으로 상대 경로 import
        try:
            from .services import save_data
            from .devices import camera
        except ImportError as e:
            print(f"[Apps Error] 모듈을 찾을 수 없습니다: {e}")
            return

        print(">>> Django 서버 시작: 백그라운드 작업 스레드 실행 중...")

        # -----------------------------------------------------------
        # [Task 1] save_data.py 실행
        # save_data.py 안에 있는 두 개의 루프 함수를 각각 쓰레드로 돌립니다.
        # -----------------------------------------------------------
        
        # 1-1. RawData 저장 루프 (0.1초 간격)
        t_raw = threading.Thread(target=save_data.save_rawdata_loop)
        t_raw.daemon = True  # 서버 꺼지면 같이 꺼지게 설정
        t_raw.start()
        print("[Thread Start] RawData 수집 시작")

        # 1-2. FinalData 저장 루프 (57초 간격)
        t_final = threading.Thread(target=save_data.save_finaldata_loop)
        t_final.daemon = True
        t_final.start()
        print("[Thread Start] FinalData 저장 시작")

        # -----------------------------------------------------------
        # [Task 2] camera.py 실행
        # camera.py 안에 있는 스케줄러 루프 함수를 쓰레드로 돌립니다.
        # -----------------------------------------------------------
        
        # 2-1. 카메라 스케줄러 (run_scheduler 함수 실행)
        t_cam = threading.Thread(target=camera.run_scheduler)
        t_cam.daemon = True
        t_cam.start()
        print("[Thread Start] 카메라 스케줄러 시작")
