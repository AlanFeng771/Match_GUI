from PyQt5 import QtWidgets
import widgets
import Manager
import os
class Controller(QtWidgets.QWidget):
    def __init__(self):
        super(Controller, self).__init__()
        self.patient_manager = Manager.PatientManager()
        self.patient_ids = []
        self.initWidget()
        
    def initWidget(self):
        # widgets
        self.player = widgets.PlayerView()
        self.load_image_button = widgets.LoadImageButton()
        self.load_bbox_button = widgets.LoadAnnotationButton()
        self.load_image_direction_button = widgets.LoadImageDirectionButton()
        self.load_bbox_direction_button = widgets.LoadAnnotationsDirectionButton()
        # layout
        VBlayout = QtWidgets.QVBoxLayout(self)
        VBlayout.addWidget(self.player)
        VBlayout.addWidget(self.load_image_direction_button)
        VBlayout.addWidget(self.load_bbox_direction_button)
        
        # func
        self.load_image_button.load_image_clicked.connect(self.load_image)
        self.load_bbox_button.load_annotation_clicked.connect(self.load_bbox)
        self.load_image_direction_button.load_image_direction_clicked.connect(self.load_images_from_direction)
        self.load_bbox_direction_button.load_annotation_direction_clicked.connect(self.load_bboxes_from_direction)
        
    def load_image(self, image_path):
        patient_id = image_path.split('/')[-1].split('.')[0]
        self.patient_manager.add_image_from_file(patient_id, image_path)
        self.player.load_image(self.patient_manager.get_patient(patient_id))

    def load_bbox(self, bbox_path):
        patient_id = bbox_path.split('/')[-1].split('.')[0]
        self.patient_manager.add_bbox_from_file(patient_id, bbox_path)
        self.player.load_bbox(self.patient_manager.get_patient(patient_id))
        
    def load_images_from_direction(self, direction_path):
        patient_ids = [path.split('/')[-1].split('.')[0] for path in os.listdir(direction_path)]
        image_paths = [f'{direction_path}/{patient_id}.npy' for patient_id in patient_ids]
        self.patient_manager.add_images_from_direction(patient_ids, image_paths)
        self.player.load_image(self.patient_manager.get_patient(patient_ids[0]))
    
    def load_bboxes_from_direction(self, direction_path):
        patient_ids = [path.split('/')[-1].split('.')[0] for path in os.listdir(direction_path)]
        bbox_paths = [f'{direction_path}/{patient_id}.json' for patient_id in patient_ids]
        self.patient_manager.add_bboxes_from_direction(patient_ids, bbox_paths)
        self.player.load_bbox(self.patient_manager.get_patient(patient_ids[0]))
        
if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)
    controller = Controller()
    controller.setGeometry(500, 300, 1200, 600)
    controller.showMaximized()
    sys.exit(app.exec_())
        
