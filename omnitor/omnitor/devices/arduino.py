import serial
import threading
import queue
import time
import struct
import serial.tools.list_ports
from dataclasses import dataclass
from threading import Lock
PACKET_HEADER_1 = 0xAA
PACKET_HEADER_2 = 0x55
@dataclass
class DataPacket:
  air_temperature: float
  air_humidity: float
  co2: float
  insolation: float
  weight: float
  ph_voltage: float
  ec_voltage: float
  water_temperature: float
  tip_count: float
@dataclass
class CommandPacket:
  command: int
class ArduinoSerial:
    def __init__(self, baudrate=9600, timeout=1):
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser = None
        self.read_thread = None
        self.write_thread = None
        self.write_queue = queue.Queue()
        self.running = False
        self.current_data = None
        self.lock = Lock()
    def get_current_data(self):
      with self.lock:
        return self.current_data
    def find_port(self):
        # ports = serial.tools.list_ports.comports()
        # for port in ports:
        #     if "Arduino" in port.description:
        #         return port.device
        return "/dev/Arduino"
    def connect(self):
        port = self.find_port()
        if not port:
            print("[Arduino] 포트를 찾지 못했습니다.")
            return False
        try:
            print(f"[Arduino] 포트 연결 시도: {port}")
            self.ser = serial.Serial(port, self.baudrate, timeout=self.timeout)
            time.sleep(2)
            print("[Arduino] 연결 성공")
            return True
        except serial.SerialException as e:
            print(f"[Arduino] : {e}")
            return False
    def read_loop(self):
        buffer = []
        while self.running:
            try:
                if self.ser.in_waiting > 0:
                  chunk = self.ser.read(self.ser.in_waiting)
                  buffer.extend(chunk)
                  while True:
                      payload = self.extract_packet(buffer)
                      if payload is None:
                          break
                      with self.lock :
                        self.current_data = self.parse_packet(payload)
                else:
                  time.sleep(0.01)
            except Exception as e:
                print(f"[Arduino] Write 오류: {e}")
                self._reconnect()
    def write_loop(self):
        while self.running:
            try:
                msg = self.write_queue.get()
                if self.ser and self.ser.is_open:
                    self.ser.write(msg)
                time.sleep(0.01)
            except Exception as e:
                print(f"[Arduino] Write 오류: {e}")
                self._reconnect()
    def _reconnect(self):
        print(("[Arduino] 재연결 시도중..."))
        if self.ser:
            try:
                self.ser.close()
            except:
                pass
        time.sleep(2)
        while not self.connect():
            print("[Arduino] 재연결 실패 - 2초 후 재시도")
            time.sleep(2)
    def start(self):
        if not self.connect():
            print("[Arduino] 시작 실패: 연결 못함")
            return
        self.running = True
        self.read_thread = threading.Thread(target=self.read_loop, daemon=True)
        self.write_thread = threading.Thread(target=self.write_loop, daemon=True)
        self.read_thread.start()
        self.write_thread.start()

    def command(self, command: int):
      self.write_queue.put(self.encode_command_packet(CommandPacket(command=command)))
    def write(self, msg):
        self.write_queue.put(msg)
    def stop(self):
        self.running = False
        if self.ser and self.ser.is_open:
            self.ser.close()
        print("[Arduino] 종료됨")
    def extract_packet(self,buffer: bytearray):
      # 최소 헤더(2) + length(1) + CRC(2)
      if len(buffer) < 5:
          return None
      while len(buffer) >= 2 and (buffer[0] != PACKET_HEADER_1 or buffer[1] != PACKET_HEADER_2):
          buffer.pop(0)
      if len(buffer) < 3:
          return None
      length = buffer[2]   # payload size (32 bytes expected)
      needed = 3 + length + 2  # header2 + length + payload + crc
      if len(buffer) < needed:
          return None  # not enough data
      packet = bytes(buffer[:needed])
      del buffer[:needed]

    # CRC
      payload = packet[3:3+length]
      recv_crc = packet[3+length] | (packet[3+length+1] << 8)
      calc_crc = self.crc16_modbus(packet[:3] + payload)
      #print(f"recv_crc: {recv_crc}, calc_crc: {calc_crc}")
      if recv_crc != calc_crc:
          #print("[Parse] CRC mismatch")
          return None
      return payload
    def parse_packet(self, packet: bytes) -> DataPacket:
      floats = struct.unpack("<9f", packet)  # little endian
      return DataPacket(*floats)
    def crc16_modbus(self, data: bytes) -> int:
      crc = 0xFFFF
      for pos in data:
          crc ^= pos
          for _ in range(8):
              if (crc & 0x0001) != 0:
                  crc >>= 1
                  crc ^= 0xA001
              else:
                  crc >>= 1
      return crc
    def encode_command_packet(self, packet: CommandPacket) -> bytes:
      PACKET_HEADER_1 = 0xAA
      PACKET_HEADER_2 = 0x55
      # payload = int32 (4 bytes)
      payload = struct.pack("<i", packet.command)  # little-endian 32bit int
      length = len(payload)  # ALWAYS 4
      # [H1][H2][LEN][PAYLOAD][CRC(2B)]
      header = bytes([PACKET_HEADER_1, PACKET_HEADER_2, length])
      crc_input = header + payload
      crc = self.crc16_modbus(crc_input)
      crc_bytes = bytes([crc & 0xFF, (crc >> 8) & 0xFF])
      return header + payload + crc_bytes
class SerialSingleton:
    _instance = None
    _lock = Lock()
    @classmethod
    def instance(cls) -> ArduinoSerial:
        with cls._lock:
            if cls._instance is None:
                cls._instance = ArduinoSerial()
            return cls._instance
        
# if __name__ == "__main__":
#    arduino_serial = SerialSingleton.instance()
#    arduino_serial.start()
#    while True:
#        time.sleep(1)
#        print("--------------------------------")
#        print(arduino_serial.get_current_data())
#        print("--------------------------------")
