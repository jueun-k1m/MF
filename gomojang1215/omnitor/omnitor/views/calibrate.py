import json
import datetime
from omnitor.omnitor.models import CalibrationData
from omnitor.omnitor.services.filtering import avg
from omnitor.omnitor.services.save_calibrationsettings import calibrate_weight, calibrate_ph, calibrate_ec
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
            action  = data.get('action')
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        
        # ======= 무게 보정 =======

        if action == 'calibrate_weight1':
            CalibrationData.objects.create(
                timestamp = datetime.now(),
                weight_real1 = data.get('weight_real1'),
                weight_filtered1 = avg('weight')
            )
            return JsonResponse({'message': '무게1 저장 완료. 다음 무게를 입력해 주세요.'})

        elif action == 'calibrate_weight2':
            target_row = CalibrationData.objects.filter(
                weight_real1__isnull=False, 
                weight_real2__isnull=True
            ).last()

            if target_row:
                target_row.weight_real2 = data.get('weight_real2')
                target_row.weight_filtered2 = avg('weight')
                target_row.save()
                return JsonResponse({'message': '무게2 저장 완료. 보정을 진행합니다.'})
            else:
                return JsonResponse({'error': '무게1 데이터가 없습니다. 먼저 무게1을 저장해 주세요.'}, status=400)
        
        elif action == 'save_weight_calibration':
            calibrate_weight()
            return JsonResponse({'message': '무게 보정이 완료되었습니다.'})

        # ======= ph 보정 =======

        elif action == 'calibrate_ph1':
            CalibrationData.objects.create(
                ph_real1 = data.get('ph_real1'),
                ph_filtered1 = avg('ph'),
                ph_water_temperature1 = data.get('ph_water_temperature1')
            )
            return JsonResponse({'message': 'ph1 저장 완료. 다음 ph를 입력해 주세요.'})
        
        elif action == 'calibrate_ph2':
            target_row = CalibrationData.objects.filter(
                ph_real1__isnull=False, 
                ph_real2__isnull=True
            ).last()

            if target_row:
                target_row.ph_real2 = data.get('ph_real2')
                target_row.ph_filtered2 = avg('ph')
                target_row.ph_water_temperature2 = data.get('ph_water_temperature2')
                target_row.save()
                return JsonResponse({'message': 'ph2 저장 완료. 보정을 진행합니다.'})
            else:
                return JsonResponse({'error': 'ph1 데이터가 없습니다. 먼저 ph1을 저장해 주세요.'}, status=400)

        elif action == 'save_ph_calibration':
            calibrate_ph()
            return JsonResponse({'message': 'ph 보정이 완료되었습니다.'})


        # ======= ec 보정 =======

        elif action == 'calibrate_ec1':
            CalibrationData.objects.create(
                ec_real1 = data.get('ec_real1'),
                ec_filtered1 = avg('ec'),
                ec_water_temperature1 = data.get('ec_water_temperature1')
            )
            return JsonResponse({'message': 'ec1 저장 완료. 다음 ec를 입력해 주세요.'})
        
        elif action == 'calibrate_ec2':
            target_row = CalibrationData.objects.filter(
                ec_real1__isnull=False, 
                ec_real2__isnull=True
            ).last()
            if target_row:
                target_row.ec_real2 = data.get('ec_real2')
                target_row.ec_filtered2 = avg('ec')
                target_row.ec_water_temperature2 = data.get('ec_water_temperature2')
                target_row.save()
                return JsonResponse({'message': 'ec2 저장 완료. 보정을 진행합니다.'})
            else:
                return JsonResponse({'error': 'ec1 데이터가 없습니다. 먼저 ec1을 저장해 주세요.'}, status=400)
       
        elif action == 'save_ec_calibration':
            calibrate_ec()
            return JsonResponse({'message': 'ec 보정이 완료되었습니다.'})


        # ======= 전체 보정 저장 =======
        elif action == 'save_all_calibration':
            calibrate_weight()
            calibrate_ph()
            calibrate_ec()

        else:
            return JsonResponse({'error': '오류'}, status=400)
        
        return JsonResponse({'status': 'success', 'message': '보정 설정 저장 완료.'})
