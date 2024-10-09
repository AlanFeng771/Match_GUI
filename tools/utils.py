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

def get_nodule_information(type='predict'):
    annotation = {}
    if type == 'predict':
        csv_file = pd.read_csv('predict_epoch_0.csv').T
        for ann_index in csv_file:
            seriesuid = csv_file[ann_index]['seriesuid']
            ann = np.array(csv_file[ann_index].values[1:])
            ann = ann[np.array([0, 1, 2, 4, 5, 6, 3])]
            if annotation.get(seriesuid, None) is None:
                annotation[seriesuid] = [ann]
            else:
                annotation[seriesuid].append(ann)

    elif type == 'gt':
        csv_file = pd.read_csv('annotation_val.csv').T
        for ann_index in csv_file:
            seriesuid = csv_file[ann_index]['seriesuid']
            ann = np.array(csv_file[ann_index].values[1:])
            if annotation.get(seriesuid, None) is None:
                annotation[seriesuid] = [ann]
            else:
                annotation[seriesuid].append(ann)

    return annotation

def get_annotation(annotation_file):
    annotations = {}
    csv_file = pd.read_csv(annotation_file).T
    for ann_index in csv_file:
        seriesuid = csv_file[ann_index]['seriesuid']
        ann = np.array(csv_file[ann_index].values[1:])
        ann = ann[np.array([0, 1, 2, 4, 5, 6, 3])]
        if annotations.get(seriesuid, None) is None:
            annotations[seriesuid] = [ann]
        else:
            annotations[seriesuid].append(ann)
    return annotations


def get_nodule_annotation(annotation_file):
    annotations = {}
    csv_file = pd.read_csv(annotation_file)
    csv_file = csv_file.sort_values(by=['coordZ']).T
    if 'state' in csv_file[0]:
        file_type = 'log'
    else:
        file_type = 'annotation'
    for ann_index in csv_file:
        seriesuid = csv_file[ann_index]['seriesuid']
        if isinstance(seriesuid, int):
            seriesuid = f'{seriesuid:04}'
        # if seriesuid in patients:
        if file_type == 'annotation':
            ann = np.array(csv_file[ann_index].values[1:7]) # x, y, z, w, h, d
            if 'probability' in csv_file[0]: # x, y, z, w, h, d, p
               ann = np.append(ann, csv_file[ann_index]['probability']) 
            else:
                ann = np.append(ann, 1.0)
                
            if 'model' in csv_file[0]: # x, y, z, w, h, d, model
                ann = np.append(ann, csv_file[ann_index]['model'])
            else:
                ann = np.append(ann, '')
        else:
            ann = np.array(csv_file[ann_index].values[1:])

        if 'nodule_type' not in csv_file[0]:
            print('ann', ann)
        nodule = Nodule(patient_id=seriesuid, nodule_id=ann_index, type=file_type, annotation_file=annotation_file)
        nodule.load_annotation(ann)
        if annotations.get(seriesuid, None) is None:
            annotations[seriesuid] = [nodule]
        else:
            annotations[seriesuid].append(nodule)
    return annotations

