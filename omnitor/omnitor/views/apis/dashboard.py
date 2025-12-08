# views.py
import json
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseNotFound, HttpResponseNotAllowed
from models import FinalData

def dashboard_data_api(request):
    """
    [API] 대시보드 데이터 조회
    """
    # 1. GET 요청인지 확인 (보안 및 규격 준수)
    if request.method != 'GET':
        return HttpResponseNotAllowed(['GET']) # 405 Method Not Allowed

    try:
        # 2. DB 조회
        final_data = FinalData.objects.last()

        # 3. 데이터가 없는 경우 404 에러 반환
        if not final_data:
            return HttpResponseNotFound("아직 수집된 센서 데이터가 없습니다.") # 404 Not Found

        # 4. 성공 시 데이터 구성
        response_data = {
            'timestamp': final_data.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
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
        }

        return JsonResponse(response_data) # 200 OK (기본값)

    except Exception as e:
        # 서버 내부에서 예상치 못한 에러가 터졌을 때
        print(f"Server Error: {e}")
        return JsonResponse({'error': '서버 내부 오류가 발생했습니다.'}, status=500)
