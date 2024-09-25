import re
from PyQt5 import QtCore, QtGui, QtWidgets 
import numpy as np
import cv2
import json
import Manager
class PhotoViewer(QtWidgets.QGraphicsView):
    photoClicked = QtCore.pyqtSignal(QtCore.QPoint)
    def __init__(self, parent):
        super(PhotoViewer, self).__init__(parent)
        self._zoom = 0
        self._empty = True
        self._scene = QtWidgets.QGraphicsScene(self)
        self._photo = QtWidgets.QGraphicsPixmapItem()
        self._scene.addItem(self._photo)
        self.setScene(self._scene)
        self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setBackgroundBrush(QtGui.QBrush(QtGui.QColor(30, 30, 30)))
        self.setFrameShape(QtWidgets.QFrame.NoFrame)

    def hasPhoto(self):
        return not self._empty

    def fitInView(self, scale=True):
        rect = QtCore.QRectF(self._photo.pixmap().rect())
        if not rect.isNull():
            self.setSceneRect(rect)
            if self.hasPhoto():
                unity = self.transform().mapRect(QtCore.QRectF(0, 0, 1, 1))
                self.scale(1 / unity.width(), 1 / unity.height())
                viewrect = self.viewport().rect()
                scenerect = self.transform().mapRect(rect)
                factor = min(viewrect.width() / scenerect.width(),
                             viewrect.height() / scenerect.height())
                self.scale(factor, factor)
            self._zoom = 0
    
    def setPhoto(self, pixmap=None):
        if pixmap and not pixmap.isNull():
            self._empty = False
            self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
            self._photo.setPixmap(pixmap)
            self._photo.setTransformationMode(QtCore.Qt.SmoothTransformation)
        else:
            self._empty = True
            self.setDragMode(QtWidgets.QGraphicsView.NoDrag)
            self._photo.setPixmap(QtGui.QPixmap())
    
    def add_item(self, item: QtWidgets.QGraphicsItem):
        self._scene.addItem(item)
    
    def remove_item(self, item: QtWidgets.QGraphicsItem):
        self._scene.removeItem(item)
      
    def wheelEvent(self, event):
        modifiers = event.modifiers()
        if self.hasPhoto():
            if modifiers == QtCore.Qt.ControlModifier:
                if event.angleDelta().y() > 0:
                    factor = 1.25
                    self._zoom += 1
                else:
                    factor = 0.75
                    self._zoom -= 1
                if self._zoom > 0:
                    self.scale(factor, factor)
                elif self._zoom == 0:
                    self.fitInView()
                else:
                    self._zoom = 0

    def toggleDragMode(self):
        if self.dragMode() == QtWidgets.QGraphicsView.ScrollHandDrag:
            self.setDragMode(QtWidgets.QGraphicsView.NoDrag)
        elif not self._photo.pixmap().isNull():
            self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)

    def mousePressEvent(self, event):
        if self._photo.isUnderMouse():
            self.photoClicked.emit(self.mapToScene(event.pos()).toPoint())
        super(PhotoViewer, self).mousePressEvent(event)


