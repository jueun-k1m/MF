from django.db import models
import datetime


# 농장 일지 모델
class FarmJournal(models.Model):
    date = models.DateField(primary_key=True)
    work = models.TextField(blank=True, null=True)
    pesticide = models.TextField(blank=True, null=True)
    fertilizer = models.TextField(blank=True, null=True)
    harvest = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    cam_time = models.TimeField(default=datetime.time(00, 00))
    image_dir = models.TextField(default="/static/journal_images/")

    def __str__(self):
        return f"농장 일지: {self.date}"


# 센서 raw 데이터 모델 (아두이노 & 토양 포함)
class RawData(models.Model):

    """ 센서 raw 데이터 모델 (아두이노 & 토양 포함)
        타임스탬프, 온도, 습도, CO2, 일사량, 수온, 무게(raw), pH(raw), EC(raw), 티핑게이지 카운트 """

    timestamp = models.DateTimeField(auto_now_add=True)
    
    # 환경 센서
    air_temperature = models.FloatField(null=True, blank=True)
    air_humidity = models.FloatField(null=True, blank=True)
    co2 = models.IntegerField(null=True, blank=True)
    insolation = models.FloatField(null=True, blank=True)
    
    # 배액 센서
    water_temperature = models.BigIntegerField(null=True, blank=True)
    ph = models.FloatField(null=True, blank=True)
    ec = models.FloatField(null=True, blank=True)

    # 로드셀
    weight = models.FloatField(null=True, blank=True)

    #티핑 게이지
    tip_count = models.IntegerField(null=True, blank=True)
    
    # 토양 센서
    soil_temperature = models.FloatField(null=True, blank=True)
    soil_humidity = models.FloatField(null=True, blank=True)
    soil_ec = models.FloatField(null=True, blank=True)
    soil_ph = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"Raw 데이터: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"

class FinalData(models.Model):

    """ 최종 보정된 센서 데이터 모델 """

    timestamp = models.DateTimeField(auto_now_add=True)
    
    # 환경
    air_temperature = models.FloatField(null=True, blank=True)
    air_humidity = models.FloatField(null=True, blank=True)
    vpd = models.FloatField(null=True, blank=True)

    co2 = models.FloatField(null=True, blank=True)
    insolation = models.FloatField(null=True, blank=True)
    total_insolation = models.FloatField(null=True, blank=True)

    # 배액
    water_temperature = models.FloatField(null=True, blank=True)
    ph = models.FloatField(null=True, blank=True)
    ec = models.FloatField(null=True, blank=True)

    # 함수량
    total_weight  = models.FloatField(null=True, blank=True)
    irrigation = models.FloatField(null=True, blank=True)
    total_irrigation = models.FloatField(null=True, blank=True)
    total_drainage = models.IntegerField(null=True, blank=True)
    
    # 토양 센서
    soil_temperature = models.FloatField(null=True, blank=True)
    soil_humidity = models.FloatField(null=True, blank=True)
    soil_ec = models.FloatField(null=True, blank=True)
    soil_ph = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"Final 데이터: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"


class CalibrationSettings(models.Model):

    """
    무게, ph, ec 보정 설정 (slope, intercept)
    y = mx + b 식으로 보정 설정 적용
    """

    # 무게 보정
    weight_slope = models.FloatField(default=0)
    weight_intercept = models.FloatField(default=0)
    
    # pH 보정
    ph_slope = models.FloatField(default=0)
    ph_intercept = models.FloatField(default=0)

    # EC 보정
    ec_slope = models.FloatField(default=0)
    ec_intercept = models.FloatField(default=0)

    def save(self, *args, **kwargs):
        # This forces the ID to always be 1
        self.id = 1
        super(CalibrationSettings, self).save(*args, **kwargs)

    @classmethod
    def load(cls):
        # Helper method to always get the first row or create it if missing
        obj, created = cls.objects.get_or_create(id=1)
        return obj

    def __str__(self):
        return "Calibration Settings (ID: 1)"
    
    
class CalibrationData(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)

    weight_real1 = models.FloatField(default=0, null=True, blank=True)
    weight_real2 = models.FloatField(default=0, null=True, blank=True)
    weight_filtered1 = models.FloatField(default=0, null=True, blank=True)
    weight_filtered2 = models.FloatField(default=0, null=True, blank=True)

    ph_real1 = models.FloatField(default=0, null=True, blank=True)
    ph_real2 = models.FloatField(default=0, null=True, blank=True)
    ph_filtered1 = models.FloatField(default=0, null=True, blank=True)
    ph_filtered2 = models.FloatField(default=0, null=True, blank=True)
    ph_water_temperature1 = models.FloatField(default=25, null=True, blank=True)
    ph_water_temperature2 = models.FloatField(default=25, null=True, blank=True)

    ec_real1 = models.FloatField(default=0, null=True, blank=True)
    ec_real2 = models.FloatField(default=0, null=True, blank=True)
    ec_filtered1 = models.FloatField(default=0, null=True, blank=True)
    ec_filtered2 = models.FloatField(default=0, null=True, blank=True)

    # 특히 이 부분들!
    ec_water_temperature1 = models.FloatField(default=25, null=True, blank=True)
    ec_water_temperature2 = models.FloatField(default=25, null=True, blank=True)
