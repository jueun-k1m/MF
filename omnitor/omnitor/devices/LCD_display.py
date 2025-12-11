import os
import sys
import time
import LCD1602 

from models import FinalData

project_path = os.path.abspath(os.path.dirname(__file__))
sys.path.append(project_path)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'imojang.settings')
import django
django.setup()


try:
    LCD1602.init(0x27, 1)
    print("LCD initialized successfully.")
except Exception as e:
    print(f"Error initializing LCD: {e}")
    print("Please check I2C connection and address (sudo i2cdetect -y 1)")
    sys.exit(1)

# ------------------

def display_data():
    try:
        latest_data = FinalData.objects.latest('timestamp')

        weight_g = latest_data.weight
        temp = latest_data.air_temperature
        humid = latest_data.air_humidity


        weight_kg_str = f"{weight_g / 1000.0:.2f}" if weight_g is not None else "--.--"
        temp_str = f"{temp:.1f}" if temp is not None else "--.-"
        humid_str = f"{humid:.1f}" if humid is not None else "--.-"

        line1 = f"{weight_kg_str}kg".ljust(16)
        line2 = f"{temp_str}*C | {humid_str}%".ljust(16)
        # ----------------------------------------

        LCD1602.write(0, 0, line1[:16])
        LCD1602.write(0, 1, line2[:16])

        print(f"Displayed: {line1.strip()} | {line2.strip()}")

    except FinalData.DoesNotExist:
        LCD1602.clear()
        LCD1602.write(0, 0, "No data yet...")
        print("No data found in database.")
    except Exception as e:
        LCD1602.clear()
        LCD1602.write(0, 0, "Display Error!")
        print(f"An error occurred: {e}")

def main():
    print("--- LCD Display Service Started (Weight, Temp, Hum) ---")
    print("Press Ctrl+C to exit.")
    try:
        while True:
            display_data()
            time.sleep(5) 
    except KeyboardInterrupt:
        print("\nExiting LCD service.")
    finally:
        LCD1602.clear()
        print("LCD cleared.")

if __name__ == "__main__":
    main()
