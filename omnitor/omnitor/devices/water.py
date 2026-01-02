import serial
import minimalmodbus
from dataclasses import dataclass
from threading import Lock

# 토양 센서 데이터 구조 정의
@dataclass
class WaterData:
    water_temperature: float
    water_ec: float
    water_ph: float


class WaterSensor:
    def __init__(self):
        self.instrument = None
        self.lock = Lock()
        self.port = None

        self.slave_address = 1
        self.baudrate = 9600
        self.bytesize = 8
        self.parity = serial.PARITY_NONE
        self.stopbits = 1
        self.timeout = 1.0
    
    def start(self):
        with self.lock:
            if self.instrument:
                return True
            
            self.port = "/dev/ttyUSB0"
            print(f"[Water1] 포트 연결 시도: {self.port}")
            
            if not self.port:
                print("[Water2] 포트를 찾지 못했습니다.")
                return False
            
            try:
                print("[Water3] 포트 연결 성공!")
                self.instrument = minimalmodbus.Instrument(self.port, self.slave_address)
                self.instrument.serial.baudrate = self.baudrate
                self.instrument.serial.bytesize = self.bytesize
                self.instrument.serial.parity = self.parity
                self.instrument.serial.stopbits = self.stopbits
                self.instrument.serial.timeout = self.timeout
                self.instrument.mode = minimalmodbus.MODE_RTU
                return True
            
            except Exception as e:
                print(f"[Water4] 초기화 실패: {e}")
                self.instrument = None
                return False

    def get_current_data(self):
        with self.lock:
            if not self.instrument:
                if not self.start():
                    return None
            
            try:
                values = self.instrument.read_registers(0, 3, functioncode=3)
                
                water_ph = values[0] / 100.0 
                water_ec = values[1]
                water_temperature = values[2] / 10.0 

                return WaterData(
                    water_temperature=water_temperature,
                    water_ec=water_ec,
                    water_ph=water_ph
                )
            
            except Exception as e:
                self.instrument.serial.close()
                self.instrument = None
                return None
            
        
    def stop(self):
        if self.instrument:
                try:
                    self.instrument.serial.close()
                except:
                    pass
                    self.instrument = None


class WaterSensorSingleton:
    _instance = None
    _lock = Lock()

    @classmethod
    def instance(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = WaterSensor()
            return cls._instance
