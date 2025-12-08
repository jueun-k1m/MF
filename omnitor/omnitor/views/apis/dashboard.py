from django.http import JsonResponse
from models import FinalData  # 같은 앱 폴더 내에 있다면 .models 사용

def dashboard_api(request):
    """
    [API] 대시보드
    최신 FinalData 리턴
    """
    # DB에서 가장 최근 데이터 가져오기
    final_data = FinalData.objects.last()

    # 데이터가 없을 경우 (빈 딕셔너리 혹은 에러 메시지 반환)
    if not final_data:
        return JsonResponse({
            'success': False,
            'message': "데이터가 아직 없습니다."
        })

    # 데이터가 있을 경우 JSON 구조 생성
    response_data = {
        'success': True,
        'timestamp': final_data.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        'air_temperature': final_data.air_temperature,
        'air_humidity': final_data.air_humidity,
        'co2': final_data.co2,
        'insolation': final_data.insolation,
        'weight': final_data.weight,
        'water_temperature': final_data.water_temperature,
        'ph': final_data.ph,
        'ec': final_data.ec,
        'tip_total': final_data.tip_total,
        'soil_temperature': final_data.soil_temperature,
        'soil_humidity': final_data.soil_humidity,
        'soil_ph': final_data.soil_ph,
        'soil_ec': final_data.soil_ec,
    }

    # JSON 응답 반환
    return JsonResponse(response_data)
