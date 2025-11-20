import os
import sys
import serial
import time
import statistics
import minimalmodbus
import serial.tools.list_ports
from collections import deque
from datetime import datetime

from omnitor.models import SensorData


# 변수 설정
modbus_baudrate = 4800

moving_average_window = 5 # 이동 평균 필터에서 윈도우 크기
save_data_sec = 60 # 데이터 저장하는 초 단위
read_data_sec = 1 # 데이터 읽는 초 단위

# 이동 평균 필터를 위한 데이터 버퍼 (Deque)
data_buffer = {
    'soil_temperature': deque(maxlen=moving_average_window),
    'soil_humidity': deque(maxlen=moving_average_window),
    'soil_ph': deque(maxlen=moving_average_window),
    'soil_ec': deque(maxlen=moving_average_window),
}


def find_modbus_port():

    """ USB 포트에서 토양 센서 (RS485 -> USB 동글 연결) 포트 찾는 함수 """

    ports = serial.tools.list_ports.comports()
    for port in ports:
        if "Serial" in port.description:
            modbus_port = port.device
            return modbus_port
    return None


def read_data(instrument):

    """ 토양 센서 데이터 읽기 함수 """

    try:
        modbus_data = instrument.read_registers(0, 4, 3)

        data = {
            'timestamp': datetime.now(),
            'soil_temperature': modbus_data[1] / 10.0,      # 단위: 0.1°C 
            'soil_humidity': modbus_data[0] / 10.0,         # 단위: 0.1% 
            'soil_ec': modbus_data[2] / 1.0,                # 단위: 1 us/cm,
            'soil_ph': modbus_data[3] / 10.0                       # 단위: 0.1 
         }
        return data

    except Exception as e:
        print(f"데이터 읽기 중 에러 발생: {e}")


    
def moving_average_filter(data, data_buffer):

    """ 이동 평균 필터 적용 및 데이터베이스 저장 함수 """

    avg_data = {}
    
    for key, value in data.items():
        if key in data_buffer:
            data_buffer[key].append(value) # 큐에 새로운 값 추가
            avg_data[key] = round(statistics.mean(data_buffer[key]), 2)  # 이동 평균 계산
        else:
            avg_data[key] = value  # 버퍼가 없으면 원래 값 사용        
    return avg_data # 평균 데이터 반환



def save_to_database(avg_data):

    """ 데이터베이스에 데이터 저장 함수 """
    try:
        
        SensorData.objects.create(
            soil_temperature=avg_data['soil_temperature'],
            soil_humidity=avg_data['soil_humidity'],
            soil_ph=avg_data['soil_ph'],
            soil_ec=avg_data['soil_ec'],
        )
    except Exception as e:
        print(f"데이터베이스 저장 중 에러 발생: {e}")

def main():

    """ 메인 함수 """
    """ 토양 센서 시리얼 포트 열기 및 데이터 읽기 """

    print("토양 센서 읽기 시작합니다.")

    instrument = None
    avg_data = None

    last_save_time = time.time()
    last_read_time = time.time()


    while True:

        try:
            current_time = time.time()

            if instrument is None:
                modbus = find_modbus_port()

                if modbus:
                    try:
                        instrument = minimalmodbus.Instrument(modbus, 1, mode='rtu') # MODBUS 연결
                        instrument.serial.baudrate = modbus_baudrate  
                        instrument.serial.bytesize = 8
                        instrument.serial.parity = serial.PARITY_NONE
                        instrument.serial.stopbits = 1
                        instrument.serial.timeout = 1  
                        instrument.close_port_after_each_call = True

                        time.sleep(2)  # 연결 안정화 대기
                        
                        if instrument:
                            print(f"토양 센서 연결 성공: {modbus}")
                        else:
                            instrument = None
                    except Exception as e:
                        print(f"토양 센서 연결 실패: {e}")
                        instrument = None
                else:
                    print("토양 센서 포트를 찾지 못 했습니다. 다시 시도합니다...")
                    instrument = None

                continue

            if current_time - last_read_time >= read_data_sec:
                data = read_data(instrument) # 데이터 읽기

                if data:
                    avg_data = moving_average_filter(data, data_buffer)

                    print(f"[{avg_data['timestamp']}] 토양 온도: {avg_data['soil_temperature']} °C, 토양 습도: {avg_data['soil_humidity']} %, 토양 pH: {avg_data['soil_ph']}, 토양 EC: {avg_data['soil_ec']} us/cm")

                    

                last_read_time = current_time

            if current_time - last_save_time >= save_data_sec:
                if avg_data:
                    save_to_database(avg_data) # 데이터베이스 저장
                    print(f"[{avg_data['timestamp']}] 데이터 저장 완료: {avg_data}")
                    last_save_time = current_time # 저장 시간 업데이트

            time.sleep(0.1)  # CPU 사용량 절감을 위한 짧은 대기

        except (OSError, serial.SerialException) as e:
            print(f"시리얼 통신 에러 발생: {e}. 포트를 재설정합니다.")
            if instrument:
                instrument.serial.close()
            instrument = None  # 오류 발생 시 포트 재설정
            time.sleep(2)  # 재시도 전 대기

        except KeyboardInterrupt:
            print("프로그램을 종료합니다.")
            if instrument and instrument.serial.is_open:
                instrument.serial.close()
            break

        except Exception as e:
            print(f"메인 루프 중 에러 발생: {e}")
            instrument = None  # 오류 발생 시 포트 재설정
            time.sleep(2)  # 재시도 전 대기        

if __name__ == '__main__':
    main()
