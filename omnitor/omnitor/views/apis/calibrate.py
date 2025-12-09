

from filtering import avg
from django.http import JsonResponse



    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=405)

    try:
        data = json.loads(request.body)
        action  = data.get('action')
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)


    if action == 'calibrate_weight':
        

        CalibrationData.objects.create(
            weight_raw1 = weight_raw1,
            weight_filtered1 = avg(weight)
        )

    elif:
