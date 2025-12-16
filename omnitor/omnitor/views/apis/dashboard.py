# gemini

import json
from django.http import JsonResponse
from omnitor.models import FinalData  # 모델 경로 확인 필요

def dashboard_api(request):
    
    """
    [API] 대시보드 데이터 조회
    가장 최근 저장된 FinalData 1개를 가져와 반환합니다.
    """
    
    # ======== GET: 최신 데이터 조회 ========
    if request.method == 'GET':
        try:
            # 최신 데이터 1개 조회 (timestamp 기준 내림차순 정렬 후 첫 번째 or last())
            latest_data = FinalData.objects.latest()

            # 데이터가 아예 없는 경우 예외 처리
            if latest_data is None:
                return JsonResponse({'message': '아직 수집된 데이터가 없습니다.'}, status=204)

            # 이미 FinalData에 save_data에서 업로드함. 정리해서 json response로 반환만 하면 됨
            response_data = {
                'timestamp': latest_data.timestamp.strftime('%Y-%m-%d %H:%M:%S'),

                # 환경 데이터
                'air_temperature': latest_data.air_temperature,
                'air_humidity': latest_data.air_humidity,
                'co2': latest_data.co2,
                'insolation': latest_data.insolation,
                # 'total_insolation': latest_data.total_insolation,
                # 'vpd': latest_data.vpd,                           
                
                # 함수량 및 관수/배액
                'weight': latest_data.weight,
                'irrigation': latest_data.irrigation,             # 이번 텀의 관수량
                # 'total_irrigation': latest_data.total_irrigation, # 오늘 누적 관수량
                'drainage': latest_data.total_drainage,           # 오늘 누적 배액량 total_drainage (tip_count * capacity)

                # 배액 센서 데이터
                'water_temperature': latest_data.water_temperature,
                'ph': latest_data.ph,
                'ec': latest_data.ec,
                
                # 토양 센서 데이터
                'soil_temperature': latest_data.soil_temperature,
                'soil_humidity': latest_data.soil_humidity,
                'soil_ph': latest_data.soil_ph,
                'soil_ec': latest_data.soil_ec
            }
            
            return JsonResponse(response_data) # 200 OK

        except Exception as e:
            # 서버 내부 에러 로깅
            print(f"[API Error] dashboard_api: {e}")
            return JsonResponse({'error': '서버 내부 오류가 발생했습니다.'}, status=500)

    # GET 이외의 요청 거부
    else:
        return JsonResponse({'error': 'Method not allowed'}, status=405)
