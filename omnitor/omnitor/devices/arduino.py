import serial
import threading
import time
import serial.tools.list_ports
from dataclasses import dataclass
from threading import Lock

@dataclass
class DataPacket:
    air_temperature: float = 0.0
    air_humidity: float = 0.0
    co2: int = 0
    insolation: float = 0.0
    weight_raw: int = 0
    ph_voltage: float = 0.0
    ec_voltage: float = 0.0
    water_temperature: float = 0.0
    tip_count: int = 0

class ArduinoSerial:
    def __init__(self, baudrate=9600, timeout=1):
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser = None
        self.running = False
        self.lock = Lock()
        
        # [IMPORTANT] Initialize with 0 to prevent NoneType errors in save_data.py
        self.current_data = DataPacket()

    def get_current_data(self):
        with self.lock:
            # Safety check: if None, return a zero-filled packet
            if self.current_data is None:
                return DataPacket()
            return self.current_data

    def find_port(self):
        ports = serial.tools.list_ports.comports()
        for port in ports:
            # Find port containing "Arduino", "USB", or "ACM"
            if "Arduino" in port.description or "USB" in port.description or "ACM" in port.device:
                return port.device
        return None

    def connect(self):
        port = self.find_port()
        if not port:
            print("[Arduino] Port not found.")
            return False
        try:
            print(f"[Arduino] Connecting to: {port}")
            self.ser = serial.Serial(port, self.baudrate, timeout=self.timeout)
            time.sleep(2)
            self.ser.reset_input_buffer()
            print("[Arduino] Connected successfully.")
            return True
        except Exception as e:
            print(f"[Arduino] Connection Failed: {e}")
            return False
        
    def read_loop(self):
        """
        [Simple Mode]
        Reads a line of text, splits by comma, and parses 9 values.
        Expected format: "25.5,60.2,400,150.0,12345,6.5,1.2,24.0,10"
        """
        while self.running:
            try:
                if self.ser and self.ser.in_waiting > 0:
                    # 1. Read a line and decode to string
                    line = self.ser.readline().decode('utf-8', errors='ignore').strip()

                    if not line:
                        continue

                    # 2. Split by comma
                    parts = line.split(',')

                    # 3. Check if we have exactly 9 values
                    if len(parts) == 9:
                        try:
                            new_data = DataPacket(
                                air_temperature=float(parts[0]),
                                air_humidity=float(parts[1]),
                                co2=int(float(parts[2])),
                                insolation=float(parts[3]),
                                weight_raw=int(float(parts[4])),
                                ph_voltage=float(parts[5]),
                                ec_voltage=float(parts[6]),
                                water_temperature=float(parts[7]),
                                tip_count=int(float(parts[8]))
                            )

                            with self.lock:
                                self.current_data = new_data
                            
                            # [Debug] Print received data
                            print(f"[DATA] {new_data}")

                        except ValueError:
                            # Ignore lines with parsing errors
                            pass
                else:
                    time.sleep(0.01)

            except Exception as e:
                print(f"[Arduino] Read Error: {e}")
                self._reconnect()

    def _reconnect(self):
        if self.ser:
            try: self.ser.close()
            except: pass
        time.sleep(2)
        while not self.connect():
            time.sleep(2)

    def start(self):
        if not self.connect(): return
        self.running = True
        read_thread = threading.Thread(target=self.read_loop, daemon=True)
        read_thread.start()

    def stop(self):
        self.running = False
        if self.ser: self.ser.close()

    # Empty methods for compatibility with other files
    def write(self, msg): pass
    def command(self, command: int): pass

class SerialSingleton:
    _instance = None
    _lock = Lock()
    @classmethod
    def instance(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = ArduinoSerial()
            return cls._instance
        

#if __name__ == "__main__":
#    arduino_serial = SerialSingleton.instance()
#    arduino_serial.start()
#    while True:
#    time.sleep(1)
#    print("--------------------------------")
#    print(arduino_serial.get_current_data())
#    print("--------------------------------")
