import json
import datetime
from omnitor.models import CalibrationData, RawData
from omnitor.services.save_calibrationsettings import calibrate_all
from omnitor.services.filtering import avg
from django.http import JsonResponse, HttpResponseBadRequest

def calibrate_api(request):

    """
    [API] 센서 보정 설정 저장
    무게 / ph / ec 각각 DB 다음 행에 보정 데이터 저장 및 보정 설정 저장
    :param request: Description
    """

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            action = data.get('action')
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        obj = CalibrationData.objects.last()
        raw = RawData.objects.last()
        if not obj:
            obj = CalibrationData.objects.create()

        # ======= WEIGHT =======
        if action == 'calibrate_weight1':
            obj.weight_real1 = data.get('weight_real1')
            obj.weight_filtered1 = avg('weight')
            obj.save()
            return JsonResponse({'message': '무게1 저장 완료'})

        elif action == 'calibrate_weight2':
            obj.weight_real2 = data.get('weight_real2')
            obj.weight_filtered2 = avg('weight')
            obj.save()
            return JsonResponse({'message': '무게2 저장 완료'})

        # ======= pH (Fixed temperature field mapping) =======
        elif action == 'calibrate_ph1':
            obj.ph_real1 = data.get('ph_real1')
            obj.ph_filtered1 = avg('water_ph')
            obj.save()
            return JsonResponse({'message': 'ph1 저장 완료'})

        elif action == 'calibrate_ph2':
            obj.ph_real2 = data.get('ph_real2')
            obj.ph_filtered2 = avg('water_ph')
            obj.save()
            return JsonResponse({'message': 'ph2 저장 완료'})

        # ======= EC (Fixed temperature field mapping) =======
        elif action == 'calibrate_ec1':
            obj.ec_real1 = data.get('ec_real1')
            obj.ec_filtered1 = avg('water_ec')
            obj.save()
            return JsonResponse({'message': 'ec1 저장 완료'})

        elif action == 'calibrate_ec2':
            obj.ec_real2 = data.get('ec_real2')
            obj.ec_filtered2 = avg('water_ec')
            obj.save()
            return JsonResponse({'message': 'ec2 저장 완료'})

        # ======= FINAL APPLY ACTIONS =======
        elif action == 'save_weight_calibration':
            calibrate_all(obj)
            return JsonResponse({'message': '무게 보정이 적용되었습니다.'})
        
        elif action == 'save_ph_calibration':
            calibrate_all(obj)
            return JsonResponse({'message': 'pH 보정이 적용되었습니다.'})

        elif action == 'save_ec_calibration':
            calibrate_all(obj)
            return JsonResponse({'message': 'EC 보정이 적용되었습니다.'})

        return JsonResponse({'error': 'Invalid Action'}, status=400)
