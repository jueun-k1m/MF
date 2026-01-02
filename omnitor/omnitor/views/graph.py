import pandas as pd
from datetime import timedelta
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from omnitor.models import FinalData

def graph_api(request):
    if request.method == 'GET':

        # 시작 날짜, 끝 날짜, 시간 범위, 시간 단위, format (csv or not) 받기
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')
        time_range = request.GET.get('time_range')
        time_unit = request.GET.get('time_unit')
        fmt = request.GET.get('format')

        # ======= 시간 단위 유효성 검사 =======
        if time_range and time_unit:
            # 단위를 비교하기 위해 분(minute) 단위 숫자로 매핑
            unit_map = {
                '10m': 10, '1h': 60, '1d': 1440, '7d': 10080, # Range용
                '1m': 1, '30m': 30, '3h': 180                 # Unit용 공통 포함
            }
            
            # 입력된 값을 숫자로 변환
            range_val = unit_map.get(time_range)
            unit_val = unit_map.get(time_unit)

            if range_val and unit_val:
                if unit_val > range_val:
                    return JsonResponse({
                        'error': '잘못된 요청입니다: 시간 단위(time_unit)가 전체 범위(time_range)보다 클 수 없습니다.'
                    }, status=400)

        end_time = timezone.now()
        start_time = end_time - timedelta(minutes=10) # 디폴트: 1시간


        # ======= 시간 범위 설정 =======
        try:
            # 시간 범위 직접 선택  
            if start_date_str and end_date_str:
                start_time = parse_datetime(start_date_str)
                end_time = parse_datetime(end_date_str)

            # 시간 범위 4가지 선택 중 하나
            elif time_range:
                if time_range == '10m': start_time = end_time - timedelta(minutes=10)
                elif time_range == '1h': start_time = end_time - timedelta(hours=1)
                elif time_range == '1d': start_time = end_time - timedelta(days=1)
                elif time_range == '7d': start_time = end_time - timedelta(days=7)
        except (ValueError, TypeError):
            return JsonResponse({'error': '파라미터 오류'}, status=400)
        
        # DB에서 시간 범위 안에 있는 데이터 가져오기
        data = FinalData.objects.filter(
            timestamp__range=(start_time, end_time)
        ).values('timestamp', 'air_temperature', 'air_humidity', 'co2', 'insolation', 'total_insolation', 'vpd', 
                 'weight', 'irrigation', 'total_irrigation', 'total_drainage',
                 'water_temperature', 'water_ph', 'water_ec', 
                 'soil_temperature', 'soil_humidity', 'soil_ec', 'soil_ph')

        data_list = list(data)

        if not data_list:
            return JsonResponse({'error': '데이터 (리스트) 없음'}, status=404)
        

        # ======= 시간 단위 설정 (pandas 사용) =======
        # pandas 시간 단위 freq로 주기 설정
        # ======= 시간 단위 설정 (pandas 사용) =======
        try:
            data_pandas = pd.DataFrame(data_list)
            data_pandas['timestamp'] = pd.to_datetime(data_pandas['timestamp'])

            # reindex를 하기 위해 timestamp를 인덱스로 설정합니다.
            data_pandas.set_index('timestamp', inplace=True) 

            unit_to_freq = {
                '1m': '1min',
                '10m': '10min',
                '30m': '30min',
                '1h': '1h',
                '3h': '3h',
                '1d': '1D'
            }
            
            freq = unit_to_freq.get(time_unit)

            if freq:
                target_times = pd.date_range(start=start_time, end=end_time, freq=freq)
                tolerance_limit = pd.Timedelta(freq)/2

                # 이제 인덱스가 시간 타입이므로 에러 없이 작동합니다.
                dp_selected = data_pandas.reindex(target_times, method='nearest', tolerance=tolerance_limit)
                dp_selected.dropna(inplace=True)
            else:
                dp_selected = data_pandas

            # ======= 결과 반환 로직 (이전 답변에서 드린 중복 해결 코드) =======
            dp_selected.reset_index(inplace=True)
            dp_selected.rename(columns={'index': 'timestamp'}, inplace=True)
            
            # 만약 reindex를 안 거쳐서 timestamp 컬럼이 두 개가 된 경우를 대비해 하나 제거
            if dp_selected.columns.duplicated().any():
                dp_selected = dp_selected.loc[:, ~dp_selected.columns.duplicated()]

            result_data = dp_selected.to_dict('records')
            return JsonResponse({'data': result_data}, safe=False)

        except Exception as e:
            print(f"Error: {e}")
            return JsonResponse({'error': str(e)}, status=500)
