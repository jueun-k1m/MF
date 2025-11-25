import os
import cv2
from datetime import datetime
import time
import json

# --- Directory and Time Settings ---
BASE_DIR = os.path.expanduser("~/gomojang/omnitor")
SAVE_DIRECTORY = os.path.join(BASE_DIR, "omnitor/frontend/static/journal_images/")

# --- Settings ---
IMAGE_WIDTH = 8000
IMAGE_HEIGHT = 6000
WARM_UP_FRAMES = 30

def decode_fourcc(val):
    return "".join([chr((int(val) >> 8 * i) & 0xFF) for i in range(4)])

def take_picture_job():
    print(f"[{datetime.now()}] 사진 캡처를 시작합니다.")
    cap = None
    try:
        os.makedirs(SAVE_DIRECTORY, exist_ok=True)
        filename = f"{datetime.now().strftime('%Y-%m-%d')}.jpg"
        full_path = os.path.join(SAVE_DIRECTORY, filename)
        
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("에러: 카메라를 열 수 없습니다.")
            return
            
        fourcc = cv2.VideoWriter_fourcc(*'MJPG')
        cap.set(cv2.CAP_PROP_FOURCC, fourcc)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, IMAGE_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, IMAGE_HEIGHT)
        
        actual_fourcc = decode_fourcc(cap.get(cv2.CAP_PROP_FOURCC))
        actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        for _ in range(WARM_UP_FRAMES):
            cap.read()
        print("사진을 캡쳐 합니다.")

        ret, frame = cap.read()

        if ret:
            cv2.imwrite(full_path, frame)
            print(f"성공. 사진이 저장 되었습니다: {full_path}")
        else:
            print("에러: 사진을 캡처하지 못 했습니다.")

    except Exception as e:
        print(f"캡처 중 오류가 났습니다: {e}")
    finally:
        if cap is not None and cap.isOpened():
            cap.release()



def main():
    take_picture_job()

    
if __name__ == "__main__":
    main()
