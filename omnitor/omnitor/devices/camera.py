import os
import cv2
from datetime import datetime
from django.conf import settings

# 설정
SAVE_DIR_NAME = "journal_images"
MEDIA_IMAGE_DIR = os.path.join(settings.MEDIA_ROOT, SAVE_DIR_NAME)
IMAGE_WIDTH = 8000
IMAGE_HEIGHT = 6000
WARM_UP_FRAMES = 30

def take_photo():
    """실제로 사진을 찍고 DB에 저장하는 함수 (내부 호출용)"""
    os.makedirs(MEDIA_IMAGE_DIR, exist_ok=True)
    
    now = datetime.now()
    today_date = now.date()
    
    # 파일명 및 경로
    filename = f"{now.strftime('%Y-%m-%d_%H-%M')}.jpg"
    full_path = os.path.join(MEDIA_IMAGE_DIR, filename)

    print(f"[{now}] 사진 촬영 시작...", flush=True)

    cap = None
    try:
        cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
        if not cap.isOpened():
            print("카메라 연결 실패", flush=True)
            return
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, IMAGE_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, IMAGE_HEIGHT)
        
        for _ in range(WARM_UP_FRAMES):
            cap.read()

        ret, frame = cap.read()
        if ret:
            cv2.imwrite(full_path, frame)
            print(f"full_path: {full_path}", flush=True)
            
        else:
            print("빈 화면", flush=True)

    except Exception as e:
        print(f"카메라 에러: {e}", flush=True)
    finally:
        if cap:
            cap.release()

def check_capture():
    """
    DB 시간을 확인해서 현재 시간과 일치하면 촬영
    """
    from omnitor.models import FarmJournal

    try:
        now = datetime.now()
        current_time_str = now.strftime("%H:%M") # 현재 시간

        # DB에서 오늘 날짜 설정 가져오기
        today = now.date()
        journal = FarmJournal.objects.filter(date=today).first()

        target_time_str = "11:27" # 기본값
        if journal and journal.cam_time:
            target_time_str = journal.cam_time.strftime("%H:%M") # DB에 저장된 시간

        # 비교: 현재 시간이 설정 시간과 같으면 촬영!
        if current_time_str == target_time_str:
            print(f"촬영 시간 도달! ({current_time_str})", flush=True)
            take_photo()
        else:
            # 디버깅용
            print(f"대기 중... 현재: {current_time_str} / 목표: {target_time_str}", flush=True)
            pass

    except Exception as e:
        print(f"카메라 시간 체크 중 에러: {e}", flush=True)
