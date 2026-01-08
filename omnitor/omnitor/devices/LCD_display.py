from RPLCD.i2c import CharLCD
import time

class LCDManager:
    def __init__(self):
        try:
            self.lcd = CharLCD(i2c_expander='PCF8574', address=0x27, port=3,
                               cols=16, rows=2, dotsize=8,
                               charmap='A00',
                               auto_linebreaks=True,
                               backlight_enabled=True)
            self.available = True
            print("[LCD_display.py] 초기화 성공 !")
        except Exception as e:
            self.lcd = None
            self.available = False
            print(f"[LCD_display.py] 초기화 실패... {e}")

    def update(self):

        if not self.available:
            return

        from omnitor.models import FinalData 


        try:
            data = FinalData.objects.last()
            time.sleep(1)

            if data:
                temp = getattr(data, 'air_temperature', 0)
                humid = getattr(data, 'air_humidity', 0)
                weight = getattr(data, 'weight', 0)
                irrig = getattr(data, 'total_irrigation', 0)
                # print(f"[LCD_display.py] Updating: Temp={temp}, Humid={humid}, Weight={weight}, Irrig={irrig}")

                self.lcd.clear()
                self.lcd.cursor_pos = (0, 0)
                self.lcd.write_string(f"{temp:.1f}°C  {weight:.1f}g")
                
                self.lcd.cursor_pos = (1, 0)
                self.lcd.write_string(f"{humid:.1f}%  {irrig:.1f}mL")
            else:
                self.lcd.clear()
                self.lcd.cursor_pos = (0, 0)
                self.lcd.write_string("Waiting for")
                self.lcd.cursor_pos = (1, 0)
                self.lcd.write_string("data...")

        except Exception as e:
            print(f"[LCD_display.py] Update Error: {e}")