class PlayerView(QtWidgets.QWidget):
    def __init__(self):
        super(PlayerView, self).__init__()
        self.images = None
        self.rects = []
        self.initWidget()

    def initWidget(self):
        # PhotoViewer
        self.viewer = PhotoViewer(self)

        # Scroll bar
        self.scrollBar = QtWidgets.QScrollBar(QtCore.Qt.Horizontal)
        self.scrollBar.setMinimum(0)
        self.scrollBar.setMaximum(0)  # 初始設置為0，因為還沒有圖片加載
        self.scrollBar.valueChanged.connect(self.show)

        # layout
        VBlayout = QtWidgets.QVBoxLayout(self)
        HBlayout = QtWidgets.QHBoxLayout()
        HBlayout.addWidget(self.scrollBar, 10)
        VBlayout.addWidget(self.viewer)
        VBlayout.addLayout(HBlayout)
        self.viewer.installEventFilter(self)
    
    def _numpytoPixmap(self, image):
        image =  cv2.cvtColor(image.astype(np.uint8), cv2.COLOR_GRAY2RGB)
        h,w,ch = image.shape
        image = QtGui.QImage(image, w, h, w*ch, QtGui.QImage.Format_RGB888)
        pix = QtGui.QPixmap(image)
        return pix
    
    def load_image(self, patient:Manager.Patient):
        self.images = patient.get_images()
        self.image_index = 0
        self.scrollBar.setMaximum(self.images.shape[2]-1)
        self.show_image()
    
    def load_bbox(self, patient:Manager.Patient):
        bboxes = patient.get_bboxes()
        for bbox in bboxes:
            left_top, right_bottom = bbox.get_annotation() # left_top = [y_min, x_min, z_min], right_bottom = [y_max, x_max, z_max]
            width = (right_bottom[1] - left_top[1])+1
            height = (right_bottom[0] - left_top[0])+1
            center_x = (left_top[1] + right_bottom[1]) / 2
            center_y = (left_top[0] + right_bottom[0]) / 2
            rect = CustomRectItem(size=(width, height), position=QtCore.QPointF(center_x, center_y), slices=[left_top[2], right_bottom[2]])
            self.rects.append(rect)
            self.viewer.add_item(rect)
    
    def show_image(self, image_index=0):
        # init
        if self.images is not None:  
            self.viewer.setPhoto(self._numpytoPixmap(self.images[:,:,image_index]))
            self.viewer.fitInView()
        self.image_index = image_index
    
    def show_bbox(self, image_index=0):
        if len(self.rects) > 0:
            for rect in self.rects:
                if rect.is_valid(image_index):
                    rect.show()
                else:
                    rect.hide()
    
    def reset_bbox_color(self):
        if len(self.rects) > 0:
            for rect in self.rects:
                rect.setBorderColor(QtCore.Qt.red)
    
    def show(self, image_index:int=0):
        self.show_image(image_index)
        self.show_bbox(image_index)
    
    def show_and_focus_bbox(self, index:int, image_index:int=0):
        print('focus on bbox {}'.format(index))
        self.reset_bbox_color()
        rect = self.rects[index]
        rect.setBorderColor(QtCore.Qt.green)
        
        self.show(image_index)
        
        
    def reset_rects(self):
        # init
        for rect in self.rects:
            self.viewer.remove_item(rect)

        del self.rects
        # init bbox annotation
        self.rects = []
 
class PatientIndexBox(QtWidgets.QComboBox):
    def __init__(self):
        super(PatientIndexBox, self).__init__()
        self.setFixedSize(QtCore.QSize(200, 50))
        self.setMaxVisibleItems(9999)

    def addPatient(self, patient_id:str):
        self.addItem(patient_id)
        self.update()
    
    def addPatients(self, patient_ids:list):
        for patient_id in patient_ids:
            self.addPatient(patient_id)
    
    def setPatientIndex(self, index:int):
        self.setCurrentIndex(index)

class NextPatientButton(QtWidgets.QPushButton):
    next_clicked = QtCore.pyqtSignal()
    def __init__(self, parent=None):
        super(NextPatientButton, self).__init__(parent)
        self.setText('Next')
        self.setFixedSize(QtCore.QSize(150, 50))

        
class PreviousPatientButton(QtWidgets.QPushButton):
    def __init__(self, parent=None):
        super(PreviousPatientButton, self).__init__(parent)
        self.setText('Previous')
        self.setFixedSize(QtCore.QSize(150, 50))

