import os
import sys
import serial
import time
import serial.tools.list_ports
from datetime import datetime
import django
import threading

# DB 사용을 위한 장고 설정
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "omnitor.settings")
django.setup()

from omnitor.models import RawData

class ArduinoController:

    def __init__(self):
        self.arduino_baudrate = 9600
        self.save_data_sec = 1
        self.ser = None # 시리얼 객체를 클래스 내에서 공유
        self.running = False # 루프 제어 변수

    def find_arduino_port(self):
        
        """ USB 포트에서 아두이노 포트 찾는 함수 """
        
        ports = serial.tools.list_ports.comports()
        for port in ports:
            if "Arduino" in port.description:
                return port.device
        return None

    def save_data(self):

        """ 아두이노에서 데이터 읽기 및 DB 저장 함수 """
        
        if self.ser and self.ser.in_waiting > 0:
            try:
                line = self.ser.readline().decode('utf-8').rstrip()
                parts = line.split(',')

                if len(parts) == 9:
                    try:
                        # DB 저장 (Django ORM은 쓰레드 안전하지만, 커넥션 관리가 필요할 수 있음. 여기선 기본 사용)
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
                        # print(f"데이터 저장 완료: {parts}") # 디버깅용
                    except Exception as e:
                        print(f"데이터베이스 저장 중 에러 발생: {e}")
            except ValueError:
                print("데이터 변환 오류입니다.")
            except Exception as e:
                print(f"데이터 읽기 오류: {e}")

    def send_command(self, command):
        
        """ 
        외부에서 호출하여 아두이노로 명령을 보내는 함수 
        
        command:
        '1' - 티핑게이지 count 리셋
        '2' - 카메라 고정 풀기
        '3' - 카메라 고정 하기
        '4' - 카메라 모터 작동 (왼쪽으로)
        '5' - 카메라 모터 작동 (오른쪽으로)
        """

        if self.ser and self.ser.is_open:
            try:
                # 명령어를 바이트로 변환하여 전송 (예: '1' -> b'1')
                msg = str(command)
                self.ser.write(msg.encode())
            except Exception as e:
                print(f"명령 전송 실패: {e}")
        else:
            print("에러: 아두이노가 연결되어 있지 않습니다.")

    def _read_process(self):

        """ 백그라운드에서 실행될 실제 무한 루프 로직 """

        last_save_time = 0
        
        while self.running:
            try:
                current_time = time.time()
                
                # 연결이 끊겼거나 없을 때 재연결 로직
                if self.ser is None:
                    port = self.find_arduino_port()
                    if port:
                        print(f"아두이노 포트 발견: {port}")
                        try:
                            self.ser = serial.Serial(port, self.arduino_baudrate, timeout=1)
                            time.sleep(2) # 연결 안정화
                        except serial.SerialException as e:
                            print(f"연결 실패: {e}")
                            self.ser = None
                    else:
                        # 포트 못 찾으면 잠시 대기
                        time.sleep(1)
                        continue

                # 데이터 읽고 DB에 저장 (1초 주기로)
                if current_time - last_save_time >= self.save_data_sec:
                    self.save_data()
                    last_save_time = current_time

                time.sleep(0.05) # CPU 점유율 낮춤

            except (OSError, serial.SerialException):
                print("시리얼 연결 끊김. 재연결 시도...")
                if self.ser:
                    self.ser.close()
                self.ser = None
                time.sleep(2)
            except Exception as e:
                print(f"예기치 못한 오류: {e}")
                time.sleep(1)

    def start_reading_loop(self):

        """ 백그라운드 쓰레드 시작 함수 """

        self.running = True
        # daemon=True로 설정하면 메인 프로그램 종료 시 쓰레드도 같이 강제 종료됨

        t = threading.Thread(target=self._read_process, daemon=True)
        t.start()

    def stop(self):

        """ 프로그램 종료 시 호출 """

        self.running = False
        if self.ser:
            self.ser.close()


# 메인 실행 부분

def main():

    # 컨트롤러 인스턴스 생성
    controller = ArduinoController()
    
    # 백그라운드에서 읽기 시작 (이제 이 코드는 멈추지 않고 바로 다음 줄로 넘어감)
    controller.start_reading_loop()


    # 메인 쓰레드는 사용자 입력을 기다림 (여기가 command 주는 곳)
    # ++++++++++++++++++++ 지금은 입력 하는 걸로 뒀지만 나중에 API POST로 수정 필요 ++++++++++++++++++++++++++
    try:
        while True:
            # 여기서 입력을 받는다
            user_input = input("명령 입력: ")
            
            if user_input == 'q':
                break
            
            # 입력받은 값을 그대로 아두이노로 전송
            if user_input in ['1', '2', '3', '4', '5']:
                controller.send_command(user_input)
            else:
                print("알 수 없는 명령어입니다. (1~5만 가능)")
                # 필요하다면 그냥 보내도 됩니다: controller.send_command(user_input)

    except KeyboardInterrupt:
        pass
    finally:
        print("프로그램을 종료합니다.")
        controller.stop()

if __name__ == '__main__':
    main()
