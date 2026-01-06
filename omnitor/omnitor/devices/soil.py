import serial
import minimalmodbus
import time
import threading
from dataclasses import dataclass
from threading import Lock

@dataclass
class SoilData:
    soil_temperature: float
    soil_humidity: float
    soil_ec: int
    soil_ph: float


class SoilSensor:
    def __init__(self):
        self.instrument = None
        self.port = "/dev/ttyUSB1" # 포트
        
        # Modbus 설정
        self.slave_address = 1
        self.baudrate = 4800 
        self.bytesize = 8
        self.parity = serial.PARITY_NONE
        self.stopbits = 1
        self.timeout = 1.0

        # 스레드 제어용 변수
        self.running = False
        self.thread = None
        
        # 데이터 공유용 변수
        self._latest_data = None 
        self.data_lock = Lock()   # 데이터 충돌 방지

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
        직접 통신하지 않고, 스레드가 갱신해둔 최신 값만 리턴 하는 함수 (save_data.save_rawdata()에서 호출)
        """
        with self.data_lock:
            return self._latest_data

    def _connect(self):
        """내부용: 시리얼 연결 시도"""
        try:
            if self.instrument and self.instrument.serial.is_open:
                return True
                
            print(f"[Soil] 포트 연결 시도...")
            self.instrument = minimalmodbus.Instrument(self.port, self.slave_address)
            self.instrument.serial.baudrate = self.baudrate
            self.instrument.serial.bytesize = self.bytesize
            self.instrument.serial.parity = self.parity
            self.instrument.serial.stopbits = self.stopbits
            self.instrument.serial.timeout = self.timeout
            self.instrument.mode = minimalmodbus.MODE_RTU
            print("[Soil] 포트 연결 성공!")
            return True
        except Exception as e:
            print(f"[Soil] 연결 실패: {e}")
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
                values = self.instrument.read_registers(0, 4, functioncode=3)
                
                new_data = SoilData(
                    soil_temperature=values[1] / 10.0,
                    soil_humidity=values[0] / 10.0,
                    soil_ec=int(values[2]),
                    soil_ph=values[3] / 10.0
                )

                # 성공 시 데이터 업데이트
                with self.data_lock:
                    self._latest_data = new_data
                
                time.sleep(0.5) # 0.5초 간격 갱신

            except Exception as e:
                print(f"[Soil Error] 읽기 실패 (센서 연결을 확인해 주세요): {e}")
                
                # 이전 값을 유지하고 싶으면 이 부분은 주석 처리하세요.
                # with self.data_lock:
                # self._latest_data = None
                
                # 연결 재설정을 위해 초기화
                if self.instrument:
                    try:
                        self.instrument.serial.close()
                    except:
                        pass
                    self.instrument = None
                
                time.sleep(3)


class SoilSensorSingleton:
    _instance = None
    _lock = Lock()

    @classmethod
    def instance(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = SoilSensor()
            return cls._instance
