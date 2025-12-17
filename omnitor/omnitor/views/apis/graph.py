# gemini

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

        end_time = timezone.now()
        start_time = end_time - timedelta(hours=1) # 디폴트: 1시간


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
                 'total_weight', 'irrigation', 'total_irrigation', 'total_drainage',
                 'water_temperature', 'ph', 'ec', 
                 'soil_temperature', 'soil_humidity', 'soil_ec', 'soil_ph')

        data_list = list(data)

        if not data_list:
            return JsonResponse({'error': '데이터 (리스트) 없음'}, status=404)
        

        # ======= 시간 단위 설정 (pandas 사용) =======
        # pandas 시간 단위 freq로 주기 설정
        try:
            data_pandas = pd.DataFrame(data_list) # pandas에서 데이터프레임 만들기
            data_pandas['timestamp'] = pd.to_datetime(data_pandas['timestamp'])

            # 시간 단위 설정
            freq = None
            if time_unit == '1m' : freq = '1min'
            elif time_unit == '10m': freq = '10min'
            elif time_unit == '30m' : freq = '30min'
            elif time_unit == '1h': freq = '1h'
            elif time_unit == '3h': freq = '3h'

            if freq:
                target_times = pd.date_range(start=start_time, end=end_time, freq=freq)
                tolerance_limit = pd.Timedelta(freq)/2

                dp_selected = data_pandas.reindex(target_times, method='nearest', tolerance=tolerance_limit)
                
                # 매칭되는 데이터가 없어서 빈 값이 된 행은 제거
                dp_selected.dropna(inplace=True)

            else:
                # 단위 선택 안 했으면 원본 그대로
                dp_selected = data_pandas

            # 사용자가 csv로 export 하고 싶다면
            if fmt == 'csv':
                response = HttpResponse(content_type='text/csv')
                response['Content-Disposition'] = 'attachment; filename="sensor_data.csv"'
                dp_selected.to_csv(path_or_buf=response, encoding='utf-8-sig', float_format='%.2f', index_label='Time')
                return response
            else:
                dp_selected.reset_index(inplace=True)
                dp_selected.rename(columns={'index': 'timestamp'}, inplace=True)
                result_data = dp_selected.to_dict('records')
                return JsonResponse({'data': result_data}, safe=False)

        except Exception as e:
            print(f"Error: {e}")
            return JsonResponse({'error': str(e)}, status=500)
