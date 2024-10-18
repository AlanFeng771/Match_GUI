from email.mime import base
from PyQt5.QtCore import Qt
from PyQt5 import QtWidgets
from PyQt5.QtGui import QKeySequence
import widgets
import Manager
import argparse
import logging
import os
logger = logging.getLogger(__name__)
class Controller(QtWidgets.QWidget):
    def __init__(self, args):
        super(Controller, self).__init__()
        self.patient_manager = Manager.PatientManager()
        self.Cls_manager = Manager.ClsManager()
        self.patient_ids = []
        self.cls_index = 0
        self.bbox_index = 0
        self.annotation_file = args.annotation_file
        self.image_direction = args.image_root
        self.bbox_annotation_file = args.bbox_annotation_file
        self.patient_ids_file = args.patient_ids_file
        self.output_file_name = args.output_file_name
        self.mask_root = args.mask_root
        self.Cls_manager.set_mask_root(self.mask_root)
        self.Cls_manager.load_csv_file(self.annotation_file)
    
        with open(self.patient_ids_file, 'r') as f:
            patient_ids = f.readlines()
            
        self.patient_ids = [patient_id.strip() for patient_id in patient_ids]
        self.initWidget()
        self.patient_manager.set_patient_ids(self.patient_ids)
        self.load_images_from_direction(self.image_direction)
        self.load_bboxes_from_file(self.bbox_annotation_file)
        
    def initWidget(self):
        # widgets
        self.player = widgets.PlayerView()
        self.player_with_bbox = widgets.PlayerWithRectView()
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
        self.next_bbox_button = widgets.NextBboxButton()
        self.previous_bbox_button = widgets.PreviousBboxButton()
        self.display_label1 = widgets.DisplayNoduleTable()
        self.display_label2 = widgets.DisplayBBoxTable()
        self.output_button = widgets.OutputButton()
        self.bbox_info_display = widgets.BboxInfoWidget()
        
        # main layout
        HBlayout = QtWidgets.QHBoxLayout(self)

        # nodule layout
        nodule_VBlayout = QtWidgets.QVBoxLayout()
        nodule_VBlayout.addWidget(self.display_label1)
        nodule_VBlayout.addWidget(self.player)
        nodule_button_HBlayout = QtWidgets.QHBoxLayout()
        nodule_button_HBlayout.addWidget(self.previous_nodule_button)
        nodule_button_HBlayout.addWidget(self.next_nodule_button)
        nodule_VBlayout.addLayout(nodule_button_HBlayout)

        # bbox layout
        bbox_VBlayout = QtWidgets.QVBoxLayout()
        bbox_VBlayout.addWidget(self.display_label2)
        bbox_VBlayout.addWidget(self.player_with_bbox)
        bbox_button_HBlayout = QtWidgets.QHBoxLayout()
        bbox_button_HBlayout.addWidget(self.previous_bbox_button)
        bbox_button_HBlayout.addWidget(self.next_bbox_button)
        bbox_VBlayout.addLayout(bbox_button_HBlayout)
        
        # control layout
        control_VBlayout = QtWidgets.QVBoxLayout()
        # ## load
        ## patient index
        control_VBlayout.addWidget(QtWidgets.QWidget())
        control_VBlayout.addWidget(self.patient_index_controller)
        ## table
        table_HBlayout = QtWidgets.QHBoxLayout()
        table_HBlayout.addWidget(self.Cls_button_list)
        table_HBlayout.addWidget(self.bbox_button_list)
        control_VBlayout.addLayout(table_HBlayout)
        
        ## bbox info
        control_VBlayout.addWidget(self.bbox_info_display)
        
        ## output
        control_VBlayout.addWidget(self.output_button)
        control_VBlayout.addWidget(QtWidgets.QWidget())
        
        HBlayout.addLayout(nodule_VBlayout)
        HBlayout.addLayout(bbox_VBlayout)
        HBlayout.addLayout(control_VBlayout)
        
        # shortcuts
        a_shortcut = QtWidgets.QShortcut(QKeySequence('a'), self)
        d_shortcut = QtWidgets.QShortcut(QKeySequence('d'), self)
        left_shortcut = QtWidgets.QShortcut(QKeySequence(Qt.Key.Key_Left), self)
        right_shortcut = QtWidgets.QShortcut(QKeySequence(Qt.Key.Key_Right), self)
        space_shortcut = QtWidgets.QShortcut(QKeySequence(Qt.Key.Key_Space), self)
        
        a_shortcut.activated.connect(self.previous_nodule)
        d_shortcut.activated.connect(self.next_nodule)
        left_shortcut.activated.connect(self.previous_bbox)
        right_shortcut.activated.connect(self.next_bbox)
        space_shortcut.activated.connect(self.confirm)
        
        # func
        self.load_image_direction_button.load_image_direction_clicked.connect(self.load_images_from_direction)
        self.load_bbox_button.load_annotation_clicked.connect(self.load_bboxes_from_file)
        self.Cls_button_list.Cls_button_clicked.connect(self.jump_to_nodule_start_slice)
        self.Cls_button_list.Cls_check_box_clicked.connect(self.change_cls_checked)
        self.bbox_button_list.bbox_button_clicked.connect(self.bbox_index_changed)
        self.bbox_button_list.bbox_check_box_clicked.connect(self.change_bbox_checked)
        self.patient_index_controller.next_clicked.connect(self.next_patient)
        self.patient_index_controller.previous_clicked.connect(self.previous_patient)
        self.patient_index_controller.patient_index_changed.connect(self.patient_index_changed)
        self.next_nodule_button.next_nodule_clicked.connect(self.next_nodule)
        self.previous_nodule_button.previous_nodule_clicked.connect(self.previous_nodule)
        self.next_bbox_button.next_bbox_clicked.connect(self.next_bbox)
        self.previous_bbox_button.previous_bbox_clicked.connect(self.previous_bbox)
        self.output_button.button_clicked.connect(self.output)
        self.bbox_info_display.bbox_type_button_clicked.connect(self.box_info_type_changed)
        self.bbox_info_display.bbox_index_changed.connect(self.change_bbox_info)
    
    def reset_info(self):
        patient_index = self.patient_manager.get_current_index()
        if patient_index is None:
            return
        patient = self.patient_manager.get_patient(patient_index)
        cls_patient = self.Cls_manager.get_patient(self.patient_ids[patient_index])
        if patient is None:
            return
        
        box = patient.get_bbox(self.bbox_index)
        if box is not None:
            bbox_type = box.get_bbox_type()
            if bbox_type == 0:
                if cls_patient is None:
                    return
                self.bbox_info_display.rest_box(box, cls_patient.get_nodule_count())
            elif bbox_type == 1:
                self.bbox_info_display.rest_box(box, patient.get_box_count())
            
    
    def bbox_index_changed(self, box_index):
        self.jump_to_nodule_bbox_start_slice(box_index)
    
    def load_images_from_direction(self, direction_path):
        image_paths = [f'{direction_path}/{patient_id}.npy' for patient_id in self.patient_ids]
        self.patient_manager.add_images_from_direction(self.patient_ids, image_paths)
        patient_index = self.patient_manager.get_current_index()
        if patient_index is None:
            return

        self.Cls_button_list.clear_buttons()
        self.patient_index_controller.clear()
        self.patient_index_controller.addPatients(self.patient_ids)
        self.load_bbox_direction_button.setEnabled(True)
                
        cls_patient = self.Cls_manager.get_patient(self.patient_ids[patient_index])
        if cls_patient is None:
            return
            
    def load_bboxes_from_direction(self, direction_path):
        print('load bboxes')
    
    def load_bboxes_from_file(self, file_path):
        if self.patient_manager is None:
            return
        self.patient_manager.load_bboxes(file_path)
        
        patient_index = self.patient_manager.get_current_index()
        if patient_index is None:
            return
        
        patient = self.patient_manager.get_patient(patient_index)
        if patient is None:
            return
        
        self.player_with_bbox.load_bbox(patient)
        self.bbox_button_list.clear_buttons()
        self.bbox_button_list.add_bboxes(patient)
        
        is_valid = self.bbox_button_list.set_bbox_button_index(self.bbox_index)
        if is_valid:
            self.jump_to_nodule_bbox_start_slice(self.bbox_index)
            self.player_with_bbox.focus_bbox(patient.get_bbox_index(self.bbox_index))
        
    def next_patient(self):
        patient_index = self.patient_manager.next_index()
        if patient_index is None:
            print('patient is not in bbox list')
            return
        else:
            self.patient_index_controller.setPatientIndex(patient_index)            
    
    def previous_patient(self):
        patient_index = self.patient_manager.previous_index()
        if patient_index is None:
            print('patient is not in bbox list')
            return
        else:
            self.patient_index_controller.setPatientIndex(patient_index)
    
    def patient_index_changed(self, index:int):
        self.patient_manager.set_patient_index(index)
        patient = self.patient_manager.get_patient(index)
        cls_patient = self.Cls_manager.get_patient(self.patient_ids[index])
        
        patient_index = self.patient_manager.get_current_index()
        
        if patient_index is None:
            print('patient is not in bbox list')
            return
        
        if cls_patient is None:
            print('patient is not in cls list')
            return
        
        if patient is None:
            return
        
        self.cls_index = 0
        self.Cls_button_list.clear_buttons()
        self.Cls_button_list.add_buttions(self.patient_ids[patient_index], cls_patient)
        cls_index = cls_patient.get_bbox_index(self.cls_index)
        self.bbox_index = 0
        self.reset_info()
        self.bbox_button_list.clear_buttons()
        self.bbox_button_list.add_bboxes(patient)
        
        self.player.load_image(patient, cls_patient)
        
        is_valid = self.Cls_button_list.set_cls_button_index(self.cls_index)
        if is_valid:
            self.player.set_current_scrollbar_index(cls_patient.get_element(self.cls_index).get_start_slice())
            self.display_label1.set_text(cls_index)
        
        self.player_with_bbox.reset_rects()
        self.player_with_bbox.load_image(patient)
        self.player_with_bbox.load_bbox(patient)

        is_valid = self.bbox_button_list.set_bbox_button_index(self.bbox_index)
        if is_valid:
            self.player_with_bbox.set_current_scrollbar_index(patient.get_bbox(self.bbox_index).get_start_slice())
            self.player_with_bbox.focus_bbox(patient.get_bbox_index(self.bbox_index))
            self.display_label2.set_text(patient.get_bbox_index(self.bbox_index))
        
    def jump_to_nodule_start_slice(self, nodule_index:int):
        self.cls_index = nodule_index
        patient_index = self.patient_manager.get_current_index()
        if patient_index is None:
            return
        
        # image_index = self.Cls_manager.get_patient(self.patient_ids[patient_index]).get_elements()[nodule_index].get_start_slice()
        cls_patient = self.Cls_manager.get_patient(self.patient_ids[patient_index])
        if cls_patient is None:
            return
        image_index = cls_patient.get_element(nodule_index).get_start_slice()
        self.player.set_current_scrollbar_index(image_index)
        self.display_label1.set_text(cls_patient.get_bbox_index(nodule_index))
    
    def jump_to_nodule_bbox_start_slice(self, nodule_index:int):
        self.bbox_index = nodule_index
        self.reset_info()
        patient_index = self.patient_manager.get_current_index()
        if patient_index is None:
            return
        patient = self.patient_manager.get_patient(patient_index)
        if patient is None:
            return
        # image_index = patient.get_start_slices()[patient.get_bbox_index(self.bbox_index)]
        image_index = patient.get_bbox(self.bbox_index).get_start_slice()
        self.player_with_bbox.set_current_scrollbar_index(image_index)
        self.player_with_bbox.focus_bbox(patient.get_bbox_index(self.bbox_index))
        self.display_label2.set_text(patient.get_bbox_index(self.bbox_index))
    
    def next_nodule(self):
        if self.Cls_button_list.set_cls_button_index(self.cls_index+1):
            self.cls_index += 1
        self.jump_to_nodule_start_slice(self.cls_index)
    
    def previous_nodule(self):
        if self.Cls_button_list.set_cls_button_index(self.cls_index-1):
            self.cls_index -= 1
        self.jump_to_nodule_start_slice(self.cls_index)
    
    def next_bbox(self):
        if self.bbox_button_list.set_bbox_button_index(self.bbox_index+1):
            self.bbox_index += 1
            
        self.jump_to_nodule_bbox_start_slice(self.bbox_index)
        
    
    def previous_bbox(self):
        if self.bbox_button_list.set_bbox_button_index(self.bbox_index-1):
            self.bbox_index -= 1
        
        self.jump_to_nodule_bbox_start_slice(self.bbox_index)
        
    def confirm(self):
        # patient_index = self.patient_manager.get_current_index()
        # if patient_index is None:
        #     return
        # patient = self.patient_manager.get_patient(patient_index)
        # if patient is None:
        #     return
        # bbox = patient.get_bbox(self.bbox_index)
        
        # if bbox is None:
        #     return
        # bbox.set_nodule_index(self.cls_index)
        # self.bbox_button_list.update_bbox_noodule_index(self.bbox_index, self.cls_index)
        print('confirm')
        
    def output(self):
        output_path = os.path.join('output', '{}.csv'.format(self.output_file_name))
        # if os.path.exists(output_path):
        #     self.nw = widgets.newWindow()
        #     self.nw.show()
        #     x = self.nw.pos().x()
        #     y = self.nw.pos().y()
        #     self.nw.move(x+50, y+50)
        #     self.nw.btn1.clicked.connect(lambda: self.replace_output_path(output_path))
        #     self.nw.btn2.clicked.connect(lambda: self.new_output_path(output_path))
            
        # else:
        #     self.patient_manager.output_match_table(output_path=output_path, patient_ids=self.patient_ids)
        self.patient_manager.output_match_table(output_path=output_path, patient_ids=self.patient_ids)
    
    def new_output_path(self, file_path:str):
        index = 1
        base_file = os.path.basename(file_path)[:-4] + '_{}'.format(index)
        file_path = os.path.join('output', '{}.csv'.format(base_file))
        while os.path.exists(file_path):
            index += 1
            base_file_split = base_file.split('_')
            base_file = base_file_split[0]
            for file_split in base_file_split[1:-1]:
                base_file += '_{}'.format(file_split)
            base_file += '_{}'.format(index)
            file_path = os.path.join('output', '{}.csv'.format(base_file))
            
        self.patient_manager.output_match_table(output_path=file_path, patient_ids=self.patient_ids)
        self.nw.close()
    
    def replace_output_path(self, file_path:str):
        self.patient_manager.output_match_table(output_path=file_path, patient_ids=self.patient_ids)
        self.nw.close()
        
        
    def change_bbox_checked(self, is_checked:bool, bbox_id:int, patietn_id:str):
        patient = self.patient_manager.get_patient_from_id(patietn_id)
        if patient is None:
            return
        bbox = patient.get_bbox(bbox_id)
        if bbox is None:
            return
        bbox.set_checked(is_checked)
    
    def change_cls_checked(self, is_checked:bool, cls_index:int, patient_id:str):
        cls_patient = self.Cls_manager.get_patient(patient_id)
        if cls_patient is None:
            return
        cls_element = cls_patient.get_element(cls_index)
        cls_element.set_checked(is_checked)
    
    def change_bbox_id_nodule_id(self, patient_id, bbox_index, nodule_index):
        patient = self.patient_manager.get_patient_from_id(patient_id)
        bbox = patient.get_bbox(bbox_index)
        if bbox is None:
            return
        bbox.set_nodule_index(nodule_index)
    
    def change_bbox_info(self, item_index, type):
        patient_index = self.patient_manager.get_current_index()
        if patient_index is None:
            return
        
        patient = self.patient_manager.get_patient(patient_index)
        if patient is None:
            return
        
        bbox = patient.get_bbox(self.bbox_index)
        if bbox is None:
            return     
        if type == -1:
            return
        
        if type == 0 and item_index!= -1:
            bbox.set_nodule_index(item_index)
        elif type == 1 and item_index != -1:
            bbox.set_group(item_index)
    
    def box_info_type_changed(self, type:int):
        patietn_intex = self.patient_manager.get_current_index()
        if patietn_intex is None:
            return

        patient = self.patient_manager.get_patient(patietn_intex)
        if patient is None:
            return
        
        cls_patient = self.Cls_manager.get_patient(self.patient_ids[patietn_intex])
        box = patient.get_bbox(self.bbox_index)
        if box is None:
            return
        box.set_box_type(type)
        if type == 0:
            if cls_patient is None:
                return
            self.bbox_info_display.add_box_items(cls_patient.get_nodule_count(), type='nodule', index=box.get_nodule_index())
        elif type == 1:
            if patient is None:
                return
            self.bbox_info_display.add_box_items(patient.get_box_count(), type='bbox', index=box.get_box_group())
        elif type == 2:
            print('Delete')
        elif type == 3:
            print('Other')
        else:
            print('Error')

    
if __name__ == '__main__':
    import sys
    parser = argparse.ArgumentParser()
    parser.add_argument('--annotation_file', type=str, default = '')
    parser.add_argument('--bbox_annotation_file', type = str, default='')
    parser.add_argument('--image_root', type=str, default = '')
    parser.add_argument('--patient_ids_file', type = str, default='')
    parser.add_argument('--output_file_name', type = str, default='')
    parser.add_argument('--mask_root', type = str, default='')
    
    args = parser.parse_args()
    app = QtWidgets.QApplication(sys.argv)
    controller = Controller(args)
    controller.setGeometry(500, 300, 1200, 600)
    controller.showMaximized()
    sys.exit(app.exec_())