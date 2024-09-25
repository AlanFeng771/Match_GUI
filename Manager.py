import numpy as np
import json
import csv
class Bbox:
    def __init__(self, bbox):
        self.bbox = bbox
        self.category = None
        self.nodule_index = -1
    
    def get_annotation(self):
        return self.bbox
    
    def get_start_slice(self):
        return self.bbox[0][2]
    
    def get_nodule_index(self):
        return self.nodule_index
    
    def set_category(self, category):
        self.category = category
    
    def set_nodule_index(self, nodule_index):
        self.nodule_index = nodule_index
        

class Patient:
    def __init__(self, image_id:str):
        self.bboxes = []
        self.image_id = image_id
        self.bbox_path = None
        self.image_path = None
        
    def _process_bboxes(self):
        self.bboxes = []
        with open(self.bbox_path, 'r') as json_file:
            bboxe_list = json.load(json_file)['bboxes']
        for bbox in bboxe_list:
            self.bboxes.append(Bbox(bbox))
    
    def set_bbox_path(self, bbox_path:str):
        self.bbox_path = bbox_path
        self._process_bboxes()
    
    def set_image_path(self, image_path:str):
        self.image_path = image_path
    
    def get_images(self):
        return np.load(self.image_path)
    
    def get_bboxes(self):
        return self.bboxes

    def is_access_granted(self):
        if self.bbox_path is not None and self.image_path is not None:
            return True
        else:
            return False
    
    def get_start_slices(self)->list:
        return [bbox.get_start_slice() for bbox in self.bboxes]

class PatientManager:
    def __init__(self):
        self.current_patient_index = None
        self.patients = {}
    
    def get_patient(self, patient_index:int)->Patient:
        patient_ids = list(self.patients.keys())
        patient_id = patient_ids[patient_index]
        if patient_id in self.patients:
            self.current_patient_index = patient_index
            return self.patients[patient_id]
        else:
            return None
    
    def get_patient_from_id(self, patient_id:str)->Patient:
        # patient_ids = list(self.patients.keys())
        # patient_index = patient_ids.index(patient_id)
        if patient_id in self.patients:
            # self.current_patient_index = patient_index
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
            patient.set_image_path(image_path)
        
    def add_bbox_from_file(self, patient_id:str, bbox_path:str):
        if patient_id not in self.patients:
            patient = Patient(patient_id)
            patient.set_bbox_path(bbox_path)
            self._add_patient(patient)
        else:
            patient = self.get_patient_from_id(patient_id)
            patient.set_bbox_path(bbox_path)
        
    def add_images_from_direction(self, patient_ids:list, image_paths:list):
        if len(patient_ids)>0:
            self.current_patient_index = 0
            
        for patient_id, image_path in zip(patient_ids, image_paths):
            self.add_image_from_file(patient_id, image_path)
    
    def add_bboxes_from_direction(self, patient_ids:list, bbox_paths:list):
        for patient_id, bbox_path in zip(patient_ids, bbox_paths):
            self.add_bbox_from_file(patient_id, bbox_path)
        
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

class ClsElement:
    def __init__(self, start_slice:int, category:int):
        self.start_slice = start_slice
        self.category = category
        
    def get_start_slice(self):
        return self.start_slice
    
    def get_category(self):
        return self.category

class PatientClsElement:
    def __init__(self, patient_id:str):
        self.patient_id = patient_id
        self.cls_elements = []
    
    def add_element(self, start_slice:int, category:int):
        self.cls_elements.append(ClsElement(start_slice, category))
    
    def get_elements(self):
        return self.cls_elements
    
    def get_nodule_count(self):
        return len(self.cls_elements)
        
class ClsManager:
    def __init__(self):
        self.patient_cls_elements = {}
    
    def get_patient(self, patient_id:str)->PatientClsElement:
        if patient_id in self.patient_cls_elements:
            return self.patient_cls_elements[patient_id]
        else:
            return None
    
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
                    
                self.patient_cls_elements[patient_id].add_element(start_slice, tw_lung_rads)
    
    
    
    
    


    
    
            
    



    
    
    