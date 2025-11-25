from django.db import models
import datetime


# 농장 일지 모델
class FarmJournal(models.Model):
    date = models.DateField(primary_key=True)
    farm_work = models.TextField(blank=True, null=True)
    pesticide = models.TextField(blank=True, null=True)
    fertilizer = models.TextField(blank=True, null=True)
    harvest = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    camtime = models.TimeField(default=datetime.time(00, 00))

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
    co2 = models.FloatField(null=True, blank=True)
    insolation = models.FloatField(null=True, blank=True)
    
    # 배액 센서
    water_temperature = models.FloatField(null=True, blank=True)
    ph_raw = models.FloatField(null=True, blank=True)
    ec_raw = models.FloatField(null=True, blank=True)

    # 로드셀
    weight_raw = models.FloatField(null=True, blank=True)

    #티핑 게이지
    tip_count = models.FloatField(null=True, blank=True)
    
    # 토양 센서
    soil_temperature = models.FloatField(null=True, blank=True)
    soil_humidity = models.FloatField(null=True, blank=True)
    soil_ec = models.FloatField(null=True, blank=True)
    soil_ph = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"데이터: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"

class FinalData(models.Model):

    """ 최종 보정된 센서 데이터 모델 """

    timestamp = models.DateTimeField(auto_now_add=True)



    def __str__(self):
        return f"최신 센서 raw 데이터: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"


class CalibrationSettings(models.Model):
    id = models.IntegerField(primary_key=True, default=1, editable=False)

    # 무게 보정
    weight_filtered1 = models.FloatField(default=0)
    weight_filtered2 = models.FloatField(default=0)
    weight_real1 = models.FloatField(default=0)
    weight_real2 = models.FloatField(default=0)
    weight_slope = models.FloatField(default=0)
    weight_intercept = models.FloatField(default=0)
    
    # pH 보정
    ph_filtered1 = models.FloatField(default=0)
    ph_filtered2 = models.FloatField(default=7.0)
    ph_real1 = models.FloatField(default=0)
    ph_real2 = models.FloatField(default=4.0)
    ph_slope = models.FloatField(default=0)
    ph_intercept = models.FloatField(default=0)

    # EC 보정
    ec_filtered1 = models.FloatField(default=0)
    ec_filtered2 = models.FloatField(default=0)
    ec_real1 = models.FloatField(default=0)
    ec_real2 = models.FloatField(default=0)
    ec_slope = models.FloatField(default=0)
    ec_intercept = models.FloatField(default=0)

    def __str__(self):
        return "보정 설정"
    
    
