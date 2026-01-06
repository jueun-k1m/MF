import json
import os
import glob
from datetime import datetime, date
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseNotAllowed
from django.conf import settings
from omnitor.models import FarmJournal

def journal_api(request):
    if request.method == 'GET':
        date_str = request.GET.get('date')

        try:
            if date_str:
                target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            else:
                target_date = date.today()

            journal = FarmJournal.objects.filter(date=target_date).first()

            data = {
                'date': target_date.strftime('%Y-%m-%d'),
                'work': journal.work if journal else '',
                'pesticide': journal.pesticide if journal else '',
                'fertilizer': journal.fertilizer if journal else '',
                'harvest': journal.harvest if journal else '',
                'notes': journal.notes if journal else '',
                'cam_time': '09:00'
            }

            if journal and journal.cam_time:
                data['cam_time'] = journal.cam_time.strftime('%H:%M')

            image_folder = os.path.join(settings.MEDIA_ROOT, 'journal_images')
            search_pattern = os.path.join(image_folder, f"{date_str}_*.jpg")
            
            files = glob.glob(search_pattern)

            if files:
                files.sort() 
                latest_file = files[-1]
                filename = os.path.basename(latest_file)

                media_url = settings.MEDIA_URL
                if not media_url.startswith('/'):
                    media_url = '/' + media_url
                
                data['image_dir'] = f"{media_url}journal_images/{filename}"

            return JsonResponse({'status': 'success', 'exists': bool(journal), 'data': data})

        except ValueError:
            return HttpResponseBadRequest("Invalid date format")


    # ===== POST =====
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            date_str = data.get('date')
            if not date_str: return HttpResponseBadRequest("Date required")
            
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()

            update_values = {}
            if 'work' in data: update_values['work'] = data['work']
            if 'pesticide' in data: update_values['pesticide'] = data['pesticide']
            if 'fertilizer' in data: update_values['fertilizer'] = data['fertilizer']
            if 'harvest' in data: update_values['harvest'] = data['harvest']
            if 'notes' in data: update_values['notes'] = data['notes']
            
            if 'cam_time' in data and data['cam_time']:
                update_values['cam_time'] = data['cam_time']
                print(f"Setting cam_time to {data['cam_time']}")

            FarmJournal.objects.update_or_create(
                date=target_date,
                defaults=update_values
            )

            return JsonResponse({'status': 'success', 'message': 'Saved'})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    else:
        return HttpResponseNotAllowed(['GET', 'POST'])
