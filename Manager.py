import numpy as np
import json
class Bbox:
    def __init__(self, bbox):
        self.bbox = bbox
        self.category = None
    
    def get_annotation(self):
        return self.bbox
    
    def set_category(self, category):
        self.category = category

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

class PatientManager:
    def __init__(self):
        self.patients = {}
    
    def get_patient(self, patient_id:str):
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
            patient = self.get_patient(patient_id)
            patient.set_image_path(image_path)
        
    def add_bbox_from_file(self, patient_id:str, bbox_path:str):
        if patient_id not in self.patients:
            patient = Patient(patient_id)
            patient.set_bbox_path(bbox_path)
            self._add_patient(patient)
        else:
            patient = self.get_patient(patient_id)
            patient.set_bbox_path(bbox_path)
        
    def add_images_from_direction(self, patient_ids:list, image_paths:list):
        for patient_id, image_path in zip(patient_ids, image_paths):
            self.add_image_from_file(patient_id, image_path)
    
    def add_bboxes_from_direction(self, patient_ids:list, bbox_paths:list):
        for patient_id, bbox_path in zip(patient_ids, bbox_paths):
            self.add_bbox_from_file(patient_id, bbox_path)
    
    


    
    
            
    



    
    
    