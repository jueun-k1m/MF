from omnitor.models import RawData
from django.forms.models import model_to_dict

WINDOW_SIZE = 5

# 평균을 낼 필드 목록을 미리 정의 (timestamp 등 제외)
TARGET_FIELDS = [
    'air_temperature', 'air_humidity', 'co2', 'insolation', 
    'weight', 'ph', 'ec', 'water_temperature', 
    'soil_temperature', 'soil_humidity', 'soil_ec', 'soil_ph'
] 

def maf_all():
    """
    DB에서 최신 window_size개를 가져와 평균을 계산하여 반환
    """
    # 1. 최신 데이터 N개 가져오기 (내림차순 정렬 후 슬라이싱)
    latest_records = RawData.objects.order_by('-timestamp')[:WINDOW_SIZE]

    if not latest_records:
        return None

    # 2. 데이터를 딕셔너리 리스트로 변환
    data_list = [model_to_dict(record) for record in latest_records]

    filtered_result = {}

    # 3. 각 필드별로 평균 계산
    for field in TARGET_FIELDS:
        # 해당 필드의 값들만 모음 (None 제외)
        values = [d[field] for d in data_list if d.get(field) is not None]
        
        if values:
            filtered_result[field] = sum(values) / len(values)
        else:
            filtered_result[field] = 0 # 혹은 None

    return filtered_result

def avg(field_name):
    """
    DB에서 특정 필드의 최신 값 WINDOW_SIZE개를 가져와 평균을 계산하여 반환
    CalibrationData filtered 값 저장할 때 사용
    :param field_name: 평균을 낼 필드 이름
    :return: 해당 필드의 평균 값
    """

    # 1. 최신 데이터 5개 가져오기
    val_5 = RawData.objects.values_list(field_name, flat=True).order_by('-timestamp')[:WINDOW_SIZE]

    # 2. 데이터가 없으면 None 반환
    if not val_5:
        return 0
    
    # 3. 평균 계산
    average_val = sum(val_5) / len(val_5) # (주의: 함수명과 변수명이 같음)
    
    return average_val
