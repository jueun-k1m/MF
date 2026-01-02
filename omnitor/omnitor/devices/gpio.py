import time
import threading
import serial
import board
import adafruit_dht
from smbus2 import SMBus

try:
    import RPi.GPIO as GPIO
except ImportError:
    import rpi_lgpio as GPIO

class GPIOSensor:
    def __init__(self):
        self.running = False
        self._lock = threading.Lock()
        
        self.data = {
            "co2": None,
            "lux": None,
            "weight": None,
            "temperature": None,
            "humidity": None,
            "tip_count": 0
        }

        # 인터럽트 방식
        self.REED_PIN = 18
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.REED_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        # 신호가 올라갈 때 감지하여 _reed_callback 함수 실행
        GPIO.add_event_detect(self.REED_PIN, GPIO.RISING, callback=self._reed_callback, bouncetime=200)

        # 센서 장치 초기화
        self._setup_sensors()

    def _setup_sensors(self):
        """각종 센서 연결 시도"""
        # CO2 센서 (UART /dev/ttyAMA0)
        try:
            self.co2_ser = serial.Serial('/dev/ttyAMA0', baudrate=9600, timeout=1)
        except Exception as e:
            print(f"[GPIO] CO2 Setup Fail: {e}")
            self.co2_ser = None

        # 조도 센서 (I2C)
        try:
            self.bus = SMBus(1)
            self.BH1750_ADDR = 0x23
        except:
            self.bus = None

        # 온습도 센서
        try:
            self.dht = adafruit_dht.DHT22(board.D4)
        except:
            self.dht = None

        # 로드셀 (HX711)
        try:
            from hx711 import HX711
            self.hx = HX711(dout_pin=5, pd_sck_pin=6)
            self.hx.reset()
        except ImportError:
            self.hx = None
            print("[GPIO] hx711 library missing")
        except Exception as e:
            self.hx = None
            print(f"[GPIO] HX711 Setup Fail: {e}")

    def _reed_callback(self, channel):
        """리드 스위치 신호가 올 때마다 실행 (인터럽트)"""
        with self._lock:
            self.data["tip_count"] += 1

    def _calculate_checksum(self, packet):
        if len(packet) != 9: return 0
        checksum = 0
        for i in range(1, 8):
            checksum = (checksum + packet[i]) & 0xFF
        checksum = 0xFF - checksum
        checksum = (checksum + 1) & 0xFF
        return checksum

    def _read_co2(self):
        if self.co2_ser is None: return None
        cmd = b"\xff\x01\x86\x00\x00\x00\x00\x00\x79"
        try:
            self.co2_ser.reset_input_buffer()
            self.co2_ser.write(cmd)
            time.sleep(0.1) 
            if self.co2_ser.in_waiting >= 9:
                response = self.co2_ser.read(9)
                if response[0] == 0xFF and response[1] == 0x86:
                    if self._calculate_checksum(response) == response[8]:
                        return response[2] * 256 + response[3]
        except:
            pass
        return None

    def _update_loop(self):
        """백그라운드에서 센서 값을 주기적으로 갱신"""
        while self.running:
            # CO2
            co2 = self._read_co2()
            
            # 조도 센서
            lux = None
            if self.bus:
                try:
                    raw = self.bus.read_i2c_block_data(self.BH1750_ADDR, 0x10, 2)
                    lux = (raw[0] << 8 | raw[1]) / 1.2
                except: pass
            
            # 로드셀 센서
            weight = None
            if self.hx:
                try:
                    w_raw = self.hx.get_raw_data()
                    weight = w_raw[0] if isinstance(w_raw, list) else w_raw # 리스트로 받는 값을 한 값으로 처리해서 저장
                except: pass

            # 온습도 센서
            temp, hum = None, None
            if self.dht:
                try:
                    temp = self.dht.temperature
                    hum = self.dht.humidity
                except RuntimeError:
                    pass

            # === 데이터 업데이트 ===
            with self._lock:
                self.data["co2"] = co2
                self.data["insolation"] = (lux/54.0) * (1.0/4.57)
                self.data["weight"] = weight
                self.data["temperature"] = temp
                self.data["humidity"] = hum
                # tip_count는 callback에서 별도로 업데이트됨

            time.sleep(2) # 2초마다 갱신

    def start(self):
        """GPIO 시작"""
        if not self.running:
            self.running = True
            t = threading.Thread(target=self._update_loop, daemon=True)
            t.start()

    def get_current_data(self):
        """외부 호출용: 현재 저장된 최신 데이터 반환 (즉시 리턴)"""
        with self._lock:
            current = self.data.copy()
            current["tip_count"] = current["tip_count"]
            return current

    def cleanup(self):
        self.running = False
        if self.co2_ser: self.co2_ser.close()
        if self.bus: self.bus.close()
        if self.dht: self.dht.exit()
        GPIO.cleanup()


# === 싱글톤 패턴 ===
class GPIOSensorSingleton:
    _instance = None
    _lock = threading.Lock()

    @classmethod
    def instance(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = GPIOSensor()
            return cls._instance
