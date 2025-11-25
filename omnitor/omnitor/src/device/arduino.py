import os
import sys
import serial
import time
import serial.tools.list_ports
from collections import deque
from datetime import datetime
import statistics
import django

# DB 사용을 위한 장고 설정
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "omnitor.settings")
django.setup()

from omnitor.models import SensorData , SensorCalibration


# 변수 설정 
arduino_baudrate = 9600 # 시리얼 통신

moving_average_window = 5 # 이동 평균 필터에서 윈도우 크기
save_data_sec = 60 # 데이터 저장하는 초 단위
read_data_sec = 1 # 데이터 읽는 초 단위

# 이동 평균을 위한 데이터 버퍼 (Deque)
data_buffer = {
    'air_temperature': deque(maxlen=moving_average_window),
    'air_humidity': deque(maxlen=moving_average_window),
    'co2': deque(maxlen=moving_average_window),
    'insolation': deque(maxlen=moving_average_window),
    'weight_raw': deque(maxlen=moving_average_window),
    'ph_raw': deque(maxlen=moving_average_window),
    'ec_raw': deque(maxlen=moving_average_window),
    'water_temperature': deque(maxlen=moving_average_window),
}


def find_arduino_port(): 

    """ USB 포트에서 아두이노 포트 찾는 함수 """

    ports = serial.tools.list_ports.comports()
    for port in ports:
        if "Arduino" in port.description:
            arduino_port = port.device
            return arduino_port
    return None


def read_data(ser):

    """ 아두이노에서 데이터 읽기 함수 """

    if ser.in_waiting > 0:
        try:
            line = ser.readline().decode('utf-8').rstrip()
            parts = line.split(',')

            if len(parts) == 9:
                data = {
                    'timestamp': datetime.now(),
                    'air_temperature': float(parts[0]),
                    'air_humidity': float(parts[1]),
                    'co2': float(parts[2]),
                    'insolation': float(parts[3]),
                    'weight_raw': float(parts[4]),
                    'ph_raw': float(parts[5]),
                    'ec_raw': float(parts[6]),
                    'water_temperature': float(parts[7]),
                    'tip_count': float(parts[8])
                }
                return data
            
        except ValueError:
            print("데이터 변환 오류입니다.")
    return None

    
def moving_avg_filter(data, data_buffer):

    """ 이동 평균 필터 적용 및 데이터베이스 저장 함수 """
    
    avg_data = {}
    
    for key, value in data.items():
        if key in data_buffer:
            data_buffer[key].append(value) # 큐에 새로운 값 추가
            avg_data[key] = round(statistics.mean(data_buffer[key]), 2)  # 이동 평균 계산
        else:
            avg_data[key] = value  # 버퍼가 없으면 원래 값 사용        
    return avg_data # 평균 데이터 반환
   

def update_latest_raw_data(avg_data):

    """ 최신 raw 데이터를 DB에 저장하는 함수 (보정용) """

    try:
        SensorCalibration.objects.update_or_create(
            id=2,
            defaults={
                'ph_raw': avg_data['ph_raw'],
                'ec_raw': avg_data['ec_raw'],
                'weight_raw': avg_data['weight_raw'],
                'water_temperature': avg_data['water_temperature'],
            }
        )
    except Exception as e:
        print(f"최신 raw 데이터 업데이트 중 에러 발생: {e}")


def save_to_database(avg_data, tip_count):

    """ 데이터베이스에 데이터 저장 함수 """

    try:
        SensorData.objects.create(
            air_temperature=avg_data['air_temperature'],
            air_humidity=avg_data['air_humidity'],
            co2=avg_data['co2'],
            insolation=avg_data['insolation'],
            water_temp=avg_data['water_temperature'],
            weight_raw=avg_data['weight'],
            ph_raw=avg_data['ph'],
            ec_raw=avg_data['ec'],
            tip_count=tip_count
        )
    except Exception as e:
        print(f"데이터베이스 저장 중 에러 발생: {e}")

def main():

    """ 메인 함수 """
    """ 아두이노 시리얼 포트 열기 및 데이터 읽기 """

    print("아두이노 센서 읽기 시작합니다.")
    
    ser = None

    last_read_time = time.time()
    last_save_time = time.time()

    while True:

        try:
            current_time = time.time()
            
            # 아두이노 연결 될 때까지 대기
            if ser is None:
                arduino = find_arduino_port()
                if arduino:
                    print(f"아두이노 포트를 찾았습니다: {arduino}")
                    try:
                        ser = serial.Serial(arduino, arduino_baudrate, timeout=1)
                        time.sleep(2)  # 시리얼 연결 안정화 대기
                    except serial.SerialException as e:
                        print(f"시리얼 포트 열기 실패: {e}")
                        ser = None
                else:
                    print("아두이노 포트를 찾지 못 했습니다. 다시 시도합니다...")
                    ser = None

                continue  # 포트를 찾을 때까지 대기

            
            # 데이터 읽기
            if current_time - last_read_time >= read_data_sec:
                data = read_data(ser) # 아두이노에서 데이터 읽기

                if data:
                    avg_data = moving_avg_filter(data, data_buffer) # 이동 평균 필터 적용
                    update_latest_raw_data(avg_data) # 최신 데이터 업데이트 (보정용)
                    print(f"[{data['timestamp']}] 읽은 데이터: {avg_data}")
                    
                    if current_time - last_save_time >= save_data_sec:
                        save_to_database(avg_data, data['tip_count']) # 데이터베이스 저장
                        print(f"[{data['timestamp']}] 데이터 저장 완료: {avg_data}")
                        last_save_time = current_time # 저장 시간 업데이트

                last_read_time = current_time

            time.sleep(0.05)  # CPU 사용량 절감을 위한 짧은 대기

        except (OSError, serial.SerialException) as e:
            print(f"시리얼 포트 오류 발생: {e}")
            if ser:
                ser.close()
            ser = None  # 포트 오류 시 재설정
            time.sleep(5)  # 재시도 전 대기

        except KeyboardInterrupt:
            print("프로그램을 종료합니다.")
            if ser and ser.is_open:
                ser.close()
            break

        except Exception as e:
            print(f"오류 발생: {e}")
            ser = None  # 오류 발생 시 시리얼 포트 재설정
            time.sleep(5)  # 재시도 전 대기
        
if __name__ == '__main__':
    main()
