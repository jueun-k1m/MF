import json
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseNotFound, HttpResponseNotAllowed
from models import FinalData


def dashboard_api(request):

    """
    [API] 대시보드 데이터 조회
    """

    # ======== GET: 날짜별 일지 & 사진 조회 ========
    if request.method == 'GET':

        try:
            # DB 조회
            latest_data = FinalData.objects.order_by('-timestamp').first()
            if not latest_data:
                return HttpResponseNotFound("아직 수집된 센서 데이터가 없습니다.") # 404 Not Found
            
            try:
                prev_data = latest_data.get_previous_by_timestamp()
            except FinalData.DoesNotExist:
                prev_data = None

            # 데이터가 없는 경우 에러 반환
            if not latest_data:
                return HttpResponseNotFound("아직 수집된 센서 데이터가 없습니다.") # 404 Not Found


            # VPD 계산
            temp = latest_data.air_temperature,
            hum = latest_data.air_humidity,
            vpd = ((0.6107 * 10 ** (7.5 * temp / (237.3 + temp))) * (1 - (hum / 100)))

            
            # 누적 함수량 계산
            instant_irrigation = 0
            if prev_data:
                instant_irrigation = latest_data.weight - prev_data.weight
    
            sum_insolation = 0



            # 데이터
            response_data = {
                'timestamp': latest_data.timestamp.strftime('%Y-%m-%d %H:%M:%S'),

                # 환경
                'air_temperature': temp,
                'air_humidity': hum,
                'co2': latest_data.co2,
                'insolation': latest_data.insolation,
                'cumulative_insolation': sum_insolation,
                'VPD' : vpd,
                
                # 함수량
                'weight': latest_data.weight,
                'irrigation' : latest_data.weight - prev_data.weight,
                'irrigation_total' : sum_irrigation,
                'drainage' : latest_data.tip_total,

                # 배액
                'water_temperature': latest_data.water_temperature,
                'ph': latest_data.ph,
                'ec': latest_data.ec,
                
                # 토양
                'soil_temperature': latest_data.soil_temperature,
                'soil_humidity': latest_data.soil_humidity,
                'soil_ph': latest_data.soil_ph,
                'soil_ec': latest_data.soil_ec

            }
            
            prev_data = latest_data

            return JsonResponse(response_data) # 200 OK (기본값)

        except Exception as e:
            # 서버 내부에서 예상치 못한 에러가 터졌을 때
            print(f"Server Error: {e}")
            return JsonResponse({'error': '서버 내부 오류가 발생했습니다.'}, status=500)
