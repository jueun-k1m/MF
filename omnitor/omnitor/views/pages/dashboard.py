# Gemini

from django.http import JsonResponse
from models import FinalData, RawData  # models.py가 같은 앱 내에 있다고 가정

def get_handler(request):
    """
    대시보드 갱신용 API
    가장 최근의 FinalData와 RawData를 가져와 JSON으로 반환합니다.
    """
    
    # 1. 가장 최근 데이터 가져오기
    # 여기서는 간단히 가장 마지막에 들어온 데이터(.last())를 가져옵니다.
    final_data = FinalData.objects.last()
    raw_data = RawData.objects.last()

    # 2. 데이터가 하나도 없을 경우를 대비한 기본값 처리
    response_data = {}

    if final_data:
        response_data.update({
            'air_temperature': final_data.air_temperature,
            'air_humidity': final_data.air_humidity,
            'co2': final_data.co2,
            'insolation': final_data.insolation,
            'weight': final_data.weight,
            'water_temperature': final_data.water_temperature,
            'ph': final_data.ph,
            'ec': final_data.ec,
            'soil_temperature': final_data.soil_temperature,
            'soil_humidity': final_data.soil_humidity,
            'soil_ph': final_data.soil_ph,
            'soil_ec': final_data.soil_ec,
        })
    else:
        # DB가 비어있을 경우 NULL 혹은 0으로 처리
        response_data['error_final'] = "No FinalData found"

    # 3. RawData 처리 및 tip_total 계산
    if raw_data:
        # 요구하신 계산 로직: tip_count * 5
        tip_total = raw_data.tip_count * 5
        response_data['tip_total'] = tip_total
    else:
        response_data['tip_total'] = 0

    # 4. JSON 응답 반환
    return JsonResponse(response_data)