class PatientControlWidget(QtWidgets.QWidget):
    next_clicked = QtCore.pyqtSignal()
    previous_clicked = QtCore.pyqtSignal()
    patient_index_changed = QtCore.pyqtSignal(int)
    def __init__(self):
        super(PatientControlWidget, self).__init__()
        self.initWidget()
    
    def initWidget(self):
        self.patient_index_box = PatientIndexBox()
        self.next_button = NextPatientButton()
        self.previous_button = PreviousPatientButton()
        
        layout = QtWidgets.QHBoxLayout(self)
        layout.setAlignment(QtCore.Qt.AlignTop)
        
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.previous_button)
        layout.addWidget(self.patient_index_box)
        layout.addWidget(self.next_button)
        
        self.next_button.clicked.connect(self.next_clicked.emit)
        self.previous_button.clicked.connect(self.previous_clicked.emit)
        self.patient_index_box.currentIndexChanged.connect(self.patient_index_changed.emit)
    
    def setPatientIndex(self, index:int):
        self.patient_index_box.setPatientIndex(index)
    
    def addPatients(self, patient_ids:list):
        self.patient_index_box.addPatients(patient_ids)
    
    def clear(self):
        self.patient_index_box.clear()

    
class CustomRectItem(QtWidgets.QGraphicsItem):
    def __init__(self, size:tuple, position:QtCore.QRectF, slices:list, border_color=QtCore.Qt.red, parent=None):
        '''
        size: (width, height)
        position: QPointF (center_x, center_y)
        slices: [z_min, z_max]
        '''
        super().__init__(parent)
        self.size = size
        self.position = position
        self.border_color = border_color
        self.slices = slices
        self.is_visible = False

    def boundingRect(self):
        return QtCore.QRectF(self.position.x()-self.size[0]/2, self.position.y()-self.size[1]/2, self.size[0], self.size[1])

    def paint(self, painter, option, widget=None):
        painter.setPen(self.border_color)
        painter.drawRect(self.position.x()-self.size[0]/2, self.position.y()-self.size[1]/2, self.size[0], self.size[1])

    def setBorderColor(self, color):
        self.border_color = color
        self.update()
    
    def setRect(self, position):
        self.position = position
        self.update()
    
    def setVisible(self, visible):
        self.is_visible = visible
    
    def getVisible(self):
        return self.is_visible
    
    def is_valid(self, slice):
        if slice >= self.slices[0] and slice < self.slices[1]:
            return True
        else:
            return False
        
class LoadImageButton(QtWidgets.QPushButton):
    load_image_clicked = QtCore.pyqtSignal(str)
    def __init__(self, parent=None):
        super(LoadImageButton, self).__init__(parent)
        self.setText('Load image')
        self.clicked.connect(self.load_image)
    
    def load_image(self):
        filename, filetype = QtWidgets.QFileDialog.getOpenFileName(self, "Open file", "./")
        if filename != '':
            self.load_image_clicked.emit(filename)

class LoadAnnotationButton(QtWidgets.QPushButton):
    load_annotation_clicked = QtCore.pyqtSignal(str)
    def __init__(self, parent=None):
        super(LoadAnnotationButton, self).__init__(parent)
        self.setText('Load annotation')
        self.clicked.connect(self.load_annotation)
    
    def load_annotation(self):
        filename, filetype = QtWidgets.QFileDialog.getOpenFileName(self, "Open file", "./")
        if filename != '':
            self.load_annotation_clicked.emit(filename)

class LoadImageDirectionButton(QtWidgets.QPushButton):
    load_image_direction_clicked = QtCore.pyqtSignal(str)
    def __init__(self, parent=None):
        super(LoadImageDirectionButton, self).__init__(parent)
        self.setText('Load image direction')
        self.setFixedSize(QtCore.QSize(260, 50))
        self.clicked.connect(self.load_image_direction)
    
    def load_image_direction(self):
        direction_path = QtWidgets.QFileDialog.getExistingDirectory(self, "Open file", "./")
        if direction_path != '':
            self.load_image_direction_clicked.emit(direction_path)
        
class LoadAnnotationsDirectionButton(QtWidgets.QPushButton):
    load_annotation_direction_clicked = QtCore.pyqtSignal(str)
    def __init__(self, parent=None):
        super(LoadAnnotationsDirectionButton, self).__init__(parent)
        self.setText('Load annotation direction')
        self.setFixedSize(QtCore.QSize(260, 50))
        self.clicked.connect(self.load_annotation_direction)
        self.setEnabled(False)
    
    def load_annotation_direction(self):
        direction_path = QtWidgets.QFileDialog.getExistingDirectory(self, "Open file", "./")
        if direction_path != '':
            self.load_annotation_direction_clicked.emit(direction_path)

class ClsButton(QtWidgets.QPushButton):
    Cls_button_clicked = QtCore.pyqtSignal(int)
    def __init__(self, text:str, index:int, parent=None):
        super(ClsButton, self).__init__(parent)
        self.setText(text)
        self.index = index
        self.clicked.connect(lambda: self.Cls_button_clicked.emit(self.index))
        self.setCheckable(True)
    
    def set_checked(self, checked:bool):
        self.setChecked(checked)

class ButtonListWindow(QtWidgets.QWidget):
    Cls_button_clicked = QtCore.pyqtSignal(int)
    def __init__(self):
        super().__init__()
        self.setFixedSize(QtCore.QSize(250, 400))
        self.Cls_buttons = []
        self.initWidget()

    def initWidget(self):
        self.setWindowTitle('Dynamic Button List with Scroll')

        # 創建一個總布局
        layout = QtWidgets.QVBoxLayout(self)

        # 創建一個 QScrollArea，來管理滾動
        scroll_area = QtWidgets.QScrollArea(self)
        scroll_area.setWidgetResizable(True)  # 自適應大小

        # 創建一個內部窗口用來承載按鈕
        button_container = QtWidgets.QWidget()
        self.button_layout = QtWidgets.QFormLayout(button_container)

        # 設置 scroll_area 的主窗口為按鈕容器
        scroll_area.setWidget(button_container)

        # 把 scroll_area 添加到主 layout
        layout.addWidget(scroll_area)

    
    def add_button(self, text:str, index:int):
        button = ClsButton(text, index, self)
        button.Cls_button_clicked.connect(self.cls_button_clicked)
        self.Cls_buttons.append(button)
        self.button_layout.addRow(button)
    
    def add_buttions(self, patient:Manager.PatientClsElement):
        del self.Cls_buttons
        self.Cls_buttons = []
        cls_elements = patient.get_elements()  
        for index, cls_element in enumerate(cls_elements):
            self.add_button('Nodule {},slice:{}, cls:{}'.format(index, cls_element.get_start_slice(), cls_element.get_category()), index)
    
    def clear_buttons(self):
        """清除當前所有按鈕"""
        while self.button_layout.count():
            item = self.button_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
    
    def set_checked(self, index:int, checked:bool):
        self.Cls_buttons[index].set_checked(checked)
    
    def reset_buttons(self):
        for button in self.Cls_buttons:
            button.set_checked(False)
    
    def cls_button_clicked(self, index:int):
        self.reset_buttons()
        self.Cls_buttons[index].set_checked(True)
        self.Cls_button_clicked.emit(index)
    
    def set_cls_button_index(self, index:int)->bool:
        self.reset_buttons()
        if index >= 0 and index < len(self.Cls_buttons):
            self.Cls_buttons[index].set_checked(True)
            return True
        elif index == len(self.Cls_buttons):
            self.Cls_buttons[len(self.Cls_buttons)-1].set_checked(True)
        elif index < 0:
            self.Cls_buttons[0].set_checked(True)
        
        return False
        
        
            
        

class BboxButton(QtWidgets.QPushButton):
    bbox_button_clicked = QtCore.pyqtSignal(int)
    def __init__(self, text:str, index:int, parent=None):
        super(BboxButton, self).__init__(parent)
        self.setText(text)
        self.index = index
        self.setCheckable(True)
        self.clicked.connect(lambda: self.bbox_button_clicked.emit(self.index))

class BboxNoduleBox(QtWidgets.QComboBox):
    def __init__(self, nodule_count:int):
        super(BboxNoduleBox, self).__init__()
        self.setFixedSize(QtCore.QSize(80, 20))
        self.setMaxVisibleItems(9999)
        self.addNodules(nodule_count)

    def addNodule(self, nodule_index:int):
        self.addItem('nodule {}'.format(nodule_index))
        self.update()
    
    def addNodules(self, nodule_count:int):
        for nodule_index in range(nodule_count):
            self.addNodule(nodule_index)
    
    def setPatientIndex(self, index:int):
        self.setCurrentIndex(index)
        
