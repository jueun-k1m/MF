import json
from datetime import datetime, date
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseNotAllowed, HttpResponse
from django.templatetags.static import static 
from omnitor.models import FarmJournal


def journal_api(request):
    """
    [API] 농장 일지 내용 조회 / 입력 저장
    
    """

    # ===== GET: 날짜별 일지 & 사진 조회 ========
    if request.method == 'GET':
        date_str = request.GET.get('date')

        try:
            if date_str:
                target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            else:
                target_date = date.today()

            # DB 조회
            journal = FarmJournal.objects.filter(date=target_date).first()

            if journal:
                # 기본 응답 구조
                data = {
                    'date': journal.date.strftime('%Y-%m-%d'),
                    'work': journal.work,
                    'pesticide': journal.pesticide,
                    'fertilizer': journal.fertilizer,
                    'harvest': journal.harvest,
                    'notes': journal.notes,
                    'image_dir': None,   
                    'cam_time': None   
                }

                # 이미지 경로 처리
                if journal.image_dir:
                    data['image_dir'] = journal.image_dir

                # 촬영 시간 처리
                if journal.cam_time:
                    data['cam_time'] = journal.cam_time.strftime('%H:%M')

                return JsonResponse({
                    'status': 'success',
                    'exists': True,
                    'data': data
                })

            else:
                return JsonResponse({
                    'status': 'success',
                    'exists': False,
                    'message': '해당 날짜의 데이터가 없습니다.',
                    'data': {}
                })

        except ValueError:
            return HttpResponseBadRequest("Invalid date format (YYYY-MM-DD)")


    # ====== POST: 농장 일지 저장 =========
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            date_str = data.get('date')

            if not date_str:
                return HttpResponseBadRequest("Date is required.")
            
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()

            journal, created = FarmJournal.objects.update_or_create(
                date=target_date,
                defaults={
                    'work': data.get('work', ''),
                    'pesticide': data.get('pesticide', ''),
                    'fertilizer': data.get('fertilizer', ''),
                    'harvest': data.get('harvest', ''),
                    'notes': data.get('notes', '')
                }
            )

            return JsonResponse({'status': 'success', 'message': 'Saved successfully'})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    else:
        return HttpResponseNotAllowed(['GET', 'POST'])
