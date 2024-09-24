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
    def __init__(self, image_id:str, bbox_path:str, image_path:str):
        self.bboxes = []
        self.image_id = image_id
        self.bbox_path = bbox_path
        self.image_path = image_path
        self._process_bboxes()
    
    def _process_bboxes(self):
        with open(self.bbox_path, 'r') as json_file:
            bboxe_list = json.load(json_file)['bboxes']
        for bbox in bboxe_list:
            self.bboxes.append(Bbox(bbox))
    
    def get_images(self):
        return np.load(self.image_path)

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
        
    def add_patient_from_file(self, image_id:str, bbox_path:str, image_path:str):
        patient = Patient(image_id, bbox_path, image_path)
        self._add_patient(patient)
        
    def add_patient_from_direction(self, image_ids:list, bbox_paths:list, image_paths:list):
        for image_id, bbox_path, image_path in zip(image_ids, bbox_paths, image_paths):
            self.add_patient_from_file(image_id, bbox_path, image_path)
    
    


    
    
            
    



    
    
    