import os
import sys
import time
import cv2
import schedule
import django
from datetime import datetime
from models import FarmJournal


current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings") 
django.setup()

STATIC_IMAGE_DIR = os.path.join(project_root, "static", "journal_images")

# 카메라 설정
IMAGE_WIDTH = 8000
IMAGE_HEIGHT = 6000
WARM_UP_FRAMES = 30


def decode_fourcc(val):
    return "".join([chr((int(val) >> 8 * i) & 0xFF) for i in range(4)])


def capture_job():

    """
    지정된 시간에 사진을 찍고 DB 업데이트 (cam_time, image_dir) 하는 함수
    """

    print(f"[{datetime.now()}] 사진 촬영 시작 !")
    
    journal = FarmJournal.objects.last()

    if not journal:
        print("에러: DB FarmJournal 데이터가 없습니다.")
        return
    
    os.makedirs(STATIC_IMAGE_DIR, exist_ok=True)

    filename = f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.jpg"
    full_path = os.path.join(STATIC_IMAGE_DIR, filename)

    save_path = f"journal_images/{filename}"

    cap = None

    try:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("에러: 카메라를 열 수 없습니다.")
            return
            
        fourcc = cv2.VideoWriter_fourcc(*'MJPG')
        cap.set(cv2.CAP_PROP_FOURCC, fourcc)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, IMAGE_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, IMAGE_HEIGHT)
        
        print("카메라 예열 중...")
        for _ in range(WARM_UP_FRAMES):
            cap.read()

        ret, frame = cap.read()

        if ret:
            cv2.imwrite(full_path, frame)
            print(f"이미지 저장 성공! 이미지가 저장된 경로: {full_path}")

            journal.image_dir = save_path
            journal.save()

        else:
            print("에러: 사진을 저장하지 못 했습니다.")

    except Exception as e:
        print(f"오류 발생: {e}")
    finally:
        if cap is not None:
            cap.release()
            print("카메라 리소스 해제됨.")

def run_scheduler():

    """
    main 루프에서 돌릴 함수
    DB cam_time 지정된 시간에 스케줄러를 사용하여 카메라 찍도록 조정
    """

    current_sched_time = None

    print("스케줄러 시작!")

    while True:
        try:
            journal = FarmJournal.objects.last()

            if journal and journal.cam_time:
                target_time_str = journal.cam_time.strftime("%H:%M")

                if current_sched_time != target_time_str:
                    schedule.clear()
                    schedule.every().day.at(target_time_str).do(capture_job)

                    current_sched_time = target_time_str

            else:
                if current_sched_time is not None:
                    schedule.clear()
                    current_sched_time = None

            schedule.run_pending()

            time.sleep(1)

        except Exception as e:
            print(f"오류 발생: {e}")
            time.sleep(5) # 대기 후 다시 시도


if __name__ == "__main__":
    run_scheduler()
