import serial
import time
import minimalmodbus
import serial.tools.list_ports
from dataclasses import dataclass
from threading import Lock

# 토양 센서 데이터 구조 정의
@dataclass
class SoilData:
    soil_temperature: float
    soil_humidity: float
    soil_ec: int
    soil_ph: float


class SoilSensor:
    def __init__(self):
        self.instrument = None
        self.lock = Lock()
        self.port = None

        self.slave_address = 1
        self.baudrate = 4800 
        self.bytesize = 8
        self.parity = serial.PARITY_NONE
        self.stopbits = 1
        self.timeout = 1.0

    def find_port(self):
        #ports = serial.tools.list_ports.comports()
        #for port in ports:
        #    if ("serial" in port.description):
                # return port.device
        #        return "/dev/ttyUSB0"
        #print('Cannot find soil port')
        return "/dev/Soil"
    
    def start(self):
        with self.lock:
            if self.instrument:
                return True
            
            self.port = self.find_port()
            print(f"[Soil] 포트 연결 시도: {self.port}")
            
            if not self.port:
                print("[Soil] 포트를 찾지 못했습니다.")
                return False
            
            try:
                print("[Soil] 포트 연결 성공!")
                self.instrument = minimalmodbus.Instrument(self.port, self.slave_address)
                self.instrument.serial.baudrate = self.baudrate
                self.instrument.serial.bytesize = self.bytesize
                self.instrument.serial.parity = self.parity
                self.instrument.serial.stopbits = self.stopbits
                self.instrument.serial.timeout = self.timeout
                self.instrument.mode = minimalmodbus.MODE_RTU
                return True
            
            except Exception as e:
                print(f"[Soil] 초기화 실패: {e}")
                self.instrument = None
                return False

    def get_current_data(self):
        with self.lock:
            if not self.instrument:
                if not self.start():
                    return None
            
            try:
                #print("Try to read register")
                values = self.instrument.read_registers(0, 4, functioncode=3)
                #print("Done")
                soil_temperature = values[0] / 10.0 
                soil_humidity = values[1] / 10.0
                soil_ec = values[2]
                soil_ph = values[3] / 10.0 

                return SoilData(
                    soil_temperature=soil_temperature,
                    soil_humidity=soil_humidity,
                    soil_ec=int(soil_ec),
                    soil_ph=soil_ph
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


class SoilSensorSingleton:
    _instance = None
    _lock = Lock()

    @classmethod
    def instance(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = SoilSensor()
            return cls._instance
