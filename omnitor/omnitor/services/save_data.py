import os
import sys
import time
import threading  # [핵심] 스레딩 모듈 추가
import django
from datetime import datetime

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
sys.path.append(root_dir)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "omnitor.settings")
django.setup()

from omnitor.models import RawData, CalibrationSettings, FinalData
from django.db import connection, close_old_connections
from django.db.models import Sum
from django.utils import timezone

from devices.arduino import SerialSingleton
from devices.soil import SoilSensorSingleton
from omnitor.omnitor.services.filtering import maf_all

# 전역 변수
prev_weight = 0
tip_capacity = 5

def run_rawdata_loop():
    """
    [Thread 1] 0.1초마다 센서 데이터를 읽어 RawData에 저장
    """
    print(">>> RawData 수집 스레드 시작 (0.1s)")
    
    # 싱글톤 인스턴스 가져오기
    arduino = SerialSingleton.instance()
    soil = SoilSensorSingleton.instance()

    # 포트가 안 열려있으면 열기
    if not arduino.ser or not arduino.ser.is_open:
        arduino.start()
    # soil 센서는 start() 구현 여부에 따라 호출 (일반적으로 필요)
    # soil.start() 

    while True:
        try:
            # [중요] 스레드 환경에서 DB 연결 끊김 방지
            close_old_connections()
            
            arduino_data = arduino.get_current_data()
            soil_data = soil.get_current_data()

            if arduino_data and soil_data:
                now = datetime.now()
                
                RawData.objects.create(
                    timestamp=now,
                    air_temperature=arduino_data.air_temperature,
                    air_humidity=arduino_data.air_humidity,
                    co2=int(arduino_data.co2),
                    insolation=arduino_data.insolation,
                    weight=int(arduino_data.weight_raw),
                    ph=arduino_data.ph_voltage,
                    ec=arduino_data.ec_voltage,
                    water_temperature=arduino_data.water_temperature,
                    tip_count=int(arduino_data.tip_count),
                    
                    soil_temperature=soil_data.soil_temperature,
                    soil_humidity=soil_data.soil_humidity,
                    soil_ec=soil_data.soil_ec,
                    soil_ph=soil_data.soil_ph
                )
            # else:
            #     print("센서 데이터 대기 중...") # 로그 너무 많이 찍히면 주석 처리

            time.sleep(0.1)

        except Exception as e:
            print(f"[RawData Error] {e}")
            time.sleep(1)

def run_finaldata_loop():
    """
    [Thread 2] 57초마다 RawData를 가공하여 FinalData에 저장
    """
    print(">>> FinalData 저장 스레드 시작 (57s)")
    
    global prev_weight # 전역 변수 사용 명시

    while True:
        try:
            # [중요] DB 연결 리셋 (필수)
            close_old_connections()
            
            # 57초 대기 (먼저 쉬고 실행할지, 실행하고 쉴지는 선택)
            time.sleep(57) 
            
            now = timezone.now()
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

            # 이동평균 필터 적용 데이터 가져오기
            filtered_data = maf_all()
            
            # RawData에서 tip_count 같은 누적값 가져오기 위해 최신값 조회
            try:
                raw_latest = RawData.objects.latest('timestamp')
            except RawData.DoesNotExist:
                print("아직 RawData가 없습니다.")
                continue

            if filtered_data:
                # 1. VPD 계산 (오타 수정: 0.6(...) -> 수식 교정)
                temp = filtered_data['air_temperature']
                hum = filtered_data['air_humidity']
                
                # ZeroDivisionError 방지
                if temp is None: temp = 0
                if hum is None: hum = 0
                
                vpd = ((0.6107 * 10 ** (7.5 * temp / (237.3 + temp))) * (1 - (hum / 100)))

                # 2. 관수량 계산
                current_weight = filtered_data['weight']
                irrigation = 0
                
                # 이전 무게가 있고, 무게가 증가했다면 관수로 판단
                if prev_weight > 0 and current_weight > prev_weight:
                     irrigation = current_weight - prev_weight
                
                # 3. 보정 설정 로드
                cal_settings = CalibrationSettings.objects.last()
                if not cal_settings:
                    # 임시 클래스 생성보다 딕셔너리나 기본값 처리가 안전
                    cal_settings = type('obj', (object,), {
                        'weight_slope': 1, 'weight_intercept': 0,
                        'ph_slope': 1, 'ph_intercept': 0,
                        'ec_slope': 1, 'ec_intercept': 0
                    })

                # 4. 누적값 계산 (aggregate 결과는 딕셔너리입니다!)
                # 주의: 지금 막 생성하려는 데이터는 DB에 없으므로 합계에 포함 안 됨.
                # 과거 데이터 합 + 현재 값으로 계산해야 정확함.
                agg_result = FinalData.objects.filter(timestamp__gte=today_start).aggregate(
                    sum_insol=Sum('insolation'),
                    sum_irrig=Sum('irrigation')
                )
                
                # None 체크 (데이터 없으면 0)
                total_insolation = (agg_result['sum_insol'] or 0) + filtered_data['insolation']
                total_irrigation = (agg_result['sum_irrig'] or 0) + irrigation

                # 5. FinalData 저장
                FinalData.objects.create(
                    timestamp=now,
                    
                    # 환경
                    air_temperature=temp,
                    air_humidity=hum,
                    co2=filtered_data['co2'],
                    insolation=filtered_data['insolation'],
                    total_insolation=total_insolation,
                    vpd=vpd,

                    # 함수량
                    weight=(cal_settings.weight_slope * current_weight) + cal_settings.weight_intercept,
                    irrigation=irrigation,
                    total_irrigation=total_irrigation,
                    total_drainage=raw_latest.tip_count * tip_capacity,

                    # 배액/토양
                    water_temperature=filtered_data['water_temperature'],
                    ph=(cal_settings.ph_slope * filtered_data['ph']) + cal_settings.ph_intercept,
                    ec=(cal_settings.ec_slope * filtered_data['ec']) + cal_settings.ec_intercept,
                    soil_temperature=filtered_data['soil_temperature'],
                    soil_humidity=filtered_data['soil_humidity'],
                    soil_ec=filtered_data['soil_ec'],
                    soil_ph=filtered_data['soil_ph']
                )

                print(f"[Saved] FinalData at {now.strftime('%H:%M:%S')}")
                
                # 다음 루프를 위해 현재 무게 저장
                prev_weight = current_weight

        except Exception as e:
            print(f"[FinalData Error] {e}")
            # 에러 나도 루프는 계속 돌게 둠

if __name__ == '__main__':
    # 메인 실행부
    
    # 스레드 1: RawData 수집 (0.1초)
    t1 = threading.Thread(target=run_rawdata_loop)
    t1.daemon = True # 메인 프로그램 종료 시 같이 종료되도록 설정
    
    # 스레드 2: FinalData 저장 (57초)
    t2 = threading.Thread(target=run_finaldata_loop)
    t2.daemon = True

    # 스레드 시작
    t1.start()
    t2.start()

    # 메인 스레드가 바로 종료되지 않도록 대기
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("프로그램을 종료합니다.")
