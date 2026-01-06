from omnitor.models import RawData
from django.forms.models import model_to_dict

WINDOW_SIZE = 5

# 평균을 낼 필드 목록을 미리 정의 (timestamp 등 제외)
TARGET_FIELDS = [
    'air_temperature', 'air_humidity', 'co2', 'insolation', 
    'weight', 'water_ph', 'water_ec', 'water_temperature', 
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
    (None 값은 제외하고 계산하여 에러 방지)
    """

    # 1. 최신 데이터 가져오기 (None 포함될 수 있음)
    val_5 = RawData.objects.values_list(field_name, flat=True).order_by('-timestamp')[:WINDOW_SIZE]

    # 2. None 값 제거 (List Comprehension)
    valid_values = [v for v in val_5 if v is not None]

    # 3. 유효한 데이터가 없으면 0 반환
    if not valid_values:
        return 0
    
    # 4. 평균 계산
    average_val = sum(valid_values) / len(valid_values)
    
    return average_val