class BboxItem(QtWidgets.QWidget):
    bbox_button_clicked = QtCore.pyqtSignal(int)
    def __init__(self, text:str, index:int, nodule_count:int, nodule_index:int, parent=None):
        super(BboxItem, self).__init__(parent)
        self.bbox = BboxButton(text, index, self)
        self.nodule_box = BboxNoduleBox(nodule_count)
        self.set_nodule_index(nodule_index)
        self.bbox.clicked.connect(lambda: self.bbox_button_clicked.emit(index))
        
        
        layout = QtWidgets.QHBoxLayout(self)
        layout.addWidget(self.bbox)
        layout.addWidget(self.nodule_box)
    
    def set_checked(self, checked:bool):
        self.bbox.setChecked(checked)
    
    def set_nodule_index(self, index:int):
        self.nodule_box.setPatientIndex(index)
        

class BboxesButtonListView(QtWidgets.QWidget):
    bbox_button_clicked = QtCore.pyqtSignal(int)
    def __init__(self):
        super().__init__()
        self.setFixedSize(QtCore.QSize(250, 400))
        self.bbox_buttons = []
        self.initWidget()

    def initWidget(self):
        self.setWindowTitle('Dynamic Button List with Scroll')

        # 創建一個總布局
        layout = QtWidgets.QVBoxLayout(self)

        # 創建一個 QScrollArea，來管理滾動
        scroll_area = QtWidgets.QScrollArea(self)
        scroll_area.setWidgetResizable(True)  # 自適應大小

        # 創建一個內部窗口用來承載按鈕
        button_container = QtWidgets.QWidget()
        self.button_layout = QtWidgets.QFormLayout(button_container)

        # 設置 scroll_area 的主窗口為按鈕容器
        scroll_area.setWidget(button_container)

        # 把 scroll_area 添加到主 layout
        layout.addWidget(scroll_area)

    
    def add_bbox(self, text:str, index:int, nodule_count:int, nodule_index:int):
        button = BboxItem(text, index, nodule_count, nodule_index, self)
        button.bbox_button_clicked.connect(self.bbox_clickd)
        self.bbox_buttons.append(button)
        self.button_layout.addRow(button)
    
    def add_bboxes(self, patient:Manager.Patient, patient_cls_element:Manager.PatientClsElement):
        del self.bbox_buttons
        self.bbox_buttons = []
        
        bboxes = patient.get_bboxes()
        for index, bbox in enumerate(bboxes):
            self.add_bbox('Bbox {}, slice:{}'.format(index, bbox.get_start_slice()), index, patient_cls_element.get_nodule_count(), bbox.get_nodule_index())
    
    def clear_buttons(self):
        """清除當前所有按鈕"""
        while self.button_layout.count():
            item = self.button_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        
    def reset_buttons(self):
        for bbox in self.bbox_buttons:
            bbox.set_checked(False)
            
    def set_checked(self, index:int, checked:bool):
        self.bbox_buttons[index].set_checked(checked)
    
    def bbox_clickd(self, index:int):
        self.reset_buttons()
        self.bbox_buttons[index].set_checked(True)
        self.bbox_button_clicked.emit(index)
    

class NextNoduleButton(QtWidgets.QPushButton):
    next_nodule_clicked = QtCore.pyqtSignal()
    def __init__(self, parent=None):
        super(NextNoduleButton, self).__init__(parent)
        self.setText('Next Nodule')
        self.clicked.connect(self.next_nodule_clicked.emit)

    
class PreviousNoduleButton(QtWidgets.QPushButton):
    previous_nodule_clicked = QtCore.pyqtSignal()
    def __init__(self, parent=None):
        super(PreviousNoduleButton, self).__init__(parent)
        self.setText('Previous Nodule')
        self.clicked.connect(self.previous_nodule_clicked.emit)