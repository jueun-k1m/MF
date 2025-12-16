# gemini

import json
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from datetime import datetime
from omnitor.omnitor.models import FarmJournal

def camera_time_api(request):
    
    # === GET 요청: 설정된 시간 조회 ===
    if request.method == 'GET':
        journal = FarmJournal.objects.last() # [중요] 인스턴스 가져오기
        
        if not journal:
            return JsonResponse({'capture_time': None, 'message': '설정된 데이터가 없습니다.'})
            
        return JsonResponse({'status': 'success', 'capture_time': journal.cam_time})

    # === POST 요청: 시간 설정 업데이트 ===
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            new_time_str = data.get('capture_time') 
            
            if not new_time_str:
                return HttpResponseBadRequest("시간을 설정해 주세요.") # 400 Bad Request

            # 시간 형식 검증
            valid_time = datetime.strptime(new_time_str, '%H:%M').time()

            # DB 업데이트
            journal = FarmJournal.objects.last()
            
            # 만약 DB가 비어있다면 새로 생성
            if not journal:
                journal = FarmJournal() 
            
            # 인스턴스에 값 할당 후 저장
            journal.cam_time = valid_time
            journal.save()
            
            print(f"카메라 시간이 새로 설정 되었습니다: {new_time_str}")
            return JsonResponse({'status': 'success', 'message': f'설정 완료: {new_time_str}'})

        except ValueError:
            return HttpResponseBadRequest("시간 범위 오류: (HH:MM).")
        except json.JSONDecodeError:
            return HttpResponseBadRequest("JSON 포멧 오류.")
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    else:
        return HttpResponseBadRequest("메서드 오류") 
