import os
import json
from datetime import datetime, date
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseNotAllowed, HttpResponse
from django.templatetags.static import static 
from models import FarmJournal

def journal_api(request):

    """
    [API] 농장 일지 내용 조회 / 입력 저장
    
    """

    # ======== GET: 날짜별 일지 & 사진 조회 ========
    if request.method == 'GET':
        # 날짜를 받고
        date_str = request.GET.get('date')

        try:
            if date_str:
                target_date = datetime.strptime(date_str, '%Y-%m-%d').date() # 문자열을 날짜 객체로 변환
            else:
                target_date = date.today() # 기본값: 오늘 날짜

            # DB 조회 (마지막 입력)
            journal = FarmJournal.objects.filter(date=target_date).last()

            if journal:
                data = {
                    'date': journal.date.strftime('%Y-%m-%d'),
                    'work': journal.work,
                    'pesticide': journal.pesticide,
                    'fertilizer': journal.fertilizer,
                    'harvest': journal.harvest,
                    'notes': journal.notes,
                    'image_dir': journal.image_dir,
                    'cam_time': journal.cam_time.strftime('%H:%M')   
                }

                # 이미지 파일 경로 설정 및 URL 생성
                journal_image_path = os.path.join('media', journal.image_dir) if journal.image_dir else None
                if journal_image_path and os.path.exists(journal_image_path):
                    image_urls = []
                    for img_file in os.listdir(journal_image_path):
                        if img_file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                            image_urls.append(static(os.path.join(journal.image_dir, img_file)))
                    data['images'] = image_urls

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
            return HttpResponseBadRequest("날짜 오류: 올바른 형식은 YYYY-MM-DD 입니다.")


    # ====== POST: 농장 일지 저장 =========
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            date_str = data.get('date')

            if not date_str:
                return HttpResponseBadRequest("날짜를 선택해 주세요.")
            
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()

            journal = FarmJournal.objects.update_or_create(
                date=target_date,
                defaults={
                    'work': data.get('work', ''),
                    'pesticide': data.get('pesticide', ''),
                    'fertilizer': data.get('fertilizer', ''),
                    'harvest': data.get('harvest', ''),
                    'notes': data.get('notes', '')
                }
            )

            return JsonResponse({'status': 'success', 'message': '일지가 저장되었습니다.'})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    else:
        return HttpResponseNotAllowed(['GET', 'POST'])
