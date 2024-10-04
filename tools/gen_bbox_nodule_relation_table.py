import json
import os
import csv
bbox_direction = 'bbox'
bbox_json_files = os.listdir(bbox_direction)
patient_ids = [patient_id.split('\\')[-1].replace('.json', '') for patient_id in os.listdir(bbox_direction)]
json_keys = ['patient_id', 'bbox_index', 'nodule_index', 'category']

with open('bbox.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    for patient_id, bbox_json_file in zip(patient_ids, bbox_json_files):
        with open(os.path.join(bbox_direction, bbox_json_file), 'r') as f:
            bbox_json = json.load(f)
            nodule_start_slice_ids = bbox_json['nodule_start_slice_ids']
            for bbox_index in range(len(nodule_start_slice_ids)):
                data = [patient_id, bbox_index, [], []]
                writer.writerow(data)

        
        
        


