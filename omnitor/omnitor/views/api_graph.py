import pandas as pd
import json
from datetime import timedelta, datetime, time
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime
from omnitor.models import FinalData

def graph_api(request):
    if request.method == 'GET':
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')
        time_range = request.GET.get('time_range')
        time_unit = request.GET.get('time_unit')
        fmt = request.GET.get('format')

        unit_map = {
            '10m': 10, '1h': 60, '1d': 1440, '7d': 10080, 
            '1m': 1, '30m': 30, '3h': 180, '6h': 360      
        }
        
        range_val = unit_map.get(time_range)
        unit_val = unit_map.get(time_unit)

        if range_val and unit_val and unit_val > range_val:
            return JsonResponse({'error': f'단위({time_unit})가 범위({time_range})보다 큽니다.'}, status=400)

        # 기본 시간 설정 (현재 시간 기준)
        end_time = timezone.now()
        start_time = end_time - timedelta(minutes=10)

        try:
            # 사용자가 날짜를 직접 선택한 경우
            if start_date_str and end_date_str:
                
                # 시간 날짜 둘 다 포함 - parse_datetime 사용
                start_dt = parse_datetime(start_date_str)
                end_dt = parse_datetime(end_date_str)


                # 시간 없고 날짜만 - parse_date 사용
                if start_dt is None:
                    start_date = parse_date(start_date_str)
                    if start_date:
                        start_dt = datetime.combine(start_date, time.min)
                
                if end_dt is None:
                    end_date = parse_date(end_date_str)
                    if end_date:
                        end_dt = datetime.combine(end_date, time.max)
                
                # 파싱 실패 (None) 에러 처리
                if start_dt is None or end_dt is None:
                     return JsonResponse({'error': '날짜 형식이 올바르지 않습니다.'}, status=400)
                
                # Timezone 적용
                if timezone.is_naive(start_dt):
                    start_time = timezone.make_aware(start_dt)
                else:
                    start_time = start_dt

                if timezone.is_naive(end_dt):
                    end_time = timezone.make_aware(end_dt)
                else:
                    end_time = end_dt

            # 선택 버튼을 사용한 경우
            elif time_range:
                if time_range == '10m': start_time = end_time - timedelta(minutes=10)
                elif time_range == '1h': start_time = end_time - timedelta(hours=1)
                elif time_range == '1d': start_time = end_time - timedelta(days=1)
                elif time_range == '7d': start_time = end_time - timedelta(days=7)
        
        except Exception as e:
            # 날짜 형식이 잘못되었거나 파싱 실패 시
            print(f"Date Parsing Error: {e}")
            return JsonResponse({'error': '날짜 형식이 올바르지 않습니다.'}, status=400)

        # DB 조회
        data = FinalData.objects.filter(
            timestamp__range=(start_time, end_time)
        ).values(
            'timestamp', 
            'air_temperature', 'air_humidity', 'co2', 'insolation', 'vpd',
            'weight', 'irrigation', 'total_drainage',
            'water_temperature', 'water_ph', 'water_ec',
            'soil_temperature', 'soil_humidity', 'soil_ec', 'soil_ph',
            'total_insolation', 'total_irrigation'
        ).order_by('timestamp')

        data_list = list(data)
        if not data_list:
            return JsonResponse({'error': '해당 기간에 데이터가 없습니다.'}, status=404)

        try:
            # DataFrame 생성
            df = pd.DataFrame(data_list)
            df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
            df.set_index('timestamp', inplace=True)

            unit_to_freq = {
                '1m': '1min', '10m': '10min', '30m': '30min',
                '1h': '1H', '3h': '3H', '6h': '6H', '1d': '1D'
            }
            freq = unit_to_freq.get(time_unit)
            
            if freq:
                target_times = pd.date_range(start=start_time, end=end_time, freq=freq)

                # target_times 의 Timezone을 df와 동일하게 맞춤 (최근 범위랑 직접 선택 범위)
                if target_times.tz is None:
                    target_times = target_times.tz_localize('UTC')
                else:
                    target_times = target_times.tz_convert('UTC')


                tolerance_limit = pd.Timedelta(freq) / 2
                df_resampled = df.reindex(target_times, method='nearest', tolerance=tolerance_limit)
                df_resampled.dropna(how='all', inplace=True)
            else:
                df_resampled = df 

            df_resampled.reset_index(inplace=True)
            df_resampled.rename(columns={'index': 'timestamp'}, inplace=True)
            
            if df_resampled.columns.duplicated().any():
                df_resampled = df_resampled.loc[:, ~df_resampled.columns.duplicated()]

            if fmt == 'excel':
                response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                filename = f"sensor_data_{start_time.strftime('%Y%m%d')}_{end_time.strftime('%Y%m%d')}.xlsx" # 파일명 포맷도 날짜 위주로 살짝 변경 추천
                response['Content-Disposition'] = f'attachment; filename={filename}'
                
                df_excel = df_resampled.copy()
                if 'timestamp' in df_excel.columns:
                    df_excel['timestamp'] = df_excel['timestamp'].apply(lambda x: x.strftime('%Y-%m-%d %H:%M:%S') if pd.notnull(x) else x)

                df_excel.to_excel(response, index=False, engine='openpyxl')
                return response

            result_json_str = df_resampled.to_json(orient='records', date_format='iso')
            result_data = json.loads(result_json_str)

            summary_data = {}
            if not df_resampled.empty:
                last_row = df_resampled.iloc[-1]
                def get_safe_value(row, key):
                    val = row.get(key)
                    if pd.notnull(val) and hasattr(val, 'item'):
                        return val.item()
                    return val if pd.notnull(val) else 0

                summary_data = {
                    'total_insolation': get_safe_value(last_row, 'total_insolation'),
                    'total_irrigation': get_safe_value(last_row, 'total_irrigation'),
                    'total_drainage': get_safe_value(last_row, 'total_drainage')
                }
            else:
                 summary_data = {'total_insolation': 0, 'total_irrigation': 0, 'total_drainage': 0}

            return JsonResponse({
                'data': result_data,
                'summary': summary_data
            }, safe=False)

        except Exception as e:
            print(f"Graph API Error: {e}")
            import traceback
            print(traceback.format_exc())
            return JsonResponse({'error': str(e)}, status=500)
