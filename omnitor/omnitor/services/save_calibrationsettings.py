from omnitor.models import CalibrationSettings

def calibrate_all(calib_settings):
    """
    Weight, pH, EC 모든 보정치를 한 번에 계산하고 하나의 레코드에 저장
    """
    print(f"[save_calib 1] calib_settings: {calib_settings.__dict__}")

    if not calib_settings:
        print("[save_calib 2] No Calibration data found for calculation.")
        return

    # 저장할 데이터 딕셔너리 준비
    defaults = {}

    try:
        # 1. Weight 보정 계산
        w_slope = (calib_settings.weight_real2 - calib_settings.weight_real1) / (calib_settings.weight_filtered2 - calib_settings.weight_filtered1)
        w_intercept = calib_settings.weight_real1 - (w_slope * calib_settings.weight_filtered1)
        defaults.update({'weight_slope': w_slope, 'weight_intercept': w_intercept})

        # 2. pH 보정 계산 (온도 보정 포함)
        if not (calib_settings.ph_filtered2):
            # print("[save_calib 3] No ph_filtered2 data found.")
            defaults.update({'ph_slope': 1.0, 'ph_intercept': 0.0})
        else:
            ph_slope = (calib_settings.ph_real2 - calib_settings.ph_real1) / (calib_settings.ph_filtered2 - calib_settings.ph_filtered1)
            ph_intercept = calib_settings.ph_real1 - (ph_slope * calib_settings.ph_filtered1)
            defaults.update({'ph_slope': ph_slope, 'ph_intercept': ph_intercept})

        # 3. EC 보정 계산 (온도 보정 포함)
        if not (calib_settings.ec_filtered2):
            # print("[save_calib 4] No ec_filtered2 data found.")
            defaults.update({'ec_slope': 1.0, 'ec_intercept': 0.0})
        else:
            ec_slope = (calib_settings.ec_real2 - calib_settings.ec_real1) / (calib_settings.ec_filtered2 - calib_settings.ec_filtered1)
            ec_intercept = calib_settings.ec_real1 - (ec_slope * calib_settings.ec_filtered1)
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
