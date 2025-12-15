import schedule

def add_time_interval_shedule(id: str, second: float, job):
  schedule.every(second).seconds.do(job).tag(id)

def add_timed_shedule(id: str, time_point: str, job):
  schedule.every().at(time_point).do(job).tag(id)

def update_time_interval_schedule(id: str, second: float, job):
  schedule.clear(id)
  add_time_interval_shedule(id, second, job)

def update_timed_schedule(id: str, time_point: str, job):
  schedule.clear(id)
  add_timed_shedule(id, time_point, job)
