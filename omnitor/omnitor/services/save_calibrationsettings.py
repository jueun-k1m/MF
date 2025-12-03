# 여기선 보정 계산만 해주고, 실제 언제 호출하고 저장하는지는 views에서 처리함

from models import RawData, FinalData, CalibrationSettings




def calibrate_weight(weight_real1, weight_real2, weight_filtered1, weight_filtered2):

    try:
        weight_slope = (weight_real2 - weight_real1) / (weight_filtered2 - weight_filtered1)
        weight_intercept = weight_real1 - weight_slope * weight_filtered1

        CalibrationSettings.objects.update_or_create(
            id=1,
            defaults={
                'weight_slope': weight_slope,
                'weight_intercept': weight_intercept
            }
        )
    except ZeroDivisionError:
        return None, None


def calibrate_ph(ph_real1, ph_real2, ph_filtered1, ph_filtered2, temperature1, temperature2):
    """
    ph 2점 보정 함수

    ph_real1: 25도일 때 실제 EC 값1 (uS/cm)
    ph_real2: 25도일 때 실제 EC 값2 (uS/cm)

    ph_filtered1: 측정된 EC 센서 전압 값 1 (V)
    ph_filtered2: 측정된 EC 센서 전압 값 2 (V)
    temperature1: 측정된 온도 센서 값 1 (°C)
    temperature2: 측정된 온도 센서 값 2 (°C)
    """

    try:
        # ph 온도 보정
        ph_temp1 = ph_real1 - 0.017 * (temperature1 - 25)
        ph_temp2 = ph_real2 - 0.017 * (temperature2 - 25)

        # ph 2점 보정
        ph_slope = (ph_temp2 - ph_temp1) / (ph_filtered2 - ph_filtered1)
        ph_intercept = ph_real1 - ph_slope * ph_filtered1

        CalibrationSettings.objects.update_or_create(
            id=1,
            defaults={
                'ph_slope': ph_slope,
                'ph_intercept': ph_intercept
            }
        )
    except ZeroDivisionError:
        return None, None
    
    
def calibrate_ec(ec_real1, ec_real2, ec_filtered1, ec_filtered2, temperature1, temperature2):
    """
    ec 2점 보정 함수

    ec_real1: 25도일 때 실제 EC 값1 (uS/cm)
    ec_real2: 25도일 때 실제 EC 값2 (uS/cm)

    ec_filtered1: 측정된 EC 센서 전압 값 1 (V)
    ec_filtered2: 측정된 EC 센서 전압 값 2 (V)
    temperature1: 측정된 온도 센서 값 1 (°C)
    temperature2: 측정된 온도 센서 값 2 (°C)
    """

    try:
        # ec 온도 보정
        ec_temp1 = ec_real1 - 0.017 * (temperature1 - 25)
        ec_temp2 = ec_real2 - 0.017 * (temperature2 - 25)

        # ec 2점 보정
        ec_slope = (ec_temp2 - ec_temp1) / (ec_filtered2 - ec_filtered1)
        ec_intercept = ec_real1 - ec_slope * ec_filtered1

        # DB에 저장
        CalibrationSettings.objects.update_or_create(
            id=1,
            defaults={
                'ec_slope': ec_slope,
                'ec_intercept': ec_intercept
            }
        )

    except ZeroDivisionError:
        return None, None


    
