from calendar import c
import numpy as np
import pandas as pd
import os
import csv
import datetime
from  collections import OrderedDict
DEFAULT_WINDOW_LEVEL = -300
DEFAULT_WINDOW_WIDTH = 1400

CATEGORIES = {  
                'Incomplete':[],
                'Negative (0)':['No lung nodules', 'complete nodule', 'central nodule', 'popcorn nodule', 'fat containing nodule'], 
                'Benign (1)':['Perifissural nodule', 'Solid nodule', 'Part solid nodule', 'Non solid nodule (GGN)'],
                'Probably Benign (2)':['Solid nodule', 'Part solid nodule', 'Non solid nodule'], 
                'Suspicious (3)':['Solid nodule', 'Part solid nodule', 'Endobronchial nodule'], 
                'Very Suspicious (4)':['Solid nodule', 'Part solid nodule'],
                'Confuse':[]
            }

def get_HU_MIN_MAX(window_level: int, window_width: int):
        hu_min = window_level - window_width // 2
        hu_max = window_level + window_width // 2
        return hu_min, hu_max

def normalize_raw_image(image: np.ndarray, window_level: int = DEFAULT_WINDOW_LEVEL, window_width: int = DEFAULT_WINDOW_WIDTH) -> np.ndarray:
    hu_min, hu_max = get_HU_MIN_MAX(window_level, window_width)    
    image = np.clip(image, hu_min, hu_max)
    image = image - hu_min
    image = image.astype(np.float32) / (hu_max - hu_min)
    return image

def get_local_time_in_taiwan() -> datetime.datetime:
    utc_now = datetime.datetime.utcnow()
    taiwan_now = utc_now + datetime.timedelta(hours=8) # Taiwan in UTC+8
    return taiwan_now

def get_local_time_str_in_taiwan() -> str:
    cur_time = get_local_time_in_taiwan()
    timestamp = "[%d-%02d-%02d-%02d%02d]" % (cur_time.year, cur_time.month, cur_time.day, cur_time.hour, cur_time.minute)
    return timestamp



    