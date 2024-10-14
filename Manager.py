from operator import index
from tkinter import N
from turtle import width
import numpy as np
import json
import csv
import tools.tools as tools
import os
from typing import Union
class Bbox:
    def __init__(self, bbox:list, bbox_index:int):
        self.bbox = bbox # centroid_x, centroid_y, centroid_z, width, height, depth
        self.bbox_index = bbox_index
        self.category = None
        self.nodule_index = -1
        self.type = 0
        self.box_group = bbox_index
        self.is_checked = False
    
    def get_annotation(self):
        return self.bbox
    
    def get_start_slice(self):
        return int(self.bbox[2] - self.bbox[5] // 2)
    
    def get_nodule_index(self):
        return self.nodule_index
    
    def get_bbox_type(self):
        return self.type
    
    def get_box_group(self):
        return self.box_group

    def get_checked(self):
        return self.is_checked
    
    def set_node_index(self, nodule_index:int):
        self.nodule_index = nodule_index
    
    def set_category(self, category):
        self.category = category
    
    def set_nodule_index(self, nodule_index):
        self.nodule_index = nodule_index
    
    def set_box_type(self, bbox_type:int):
        self.type = bbox_type
    
    def set_group(self, box_group:int):
        self.box_group = box_group
    
    def set_checked(self, is_checked:bool):
        self.is_checked = is_checked

class Patient:
    def __init__(self, image_id:str):
        self.bboxes = []
        self.image_id = image_id
        self.bbox_path = None
        self.image_path = None
        self.bbox_index = 0
        
    # def _process_bboxes(self, match:list=[]):
    #     self.bboxes = []
    #     if self.bbox_path is None:
    #         return

    #     if os.path.exists(self.bbox_path) is False:
    #         print('bbox file not found:', self.bbox_path)
    #         return
            
    #     with open(self.bbox_path, 'r') as json_file:
    #         bboxe_list = json.load(json_file)['bboxes']
            
    #     for bbox_index, bbox_data in enumerate(bboxe_list):
    #         bbox = Bbox(bbox_data, bbox_index=bbox_index)
    #         if bbox_index < len(match):
    #             bbox.set_nodule_index(match[bbox_index])
    #         self.bboxes.append(bbox)
    
    def set_bbox(self, bbox_info:list):
        # self.bboxes = []
            
        # for bbox_index, bbox_info in enumerate(bbox_list):
        bbox_data = bbox_info[:6] # cnetroid_x, centroid_y, centroid_z, width, height, depth
        bbox_type = bbox_info[6]
        releated_index = bbox_info[7]
        is_checked = bbox_info[8]
        bbox = Bbox(bbox_data, bbox_index=self.bbox_index)
        self.bbox_index += 1
        bbox.set_box_type(bbox_type)
        if bbox_type == 0:
            bbox.set_nodule_index(releated_index)
        elif bbox_type == 1:
            bbox.set_group(releated_index)
        bbox.set_checked(is_checked)
        self.bboxes.append(bbox)
    
    
    # def set_bbox_path(self, bbox_path:str):
    #     self.bbox_path = bbox_path
    #     self._process_bboxes()
    
    # def set_bbox(self, bbox_path:str, match:list=[]):
    #     self.bbox_path = bbox_path
    #     self._process_bboxes(match)
    
    def set_image_path(self, image_path:str):
        self.image_path = image_path
    
    def get_images(self):
        # return np.load(self.image_path)['image']
        return tools.normalize_raw_image(np.load(self.image_path))
    
    def get_bboxes(self):
        return self.bboxes

    def get_box_count(self):
        return len(self.bboxes)
    
    def get_bbox(self, bbox_index:int):
        if self.is_bbox_index_valid(bbox_index):
            return self.bboxes[bbox_index]
        else:
            return None

    def is_access_granted(self):
        if self.bbox_path is not None and self.image_path is not None:
            return True
        else:
            return False
    
    def get_start_slices(self)->list:
        return [bbox.get_start_slice() for bbox in self.bboxes]
    
    def is_bbox_index_valid(self, bbox_index:int):
        if bbox_index < 0 or bbox_index >= len(self.bboxes):
            return False
        else:
            return True
    def get_image_id(self):
        return self.image_id

class PatientManager:
    def __init__(self):
        self.current_patient_index = None
        self.current_bbox_index = None
        self.patients = {}
        self.match_table:dict = {}

    def get_patient(self, patient_index: int) -> Union[Patient, None]:
        patient_ids = list(self.patients.keys())
        patient_id = patient_ids[patient_index]
        if patient_id in self.patients:
            self.current_patient_index = patient_index
            return self.patients[patient_id]
        else:
            return None
    
    def get_patient_from_id(self, patient_id:str)->Union[Patient, None]:
        if patient_id in self.patients:
            return self.patients[patient_id]
        else:
            return None
    
    def _add_patient(self, patient:Patient):
        self.patients[patient.image_id] = patient
        
    def add_image_from_file(self, patient_id:str, image_path:str):
        if patient_id not in self.patients:
            patient = Patient(patient_id)
            patient.set_image_path(image_path)
            self._add_patient(patient)
        else:
            
            patient = self.get_patient_from_id(patient_id)
            if patient is not None:
                patient.set_image_path(image_path)
        
    # def add_bbox_from_file(self, patient_id:str, bbox_path:str):
    #     if patient_id not in self.patients:
    #         patient = Patient(patient_id)
    #         self._add_patient(patient)
    #     else:
    #         patient = self.get_patient_from_id(patient_id)
    #         # patient.set_bbox_path(bbox_path)
        
    #     if patient is None:
    #         return
        
    #     if patient_id in self.match_table:
    #         patient.set_bbox(bbox_path, self.match_table[patient_id])
    #     else:
    #         patient.set_bbox(bbox_path)
        
    def add_images_from_direction(self, patient_ids:list, image_paths:list):
        if len(patient_ids)>0:
            self.current_patient_index = 0
            
        for patient_id, image_path in zip(patient_ids, image_paths):
            self.add_image_from_file(patient_id, image_path)
    
    # def add_bboxes_from_direction(self, patient_ids:list, bbox_paths:list):
    #     for patient_id, bbox_path in zip(patient_ids, bbox_paths):
    #         self.add_bbox_from_file(patient_id, bbox_path)
        
    def get_current_index(self):
        return self.current_patient_index
    
    def next_index(self):
        patient_ids = list(self.patients.keys())
        if self.current_patient_index is None:
            return None
        
        if self.current_patient_index == len(patient_ids) - 1:
            self.current_patient_index = len(patient_ids) - 1
        else:
            self.current_patient_index += 1
    
    def previous_index(self):
        if self.current_patient_index is None:
            return None

        if self.current_patient_index == 0:
            self.current_patient_index = 0
        else:
            self.current_patient_index -= 1
    
    def set_patient_index(self, patient_index:int):
        patient_ids = list(self.patients.keys())
        if patient_index < 0 or patient_index >= len(patient_ids):
            return
        self.current_patient_index = patient_index
    
    def load_match_table(self, match_table_file:str):
        with open(match_table_file, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                patient_id = row['patient_id']
                if patient_id not in self.match_table:
                    self.match_table[patient_id] = []
                
                self.match_table[patient_id].append(int(row['nodule_id']))
    
    def load_bboxes(self, bbox_annotaion_file:str):
        with open(bbox_annotaion_file, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                patient_id = row['patient_id']
                bbox_list = [float(row['center_x']), float(row['center_y']), float(row['center_z']), int(row['width']), int(row['height']), int(row['depth']), int(row['type']), int(row['index']), row['is_checked']=='True']
                
                if patient_id not in self.patients:
                    patient = Patient(patient_id)
                    self._add_patient(patient)
                else:
                    patient = self.get_patient_from_id(patient_id)
                
                if patient is None:
                    return
                patient.set_bbox(bbox_list)
        
    def output_match_table(self, match_table_file:str):
        with open(match_table_file, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['patient_id', 'bbox_id', 'nodule_id'])
            for patient_id, patient in self.patients.items():
                bbox = patient.get_bboxes()
                for bbox_index, bbox_data in enumerate(bbox):
                    writer.writerow([patient_id, bbox_index, bbox_data.get_nodule_index()])
    
class ClsElement:
    def __init__(self, start_slice:int, category:int):
        self.start_slice = start_slice
        self.category = category
        self.is_checked = False
        
    def get_start_slice(self):
        return self.start_slice
    
    def get_category(self):
        return self.category

    def get_checked(self):
        return self.is_checked
    
    def set_checked(self, is_checked:bool):
        self.is_checked = is_checked    

class PatientClsElement:
    def __init__(self, patient_id:str):
        self.patient_id = patient_id
        self.cls_elements = []
        self.sort_cls_elements = []
        self.sorted_index = []
        self.mask_path = None
    
    def add_element(self, start_slice:int, category:int):
        self.cls_elements.append(ClsElement(start_slice, category))
        start_slices = [cls_element.get_start_slice() for cls_element in self.cls_elements]
        self.sort_cls_elements = sorted(self.cls_elements, key=lambda cls_element: cls_element.get_start_slice()) 
        self.sorted_index = sorted((start_slice, bbox_index) for bbox_index, start_slice in enumerate(start_slices))
        self.sorted_index = [sorted_index[1] for sorted_index in self.sorted_index]
    
    def get_bbox_index(self, indx)->int:
        return self.sorted_index[indx]
    
    def get_elements(self):
        return self.cls_elements

    def get_sorted_elements(self):
        return self.sort_cls_elements
    
    def get_element(self, element_index):
        return self.sort_cls_elements[element_index]

    def get_nodule_index(self, indx):
        return self.sorted_index[indx]
    
    def get_nodule_count(self):
        return len(self.cls_elements)
    
    def set_mask_path(self, mask_path:str):
        self.mask_path = mask_path
        
    def get_contour_images(self):
        mask = np.load(self.mask_path)['image']
        
        return mask
        
class ClsManager:
    def __init__(self):
        self.patient_cls_elements = {}
        self.mask_root = None
    
    def get_patient(self, patient_id:str)->Union[PatientClsElement, None]:
        if patient_id in self.patient_cls_elements:
            return self.patient_cls_elements[patient_id]
        else:
            return None
    
    def set_mask_root(self, mask_root:str):
        self.mask_root = mask_root
        
    def load_csv_file(self, csv_file:str):
        with open(csv_file, 'r') as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                img_name = row['Img name']
                tw_lung_rads = int(row['TW_Lung_RADS'])
                _, patient_id, start_slice = img_name.split('-')
                patient_id = patient_id[2:]
                start_slice = int(start_slice[1:])
                if patient_id not in self.patient_cls_elements:
                    self.patient_cls_elements[patient_id] = PatientClsElement(patient_id)
                
                if self.mask_root is not None:
                    mask_path = os.path.join(self.mask_root, patient_id + '.npz')
                    self.patient_cls_elements[patient_id].set_mask_path(mask_path)
                    
                self.patient_cls_elements[patient_id].add_element(start_slice, tw_lung_rads)
    
    
    
    
    


    
    
            
    



    
    
    