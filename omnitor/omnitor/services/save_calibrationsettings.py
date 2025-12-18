# 여기선 보정 계산만 해주고, 실제 언제 호출하고 저장하는지는 views에서 처리함

from omnitor.models import CalibrationData, CalibrationSettings

def calibrate_weight():

    """
    weight 2점 보정 함수
    weight_real1: 실제 무게 값1 (g)
    weight_real2: 실제 무게 값2 (g)
    weight_filtered1: 측정된 무게 센서 값 1 (g)
    weight_filtered2: 측정된 무게 센서 값 2 (g)
    """

    calib_data = CalibrationData.objects.last()

    if not calib_data:
        print("[1] No CalibrationData")
        return

    try:
        # m = (y2 - y1) / (x2 - x1)
        weight_slope = (calib_data.weight_real2 - calib_data.weight_real1) / (calib_data.weight_filtered2 - calib_data.weight_filtered1)
        # b = y1 - m*x1
        weight_intercept = calib_data.weight_real1 - (weight_slope * calib_data.weight_filtered1)

        print("[2] Calibration calculation complete")

        CalibrationSettings.objects.update_or_create(
            weight_slope= weight_slope,
            weight_intercept=weight_intercept
        )
        
        print ("[3] CalibrationSettings saved")
    except ZeroDivisionError:
        return None, None


def calibrate_ph():

    """
    ph 2점 보정 함수

    ph_real1: 25도일 때 실제 EC 값1 (uS/cm)
    ph_real2: 25도일 때 실제 EC 값2 (uS/cm)

    ph_filtered1: 측정된 EC 센서 전압 값 1 (V)
    ph_filtered2: 측정된 EC 센서 전압 값 2 (V)

    temperature1: 측정된 온도 센서 값 1 (°C)
    temperature2: 측정된 온도 센서 값 2 (°C)
    """

    calib_data = CalibrationData.objects.last()
    if not calib_data:
        print("[4] No CalibrationData")
        return

    try:
        # ph 온도 보정
        ph_temp1 = calib_data.ph_real1 - 0.017 * (calib_data.ph_water_temperature1 - 25)
        ph_temp2 = calib_data.ph_real2 - 0.017 * (calib_data.ph_water_temperature2 - 25)

        # ph 2점 보정
        ph_slope = (ph_temp2 - ph_temp1) / (calib_data.ph_filtered2 - calib_data.ph_filtered1)
        ph_intercept = ph_temp1 - (ph_slope * calib_data.ph_filtered1)
        print("[5] Calibration calculation complete")

        CalibrationSettings.objects.update_or_create(
            ph_slope=ph_slope,
            ph_intercept=ph_intercept
        )
        print ("[6] CalibrationSettings saved")

    except ZeroDivisionError:
        return None, None
    
    
def calibrate_ec():

    """
    ec 2점 보정 함수

    ec_real1: 25도일 때 실제 EC 값1 (uS/cm)
    ec_real2: 25도일 때 실제 EC 값2 (uS/cm)

    ec_filtered1: 측정된 EC 센서 전압 값 1 (V)
    ec_filtered2: 측정된 EC 센서 전압 값 2 (V)
    temperature1: 측정된 온도 센서 값 1 (°C)
    temperature2: 측정된 온도 센서 값 2 (°C)
    """

    calib_data = CalibrationData.objects.last()
    if not calib_data:
        print("[7] No CalibrationData")
        return

    try:
        # ec 온도 보정
        ec_temp1 = calib_data.ec_real1 - 0.017 * (calib_data.ec_water_temperature1 - 25)
        ec_temp2 = calib_data.ec_real2 - 0.017 * (calib_data.ec_water_temperature2 - 25)

        # ec 2점 보정
        ec_slope = (ec_temp2 - ec_temp1) / (calib_data.ec_filtered2 - calib_data.ec_filtered1)
        ec_intercept = ec_temp1 - (ec_slope * calib_data.ec_filtered1)
        print("[8] Calibration calculation complete")
        # DB에 저장
        CalibrationSettings.objects.update_or_create(
            ec_slope=ec_slope,
            ec_intercept=ec_intercept
        )
        print ("[9] CalibrationSettings saved")

    except ZeroDivisionError:
        return None, None

