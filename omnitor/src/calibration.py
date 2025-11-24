from omnitor.models import SensorData, SensorCalibration, CalibrationSettings, CalibratedData

weight_raw = SensorCalibration.weight_raw
ph_raw = SensorCalibration.ph_raw
ec_raw = SensorCalibration.ec_raw

water_temperature = SensorCalibration.water_temperature

def calibrate_weight(weight_raw):

    """ 무게 보정 함수 """

    settings = CalibrationSettings.objects.first()
    if not settings:
        return weight_raw  # 보정 설정이 없으면 원래 값 반환

    # 2점 보정 계산
    slope = (settings.weight_point2_value - settings.weight_point1_value) / (settings.weight_point2_raw - settings.weight_point1_raw)
    intercept = settings.weight_point1_value - slope * settings.weight_point1_raw
    calibrated_value = slope * weight_raw + intercept
    

    CalibratedData.objects.update_or_create(
        weight_calibrated=calibrate_weight(weight_raw),
    )
    
    CalibrationSettings.objects.filter(id=settings.id).update(
        weight_slope=slope,
        weight_intercept=intercept
    )   

def calibrate_ph(voltage, water_temperature):

    """ pH 보정 함수 """

    settings = CalibrationSettings.objects.first()
    if not settings:
        return voltage  # 보정 설정이 없으면 원래 값 반환


    # ph 온도 보정 적용
    ph1_temp = settings.ph_point1_value - 0.017(water_temperature - 25)
    ph2_temp = settings.ph_point2_value - 0.017(water_temperature - 25)

    # 선형 보정 계산
    slope = (ph2_temp - ph1_temp) / (settings.ph_point2_voltage - settings.ph_point1_voltage)
    intercept = ph1_temp - slope * settings.ph_point1_voltage
    calibrated_value = slope * voltage + intercept

    CalibratedData.objects.update_or_create(
        ph_calibrated=calibrate_ph(voltage, water_temperature),
    )  
    CalibrationSettings.objects.filter(id=settings.id).update(  
        ph_slope=slope,
        ph_intercept=intercept
    )

def calibrate_ec(voltage, water_temperature):

    """ EC 보정 함수 """

    settings = CalibrationSettings.objects.first()
    if not settings:
        return voltage  # 보정 설정이 없으면 원래 값 반환


    # EC 온도 보정 적용 (25도 기준)
    ec1_temp = settings.ec_point1_value*(1 + 0.02 * (water_temperature - 25))
    ec2_temp = settings.ec_point2_value*(1 + 0.02 * (water_temperature - 25))

    # 선형 보정 계산
    slope = (ec2_temp - ec1_temp) / (settings.ec_point2_voltage - settings.ec_point1_voltage)
    intercept = settings.ec_point1_value - slope * settings.ec_point1_voltage
    calibrated_value = slope * voltage + intercept
    
    CalibratedData.objects.update_or_create(
        ec_calibrated=calibrate_ec(voltage, water_temperature),
    )

    CalibrationSettings.objects.filter(id=settings.id).update(  
        ec_slope=slope,
    )


def main():

    weight_raw = SensorCalibration.weight_raw
    ph_raw = SensorCalibration.ph_raw
    ec_raw = SensorCalibration.ec_raw
    
    calibrate_weight(weight_raw)
    calibrate_ph(ph_raw, water_temperature)
    calibrate_ec(ec_raw, water_temperature)

if __name__ == "__main__":
    main()
