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

from omnitor.models import RawData


# 변수 설정 
arduino_baudrate = 9600 # 시리얼 통신

save_data_sec = 1 # 데이터 저장하는 초 단위


def find_arduino_port(): 

    """ USB 포트에서 아두이노 포트 찾는 함수 """

    ports = serial.tools.list_ports.comports()
    for port in ports:
        if "Arduino" in port.description:
            arduino_port = port.device
            return arduino_port
    return None


def save_data(ser):

    """ 아두이노에서 데이터 읽기 함수 """

    if ser.in_waiting > 0:
        try:
            line = ser.readline().decode('utf-8').rstrip()
            parts = line.split(',')

            if len(parts) == 9:
                try:
                    RawData.objects.create(
                        timestamp=datetime.now(),
                        air_temperature=float(parts[0]),
                        air_humidity=float(parts[1]),
                        co2=float(parts[2]),
                        insolation=float(parts[3]),
                        weight_raw=float(parts[4]),
                        ph_raw=float(parts[5]),
                        ec_raw=float(parts[6]),
                        water_temperature=float(parts[7]),
                        tip_count=int(parts[8])
                    )
                except Exception as e:
                    print(f"데이터베이스 저장 중 에러 발생: {e}")
                
            
        except ValueError:
            print("데이터 변환 오류입니다.")
    return


def main():

    """ 메인 함수 """
    """ 아두이노 시리얼 포트 열기 및 데이터 읽기 """

    print("아두이노 센서 읽기 시작합니다.")
    
    ser = None

    last_read_time = 0

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

            
            # 데이터 읽기 및 저장
            if current_time - last_read_time >= save_data_sec:
                save_data()
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
