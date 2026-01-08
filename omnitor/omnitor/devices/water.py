import serial
import minimalmodbus
import time
import threading
from dataclasses import dataclass
from threading import Lock

@dataclass
class WaterData:
    water_temperature: float
    water_ec: float
    water_ph: float


class WaterSensor:
    def __init__(self):
        self.instrument = None
        self.port = "/dev/ttyUSB0"

        self.slave_address = 1
        self.baudrate = 9600
        self.bytesize = 8
        self.parity = serial.PARITY_NONE
        self.stopbits = 1
        self.timeout = 1.0

        # 스레드 제어용 변수
        self.running = False
        self.thread = None
        
        # 데이터 공유용 변수
        self._latest_data = None 
        self.data_lock = Lock() # 데이터 충돌 방지
    
    def start(self):
        """
        센서 통신을 담당할 백그라운드 스레드 (apps.py에서 호출)
        """
        if self.running:
            return True
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()
        return True
    

    def stop(self):
        self.running = False
        if self.instrument:
            try:
                self.instrument.serial.close()
            except:
                pass

    def get_current_data(self):
        """
        스레드가 최신화한 데이터를 즉시 반환 (save_data.save_rawdata()에서 호출)
        """
        with self.data_lock:
            return self._latest_data


    def _connect(self):
        """내부용: 시리얼 연결 시도"""
        try:
            if self.instrument and self.instrument.serial.is_open:
                return True

            print(f"[Water] 포트 연결 시도...")
            self.instrument = minimalmodbus.Instrument(self.port, self.slave_address)
            self.instrument.serial.baudrate = self.baudrate
            self.instrument.serial.bytesize = self.bytesize
            self.instrument.serial.parity = self.parity
            self.instrument.serial.stopbits = self.stopbits
            self.instrument.serial.timeout = self.timeout
            self.instrument.mode = minimalmodbus.MODE_RTU
            print("[Water] 포트 연결 성공!")

            return True
            
        except Exception as e:
            print(f"[Water4] 연결 실패: {e}")
            self.instrument = None
            return False

    def _loop(self):
        """
        연결이 끊기면 재연결을 시도하고, 데이터를 읽어 변수에 저장하는 무한 루프 함수
        """

        while self.running:
            # 연결이 안 되어 있으면 연결 시도
            if not self._connect():
                time.sleep(5) # 5초 대기
                continue

            # 데이터 읽기
            try:
                values = self.instrument.read_registers(0, 3, functioncode=3)

                new_data = WaterData(                    
                    water_ph=values[0] / 100.0,
                    water_ec=values[1],
                    water_temperature=values[2] / 10.0
                )

                with self.data_lock:
                    self._latest_data = new_data
                
                time.sleep(1) # 1초 간격 갱신

            except Exception as e:
                print(f"[Water Loop Error] 읽기 실패 (센서 연결을 확인해 주세요): {e}")
                
            # 연결 재설정을 위해 초기화
                if self.instrument:
                    try:
                        self.instrument.serial.close()
                    except:
                        pass
                    self.instrument = None
                
                time.sleep(3)
            
        
class WaterSensorSingleton:
    _instance = None
    _lock = Lock()

    @classmethod
    def instance(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = WaterSensor()
            return cls._instance