class Nodule:
    def __init__(self, patient_id, nodule_id, annotation_file=None, type='predict'):
        self.patient_id = patient_id
        self.nodule_id = nodule_id
        self.center_x = 0
        self.center_y = 0
        self.center_z = 0
        self.w = 0
        self.h = 0
        self.confidence = 0
        self.nodule_type = None
        self.bbox = None
        self.type = type
        self.model_name = ''
        self.annotation_file = annotation_file
        '''
        self.stare == -1 can't comment
        self.state == 0 no comment
        self.state == 1 no comment but no save (temp comment)
        self.state == 2 comment and save
        '''
        self.state = 0
        self.is_hidden = False
        self.log = {'category':-1,
                    'gt_category':-1,
                    'is_follow_up':False,
                    'is_pneumonia':False,
                    'log':''}
        
        # record pneumonia serise
        self.black_list = []

    def load_annotation(self, annotation):
        if(annotation[7] != ''):
            print('annotation', annotation)
        if self.type == 'annotation':
            self.center_x = annotation[0]
            self.center_y = annotation[1]
            self.center_z = annotation[2]
            self.w = annotation[3]
            self.h = annotation[4]
            self.d = annotation[5]
            self.confidence = annotation[6]
            self.model_name = annotation[7]
            # print('model_name', self.model_name)
            self.state = 0
        # elif self.type == 'gt':
        #     self.center_x = annotation[0]
        #     self.center_y = annotation[1]
        #     self.center_z = annotation[2]
        #     self.w = annotation[3]
        #     self.h = annotation[4]
        #     self.d = annotation[5]
        #     self.nodule_type = annotation[6]
        #     self.state = -1
        elif self.type == 'log':
            # annotation = annotation[np.array([0, 1, 2, 4, 5, 6, 3, 7, 8, 9, 10])]
            self.center_x = annotation[0]
            self.center_y = annotation[1]
            self.center_z = annotation[2]
            self.w = annotation[3]
            self.h = annotation[4]
            self.d = annotation[5]
            self.confidence = annotation[6]
            self.state = annotation[7]
            self.log['category'] = annotation[8]
            self.log['gt_category'] = annotation[9]
            self.log['is_follow_up'] = annotation[10]
            self.log['is_pneumonia'] = annotation[11]
            self.model_name = annotation[13]
        
    def get_nodule_annotation(self):
        return self.center_x, self.center_y, self.center_z, self.w, self.h, self.d, self.confidence
    
    def set_bbox(self, bbox):
        self.bbox = bbox
    
    def set_hidden(self, hidden):
        self.is_hidden = hidden
    
    def set_state(self, state):
        self.state = state
    
    def set_slice_range(self, start, end):
        self.center_z = (end + start)/2
        self.d = end - start
    
    def set_log(self, category, log, black_list):
        self.black_list = black_list
        self.log['category'] = category[0]
        self.log['gt_category'] = category[1]
        self.log['is_follow_up'] = category[2]
        self.log['is_pneumonia'] = category[3]
        self.log['log'] = log
    
    def get_log(self):
        return self.log
    
    def output_log(self):
        if self.state == 1:
            self.state = 2
        
        output = [
            self.patient_id,
            self.center_x,
            self.center_y,
            self.center_z,
            self.w,
            self.h,
            self.d,
            self.confidence,
            self.state,
            self.log['category'],
            self.log['gt_category'],
            self.log['is_follow_up'],
            self.log['is_pneumonia'],
            str(self.log['log']),
            self.model_name
        ]
        return output

def get_local_time_in_taiwan() -> datetime.datetime:
    utc_now = datetime.datetime.utcnow()
    taiwan_now = utc_now + datetime.timedelta(hours=8) # Taiwan in UTC+8
    return taiwan_now

def get_local_time_str_in_taiwan() -> str:
    cur_time = get_local_time_in_taiwan()
    timestamp = "[%d-%02d-%02d-%02d%02d]" % (cur_time.year, cur_time.month, cur_time.day, cur_time.hour, cur_time.minute)
    return timestamp

def output_log_file(nodels, outdir_root):
    annotation_file_type = nodels[list(nodels.keys())[0]][0].type
    annotation_file = nodels[list(nodels.keys())[0]][0].annotation_file
    black_list = nodels[list(nodels.keys())[0]][0].black_list
    if annotation_file_type != 'log':
        timestamp = get_local_time_str_in_taiwan()
        outdir = os.path.join(outdir_root, timestamp)

        if not os.path.isdir(outdir):
            os.makedirs(outdir)

        outfile = os.path.join(outdir, f'{timestamp}_{annotation_file.split("/")[-1]}')
    else:
        print('log file')
        outfile = annotation_file

    
    title = ['seriesuid','coordX','coordY','coordZ','w','h','d','probability', 'state', 'category', 'gt_category', 'is_follow_up', 'is_pneumonia', 'log', 'model']
    with open(outfile, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(title)
        for patient_id in nodels.keys():
            for nodule in nodels[patient_id]:
                log = nodule.output_log()
                # print('log', log)
                if patient_id in black_list:
                    nodule.set_state(1)
                    log[12] = True
                writer.writerow(log)



    