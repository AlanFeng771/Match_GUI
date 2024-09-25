from json import load
from tkinter import N
from PyQt5.QtCore import Qt
from PyQt5 import QtWidgets
import widgets
import Manager
import os
class Controller(QtWidgets.QWidget):
    def __init__(self):
        super(Controller, self).__init__()
        self.patient_manager = Manager.PatientManager()
        self.Cls_manager = Manager.ClsManager()
        self.patient_ids = []
        self.cls_index = 0
        self.bbox_index = 0
        self.Cls_manager.load_csv_file(r'E:\workspace\python\Tools\check_nodule_classification\lung_M_class_0001-1800.csv')
        self.patient_ids = []
        self.initWidget()
        
    def initWidget(self):
        # widgets
        self.player = widgets.PlayerView()
        self.player_with_bbox = widgets.PlayerView()
        self.load_image_button = widgets.LoadImageButton()
        self.load_bbox_button = widgets.LoadAnnotationButton()
        self.load_image_direction_button = widgets.LoadImageDirectionButton()
        self.load_bbox_direction_button = widgets.LoadAnnotationsDirectionButton()
        self.next_patient_button = widgets.NextPatientButton()
        self.previous_patient_button = widgets.PreviousPatientButton()
        self.Cls_button_list = widgets.ButtonListWindow() 
        self.bbox_button_list = widgets.BboxesButtonListView()
        self.patient_index_controller = widgets.PatientControlWidget()
        self.next_nodule_button = widgets.NextNoduleButton()
        self.previous_nodule_button = widgets.PreviousNoduleButton()
          
        # layout
        VBlayout = QtWidgets.QVBoxLayout(self)
        HBlayout = QtWidgets.QHBoxLayout()
        VBlayout1 = QtWidgets.QVBoxLayout()
        list_HBlayout = QtWidgets.QHBoxLayout()
        load_HBlayout = QtWidgets.QHBoxLayout()
        HBlayout.addWidget(self.player, 4)
        HBlayout.addWidget(self.player_with_bbox, 4)
        load_HBlayout.addWidget(self.load_image_direction_button)
        load_HBlayout.addWidget(self.load_bbox_direction_button)
        VBlayout1.addLayout(load_HBlayout)
        VBlayout1.addWidget(self.patient_index_controller)
        list_HBlayout.addWidget(self.Cls_button_list)
        list_HBlayout.addWidget(self.bbox_button_list)
        VBlayout1.addLayout(list_HBlayout)
        VBlayout1.addWidget(QtWidgets.QWidget())
        HBlayout.addLayout(VBlayout1)
        VBlayout.addLayout(HBlayout)
        VBlayout.addWidget(self.next_nodule_button)
        VBlayout.addWidget(self.previous_nodule_button)
        
        # func
        self.load_image_button.load_image_clicked.connect(self.load_image)
        self.load_bbox_button.load_annotation_clicked.connect(self.load_bbox)
        self.load_image_direction_button.load_image_direction_clicked.connect(self.load_images_from_direction)
        self.load_bbox_direction_button.load_annotation_direction_clicked.connect(self.load_bboxes_from_direction)
        self.Cls_button_list.Cls_button_clicked.connect(self.jump_to_nodule_start_slice)
        self.bbox_button_list.bbox_button_clicked.connect(self.jump_to_nodule_bbox_start_slice)
        self.patient_index_controller.next_clicked.connect(self.next_patient)
        self.patient_index_controller.previous_clicked.connect(self.previous_patient)
        self.patient_index_controller.patient_index_changed.connect(self.patient_index_changed)
        self.next_nodule_button.next_nodule_clicked.connect(self.next_nodule)
        self.previous_nodule_button.previous_nodule_clicked.connect(self.previous_nodule)
        
    def load_image(self, image_path):
        self.patient_ids = [image_path.split('/')[-1].split('.')[0]]
        self.patient_manager.add_image_from_file(self.patient_ids[0], image_path)
        self.player.load_image(self.patient_manager.get_patient(0))

    def load_bbox(self, bbox_path):
        self.patient_manager.add_bbox_from_file(self.patient_ids[0], bbox_path)
        self.player.load_bbox(self.patient_manager.get_patient(0))
        
        self.bbox_button_list.clear_buttons()
        self.bbox_button_list.add_buttions(self.patient_manager.get_patient(0))
        
    def load_images_from_direction(self, direction_path):
        self.patient_ids = [path.split('/')[-1].split('.')[0] for path in os.listdir(direction_path)]
        if len(self.patient_ids) == 0:
            return
        
        image_paths = [f'{direction_path}/{patient_id}.npy' for patient_id in self.patient_ids]
        self.patient_manager.add_images_from_direction(self.patient_ids, image_paths)
        
        patient_index = self.patient_manager.get_current_index()
        if patient_index is None:
            return
        self.player.load_image(self.patient_manager.get_patient(patient_index))
        self.player_with_bbox.load_image(self.patient_manager.get_patient(patient_index))
        self.player.show(0)
        self.player_with_bbox.show(0)
        self.Cls_button_list.clear_buttons()
        
        self.patient_index_controller.clear()
        self.patient_index_controller.addPatients(self.patient_ids)
        self.load_bbox_direction_button.setEnabled(True)
        
    def load_bboxes_from_direction(self, direction_path):
        if len(self.patient_ids) == 0:
            return

        bbox_paths = [f'{direction_path}/{patient_id}.json' for patient_id in self.patient_ids]
        self.patient_manager.add_bboxes_from_direction(self.patient_ids, bbox_paths)
        
        patient_index = self.patient_manager.get_current_index()
        if patient_index is None:
            return
        self.player_with_bbox.load_bbox(self.patient_manager.get_patient(patient_index))
        self.player_with_bbox.show(0)
        
        self.bbox_button_list.clear_buttons()
        self.bbox_button_list.add_bboxes(self.patient_manager.get_patient(patient_index), self.Cls_manager.get_patient(self.patient_ids[patient_index]))
        
    def next_patient(self):
        self.patient_manager.next_index()
        patient_index = self.patient_manager.get_current_index()
        if patient_index is None:
            return
        else:
            self.patient_index_controller.setPatientIndex(patient_index)            
    
    def previous_patient(self):
        self.patient_manager.previous_index()
        patient_index = self.patient_manager.get_current_index()
        if patient_index is None:
            return
        else:
            self.patient_index_controller.setPatientIndex(patient_index)
    
    def patient_index_changed(self, index:int):
        self.patient_manager.set_patient_index(index)
        patient = self.patient_manager.get_patient(index)
        cls_patient = self.Cls_manager.get_patient(self.patient_ids[index])
        patient_index = self.patient_manager.get_current_index()
        if patient_index is None:
            return
        
        self.Cls_button_list.clear_buttons()
        self.Cls_button_list.add_buttions(cls_patient)
        
        self.bbox_button_list.clear_buttons()
        self.bbox_button_list.add_bboxes(patient, cls_patient)
        
        self.player_with_bbox.reset_rects()
        self.player.load_image(patient)
        self.player_with_bbox.load_image(patient)
        self.player_with_bbox.load_bbox(patient)
        self.player.show(0)
        self.player_with_bbox.show(0)
        
        self.Cls_button_list.set_cls_button_index(self.cls_index)
        self.jump_to_nodule_start_slice(self.cls_index)
        
    
    def jump_to_nodule_start_slice(self, nodule_index:int):
        patient_index = self.patient_manager.get_current_index()
        if patient_index is None:
            return
        image_index = self.Cls_manager.get_patient(self.patient_ids[patient_index]).get_elements()[nodule_index].get_start_slice()
        self.player.show(image_index)
    
    def jump_to_nodule_bbox_start_slice(self, nodule_index:int):
        patient_index = self.patient_manager.get_current_index()
        if patient_index is None:
            return
        image_index = self.patient_manager.get_patient(patient_index).get_start_slices()[nodule_index]
        self.player_with_bbox.show_and_focus_bbox(index=nodule_index, image_index=image_index)
    
    def next_nodule(self):
        print(self.cls_index)
        if self.Cls_button_list.set_cls_button_index(self.cls_index+1):
            self.cls_index += 1
        self.jump_to_nodule_start_slice(self.cls_index)
    
    def previous_nodule(self):
        if self.Cls_button_list.set_cls_button_index(self.cls_index-1):
            self.cls_index -= 1
        self.jump_to_nodule_start_slice(self.cls_index)
        
if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)
    controller = Controller()
    controller.setGeometry(500, 300, 1200, 600)
    controller.showMaximized()
    sys.exit(app.exec_())
        
