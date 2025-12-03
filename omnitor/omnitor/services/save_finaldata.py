from models import CalibrationSettings, FinalData

def calc_and_save_final_data(filtered_data):
    """
    필터링 된 데이터에 보정 설정을 적용하여 FInalData DB에 최종 데이터를 저장
    """

    if not filtered_data:
        return None
    
    settings = CalibrationSettings.load()
    
