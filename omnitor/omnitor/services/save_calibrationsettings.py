from omnitor.models import CalibrationData, CalibrationSettings

def calibrate_all(calib_data):
    """
    Weight, pH, EC 모든 보정치를 한 번에 계산하고 하나의 레코드에 저장
    """
    print(f"[save_calib 1] calib_data: {calib_data.__dict__}")

    if not calib_data:
        print("[save_calib 2] No CalibrationData found for calculation.")
        return

    # 저장할 데이터 딕셔너리 준비
    defaults = {}

    try:
        # 1. Weight 보정 계산
        if calib_data.weight_filtered2 != calib_data.weight_filtered1:
            w_slope = (calib_data.weight_real2 - calib_data.weight_real1) / (calib_data.weight_filtered2 - calib_data.weight_filtered1)
            w_intercept = calib_data.weight_real1 - (w_slope * calib_data.weight_filtered1)
            defaults.update({'weight_slope': w_slope, 'weight_intercept': w_intercept})

        # 2. pH 보정 계산 (온도 보정 포함)
        if calib_data.ph_filtered2 != calib_data.ph_filtered1:
            ph_slope = (calib_data.ph_real2 - calib_data.ph_real1) / (calib_data.ph_filtered2 - calib_data.ph_filtered1)
            ph_intercept = calib_data.ph_real1 - (ph_slope * calib_data.ph_filtered1)
            defaults.update({'ph_slope': ph_slope, 'ph_intercept': ph_intercept})

        # 3. EC 보정 계산 (온도 보정 포함)
        if calib_data.ec_filtered2 != calib_data.ec_filtered1:
            ec_slope = (calib_data.ec_real2 - calib_data.ec_real1) / (calib_data.ec_filtered2 - calib_data.ec_filtered1)
            ec_intercept = calib_data.ec_real1 - (ec_slope * calib_data.ec_filtered1)
            defaults.update({'ec_slope': ec_slope, 'ec_intercept': ec_intercept})

        # DB 저장 (ID=1인 단일 설정 레코드 업데이트 혹은 생성)
        if defaults:
            obj, created = CalibrationSettings.objects.update_or_create(
                id=1, 
                defaults=defaults
            )
            print(f"[SaveCalSet] All settings saved. Created: {created}")
            print(f"DEBUG DATA: {defaults}")
        else:
            print("[SaveCalSet] No data calculated. Check if filtered values are identical.")

    except ZeroDivisionError as e:
        print(f"[Error] ZeroDivisionError: {e}")
