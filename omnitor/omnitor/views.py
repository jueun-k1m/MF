from django.shortcuts import render
from django.http import JsonResponse, HttpResponseBadRequest
from django.utils import timezone
from datetime import datetime, timedelta
from django.conf import settings as django_settings
from django.contrib.staticfiles.storage import staticfiles_storage
import json
import time
import statistics
import math
import os


from views.pages.dashboard import dashboard_api
from views.apis.calibrate import calibrate_api
from views.apis.camera_time import camera_time_api
from views.apis.journal import journal_api
