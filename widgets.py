from operator import is_
from PyQt5 import QtCore, QtGui, QtWidgets 
import numpy as np
import cv2
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
        self.current_contour_item = None
        self.setScene(self._scene)
        self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setBackgroundBrush(QtGui.QBrush(QtGui.QColor(30, 30, 30)))
        self.setFrameShape(QtWidgets.QFrame.NoFrame)

    def hasPhoto(self):
        return not self._empty

    def fit_in_view(self):
        rect = QtCore.QRectF(self._photo.pixmap().rect())
        if not rect.isNull():
            self.setSceneRect(rect)
            if self.hasPhoto():
                unity = self.transform().mapRect(QtCore.QRectF(0, 0, 1, 1))
                self.scale(1 / unity.width(), 1 / unity.height())
                viewport = self.viewport()
                if viewport is not None:
                    viewrect = viewport.rect()
                else:
                    viewrect = QtCore.QRect()
                scenerect = self.transform().mapRect(rect)
                factor = min(viewrect.width() / scenerect.width(),
                             viewrect.height() / scenerect.height())
                self.scale(factor, factor)
            self._zoom = 0
    
    
    def setPhoto(self, pixmap=None, contour_item=None):
        if pixmap and not pixmap.isNull():
            self._empty = False
            self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
            self._photo.setPixmap(pixmap)
            self._photo.setTransformationMode(QtCore.Qt.TransformationMode.SmoothTransformation)
            if contour_item is not None:
                if self.current_contour_item is not None:
                    self._scene.removeItem(self.current_contour_item)
                self.current_contour_item = contour_item
                self._scene.addItem(contour_item)
        else:
            self._empty = True
            self.setDragMode(QtWidgets.QGraphicsView.NoDrag)
            self._photo.setPixmap(QtGui.QPixmap())

    def add_item(self, item: QtWidgets.QGraphicsItem):
        self._scene.addItem(item)
    
    def remove_item(self, item: QtWidgets.QGraphicsItem):
        self._scene.removeItem(item)
      
    def wheelEvent(self, event):
        if event is None:
            return
        modifiers = event.modifiers()
        if self.hasPhoto():
            if modifiers == QtCore.Qt.KeyboardModifier.ControlModifier:
                if event.angleDelta().y() > 0:
                    factor = 1.25
                    self._zoom += 1
                else:
                    factor = 0.75
                    self._zoom -= 1
                if self._zoom > 0:
                    self.scale(factor, factor)
                elif self._zoom == 0:
                    self.fit_in_view()
                else:
                    self._zoom = 0

    def toggleDragMode(self):
        if self.dragMode() == QtWidgets.QGraphicsView.ScrollHandDrag:
            self.setDragMode(QtWidgets.QGraphicsView.NoDrag)
        elif not self._photo.pixmap().isNull():
            self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)

    # def mousePressEvent(self, event):
    #     if self._photo.isUnderMouse():
    #         if event is None:
    #             return
    #         point = self.mapToScene(event.pos().toPoint())
    #         if point is None:
    #             return
    #         self.photoClicked.emit(point.toPoint())
    #     super(PhotoViewer, self).mousePressEvent(event)

class PlayerView(QtWidgets.QWidget):
    def __init__(self):
        super(PlayerView, self).__init__()
        self.images = None
        self.num_of_images = 0
        self.contour_images = None
        self.setFixedSize(QtCore.QSize(512, 512))
        self.initWidget()
        
    def initWidget(self):
        label_font = QtGui.QFont()
        label_font.setFamily('Verdana')
        label_font.setPointSize(12)
        label_font.setBold(True)  
        # PhotoViewer
        self.viewer = PhotoViewer(self)

        # Scroll bar
        self.scrollBar = QtWidgets.QScrollBar(QtCore.Qt.Orientation.Horizontal)
        self.scrollBar.setMinimum(0)
        self.scrollBar.setMaximum(0)  # 初始設置為0，因為還沒有圖片加載
        self.scrollBar.valueChanged.connect(self.show)

        # Text
        self.sliceText = QtWidgets.QLineEdit('0')
        self.sliceText.setFont(label_font)
        self.sliceText.setFixedSize(QtCore.QSize(50, 30))
        self.maxSliceText = QtWidgets.QLabel('/')
        self.maxSliceText.setFont(label_font)
        self.maxSliceText.setFixedSize(QtCore.QSize(50, 30))
        
        # layout
        VBlayout = QtWidgets.QVBoxLayout(self)
        HBlayout = QtWidgets.QHBoxLayout()
        HBlayout.addWidget(self.scrollBar, 10)
        HBlayout.addWidget(self.sliceText, 1)
        HBlayout.addWidget(self.maxSliceText, 1)
        VBlayout.addWidget(self.viewer)
        VBlayout.addLayout(HBlayout)
        self.viewer.installEventFilter(self)
    
    def _numpytoPixmap(self, image):
        image =  cv2.cvtColor(image.astype(np.uint8), cv2.COLOR_GRAY2RGB)
        h,w,ch = image.shape
        image = QtGui.QImage(image, w, h, w*ch, QtGui.QImage.Format_RGB888)
        pix = QtGui.QPixmap(image)
        return pix
    
    def _generate_contour_item(self, contour_image):
        height, width = contour_image.shape
        contour_image = np.array(contour_image, dtype=np.uint8)

            
        contour_pixmap = QtGui.QPixmap(width, height)
        transparent_color = QtGui.QColor(0, 0, 0, 0)
        contour_pixmap.fill(transparent_color)
        painter = QtGui.QPainter(contour_pixmap)
        
        if np.max(contour_image) == 0:
            print('invalid contour image')
            painter.end()
            return QtWidgets.QGraphicsPixmapItem(contour_pixmap)
        
        y_index, x_index = np.where(contour_image == 255)
        for y, x in zip(y_index, x_index):
            painter.setPen(QtGui.QColor(255, 0, 0, contour_image[y, x]))  # Red color for edges
            painter.drawPoint(x, y)
        painter.end()
        contour_item = QtWidgets.QGraphicsPixmapItem(contour_pixmap)
        
        return contour_item
        
    def load_image(self, patient:Manager.Patient, patient_cls_element:Manager.PatientClsElement):
        self.images = patient.get_images()
        if self.images is None:
            return
        self.image_index = 0
        self.num_of_images = self.images.shape[2]
        self.contour_images = patient_cls_element.get_contour_images()
        self.scrollBar.setMaximum(self.images.shape[2]-1)
        self.show_image()
    
    def show_image(self, image_index=0):
        # init
        if self.contour_images is not None:
            contour_item = self._generate_contour_item(self.contour_images[:,:,image_index])
        else:
            contour_item = None
        if self.images is not None: 
            self.viewer.setPhoto(self._numpytoPixmap(self.images[:,:,image_index]), contour_item)
            # self.viewer.fit_in_view()
        self.image_index = image_index
    
    
    def show(self, image_index:int=0):
        self.sliceText.setText(str(image_index))
        self.show_image(image_index)
    
    def set_current_scrollbar_index(self, value:int):
        self.scrollBar.setValue(value)
    
    def reset_rects(self):
        # init
        for rect in self.rects:
            self.viewer.remove_item(rect)

        del self.rects
        # init bbox annotation
        self.rects = []
    
    def wheelEvent(self, event):
        modifiers = event.modifiers()
        if modifiers == QtCore.Qt.NoModifier:
            if event.angleDelta().y() > 0:
                action = 'next'
            else:
                action = 'previous'

            self.scroll_image(action)
            
    def scroll_image(self, type):
        if type == 'previous':
            if self.image_index > 0:
                currrent_image_index = self.image_index
                self.scrollBar.setValue(currrent_image_index-1)
        elif type == 'next':
            if self.image_index < self.num_of_images-1:
                currrent_image_index = self.image_index
                self.scrollBar.setValue(currrent_image_index+1) 

class PlayerWithRectView(QtWidgets.QWidget):
    def __init__(self):
        super(PlayerWithRectView, self).__init__()
        self.images = None
        self.num_of_images = 0
        self.rects = []
        self.setFixedSize(QtCore.QSize(512, 512))
        self.initWidget()

    def initWidget(self):
        label_font = QtGui.QFont()
        label_font.setFamily('Verdana')
        label_font.setPointSize(12)
        label_font.setBold(True)  
        # PhotoViewer
        self.viewer = PhotoViewer(self)

        # Scroll bar
        self.scrollBar = QtWidgets.QScrollBar(QtCore.Qt.Orientation.Horizontal)
        self.scrollBar.setMinimum(0)
        self.scrollBar.setMaximum(0)  # 初始設置為0，因為還沒有圖片加載
        self.scrollBar.valueChanged.connect(self.show)

        # Text
        self.sliceText = QtWidgets.QLineEdit('0')
        self.sliceText.setFont(label_font)
        self.sliceText.setFixedSize(QtCore.QSize(50, 30))
        self.maxSliceText = QtWidgets.QLabel('/')
        self.maxSliceText.setFont(label_font)
        self.maxSliceText.setFixedSize(QtCore.QSize(50, 30))
        
        # layout
        VBlayout = QtWidgets.QVBoxLayout(self)
        HBlayout = QtWidgets.QHBoxLayout()
        HBlayout.addWidget(self.scrollBar, 10)
        HBlayout.addWidget(self.sliceText, 1)
        HBlayout.addWidget(self.maxSliceText, 1)
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
        if self.images is None:
            return
        self.image_index = 0
        self.num_of_images = self.images.shape[2]
        self.scrollBar.setMaximum(self.images.shape[2]-1)
        self.show_image()
    
    def load_bbox(self, patient:Manager.Patient):
        bboxes = patient.get_bboxes()
        for bbox in bboxes:
            center_x, center_y, center_z, width, height, depth = bbox.get_annotation()
            rect = CustomRectItem(size=(width, height), position=QtCore.QPointF(center_x, center_y), slices=[int(center_z-depth/2), int(center_z+depth/2)])
            self.rects.append(rect)
            self.viewer.add_item(rect)
    
    def show_image(self, image_index=0):
        # init
        if self.images is not None:  
            self.viewer.setPhoto(self._numpytoPixmap(self.images[:,:,image_index]))
            # self.viewer.fitInView()
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
                rect.setBorderColor(QtCore.Qt.GlobalColor.red)
    
    def show(self, image_index:int=0):
        self.sliceText.setText(str(image_index))
        self.show_image(image_index)
        self.show_bbox(image_index)
    
    def focus_bbox(self, index:int):
        self.reset_bbox_color()
        rect = self.rects[index]
        rect.setBorderColor(QtCore.Qt.GlobalColor.green)
        # print('focus bbox')
    
    def set_current_scrollbar_index(self, value:int):
        self.scrollBar.setValue(value)
        
    def reset_rects(self):
        # init
        for rect in self.rects:
            self.viewer.remove_item(rect)

        del self.rects
        # init bbox annotation
        self.rects = []
    
    def wheelEvent(self, event):
        modifiers = event.modifiers()
        if modifiers == QtCore.Qt.NoModifier:
            if event.angleDelta().y() > 0:
                action = 'next'
            else:
                action = 'previous'

            self.scroll_image(action)

    def scroll_image(self, type):
        if type == 'previous':
            if self.image_index > 0:
                currrent_image_index = self.image_index
                self.scrollBar.setValue(currrent_image_index-1)
        elif type == 'next':
            if self.image_index < self.num_of_images-1:
                currrent_image_index = self.image_index
                self.scrollBar.setValue(currrent_image_index+1) 
 
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
        layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        
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
    def __init__(self, size:tuple, position:QtCore.QRectF, slices:list, border_color=QtCore.Qt.GlobalColor.red, parent=None):
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
        if painter is None:
            return
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
        self.setFixedSize(QtCore.QSize(260, 50))
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

class ClsBboxCheckBox(QtWidgets.QCheckBox):
    bbox_check_box_clicked = QtCore.pyqtSignal(bool)
    def __init__(self, parent=None):
        super(ClsBboxCheckBox, self).__init__(parent)
        self.clicked.connect(lambda: self.bbox_check_box_clicked.emit(self.isChecked()))
        
class ClsBboxItem(QtWidgets.QWidget):
    Cls_button_clicked = QtCore.pyqtSignal(int)
    Cls_check_box_clicked = QtCore.pyqtSignal(bool, int) # checked, bbox_index

    def __init__(self, text:str, index:int, start_slice:int, nodule_index:int, parent=None):
        super(ClsBboxItem, self).__init__(parent)
        self.bbox_index = index
        self.start_slice = start_slice
        self.bbox = ClsButton(text, index)

        self.check_box = ClsBboxCheckBox()
        
        self.bbox.clicked.connect(lambda: self.Cls_button_clicked.emit(index))
        self.check_box.bbox_check_box_clicked.connect(lambda checked: self.Cls_check_box_clicked.emit(checked, self.bbox_index))
        
        layout = QtWidgets.QHBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.check_box, 2)
        layout.addWidget(self.bbox, 8)
    
    def set_checked(self, checked:bool):
        self.bbox.setChecked(checked)
    
    def set_checked_box(self, checked:bool):
        self.check_box.setChecked(checked)
    
    def get_start_slice(self):
        return self.start_slice

class ButtonListWindow(QtWidgets.QWidget):
    Cls_button_clicked = QtCore.pyqtSignal(int)
    Cls_check_box_clicked = QtCore.pyqtSignal(bool, int, str) # checked, bbox_index, patient_id
    def __init__(self):
        super().__init__()
        self.patient_id = ''
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

    
    def add_button(self, text:str, start_slice:int, index:int, is_checked:bool):
        start_slice = start_slice
        button = ClsBboxItem(text, index, start_slice, 0, self)
        button.Cls_button_clicked.connect(self.cls_button_clicked)
        button.Cls_check_box_clicked.connect(lambda checked, bbox_index: self.Cls_check_box_clicked.emit(checked, bbox_index, self.patient_id))
        button.set_checked_box(is_checked)
        self.Cls_buttons.append(button)
        self.button_layout.addRow(button)
        
    
    def add_buttions(self, patient_id:str, patient_cls_element:Manager.PatientClsElement):
        del self.Cls_buttons
        self.Cls_buttons = []
        cls_elements = patient_cls_element.get_sorted_elements()
        self.patient_id = patient_id
        for index, cls_element in enumerate(cls_elements):
            self.add_button('Nodule {},slice:{}, cls:{}'.format(patient_cls_element.get_nodule_index(index), cls_element.get_start_slice(), cls_element.get_category()), cls_element.get_start_slice(), index, cls_elements[index].get_checked())
    
    def clear_buttons(self):
        """清除當前所有按鈕"""
        while self.button_layout.count():
            item = self.button_layout.takeAt(0)
            if item is None:
                return
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
        if len(self.Cls_buttons) == 0:
            return False
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
    
    def set_checked(self, checked:bool):
        self.setChecked(checked)

class BboxNoduleBox(QtWidgets.QComboBox):
    bbox_index_changed = QtCore.pyqtSignal(int)
    def __init__(self, nodule_count:int):
        super(BboxNoduleBox, self).__init__()
        self.setFixedSize(QtCore.QSize(80, 20))
        self.setMaxVisibleItems(9999)
        self.addNodules(nodule_count)
        self.currentIndexChanged.connect(lambda index: self.bbox_index_changed.emit(index))

    def addNodule(self, nodule_index:int):
        self.addItem('nodule {}'.format(nodule_index))
        self.update()
    
    def addNodules(self, nodule_count:int):
        for nodule_index in range(nodule_count):
            self.addNodule(nodule_index)
    
    def setPatientIndex(self, index:int):
        self.setCurrentIndex(index)

class BboxCheckBox(QtWidgets.QCheckBox):
    bbox_check_box_clicked = QtCore.pyqtSignal(bool)
    def __init__(self, parent=None):
        super(BboxCheckBox, self).__init__(parent)
        self.clicked.connect(lambda: self.bbox_check_box_clicked.emit(self.isChecked()))

class BboxItem(QtWidgets.QWidget):
    bbox_button_clicked = QtCore.pyqtSignal(int)
    bbox_check_box_clicked = QtCore.pyqtSignal(bool, int) # checked, bbox_index
    def __init__(self, text:str, start_slice:int, index:int, nodule_index:int, parent=None):
        super(BboxItem, self).__init__(parent)
        self.bbox_index = index
        self.start_slice = start_slice
        self.bbox = BboxButton(text, index)
        self.check_box = BboxCheckBox()
        
        # self.set_nodule_index(nodule_index)
        self.bbox.clicked.connect(lambda: self.bbox_button_clicked.emit(index))
        self.check_box.bbox_check_box_clicked.connect(lambda checked: self.bbox_check_box_clicked.emit(checked, self.bbox_index))
        
        layout = QtWidgets.QHBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.check_box, 2)
        layout.addWidget(self.bbox, 8)
    
    def set_checked(self, checked:bool):
        self.bbox.setChecked(checked)
    
    def set_checked_box(self, checked:bool):
        self.check_box.setChecked(checked)
    
    def get_start_slice(self):
        return self.start_slice
            
class BboxesButtonListView(QtWidgets.QWidget):
    bbox_button_clicked = QtCore.pyqtSignal(int)
    bbox_check_box_clicked = QtCore.pyqtSignal(bool, int, str) # checked, bbox_index, patient_id
    def __init__(self):
        super().__init__()
        self.setFixedSize(QtCore.QSize(250, 400))
        self.patient_id = ''
        self.bbox_buttons = []
        self.bbox_index = -1
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

    
    def add_bbox(self, text:str, start_slice:int,  index:int, is_checked:bool, nodule_index:int):
        button = BboxItem(text, start_slice, index, nodule_index, self)
        button.bbox_button_clicked.connect(self.bbox_clickd)
        button.bbox_check_box_clicked.connect(lambda checked, bbox_index: self.bbox_check_box_clicked.emit(checked, bbox_index, self.patient_id))

        button.set_checked_box(is_checked)
        self.bbox_buttons.append(button)
        self.button_layout.addRow(button)
    
    def add_bboxes(self, patient:Manager.Patient):
        del self.bbox_buttons
        self.bbox_buttons = []
        self.patient_id = patient.get_image_id()
        bboxes = patient.get_sorted_bboxes()
        for index, bbox in enumerate(bboxes):
            self.add_bbox('Bbox {}, slice:{}'.format(patient.get_bbox_index(index), bbox.get_start_slice()), bbox.get_start_slice(), index, bboxes[index].get_checked(), bbox.get_nodule_index())
        
        # self.bbox_buttons = sorted(self.bbox_buttons, key=lambda x: x.get_start_slice())
        # for box_button in self.bbox_buttons:
        #     self.button_layout.addRow(box_button)
    
    def clear_buttons(self):
        """清除當前所有按鈕"""
        while self.button_layout.count():
            item = self.button_layout.takeAt(0)
            if item is not None:
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
    
    def set_bbox_button_index(self, index:int)->bool:
        self.reset_buttons()
        if len(self.bbox_buttons) == 0:
            return False
        
        if index >= 0 and index < len(self.bbox_buttons):
            self.bbox_buttons[index].set_checked(True)
            return True
        elif index == len(self.bbox_buttons):
            self.bbox_buttons[len(self.bbox_buttons)-1].set_checked(True)
        elif index < 0:
            self.bbox_buttons[0].set_checked(True)
        return False

    def update_bbox_noodule_index(self, index:int, nodule_index:int):
        self.bbox_buttons[index].set_nodule_index(nodule_index)

class BboxTypeButton(QtWidgets.QPushButton):
    bbox_type_button_clicked = QtCore.pyqtSignal(str)
    def __init__(self, text:str, parent=None):
        super(BboxTypeButton, self).__init__(parent)
        self.setText(text)
        self.setCheckable(True)
        self.clicked.connect(lambda: self.bbox_type_button_clicked.emit(text))

    def set_checked(self, checked:bool):
        self.setChecked(checked)
        
class Box(QtWidgets.QComboBox):
    bbox_index_changed = QtCore.pyqtSignal(int)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setMaxVisibleItems(9999)
        self._updating = False  # 用來追蹤是否在更新

        # 綁定 currentIndexChanged 信號
        self.currentIndexChanged.connect(self.on_index_changed)

    def on_index_changed(self, index: int):
        if not self._updating:  # 只有當非更新狀態時才發送信號
            self.bbox_index_changed.emit(index)

    def add_item(self, nodule_index: int, type: str = 'nodule'):
        if type == 'nodule':
            self.addItem(f'nodule {nodule_index}')
        elif type == 'bbox':
            self.addItem(f'bbox {nodule_index}')
        else:
            self.addItem(f'{nodule_index}')
        self.update()

    def add_items(self, nodule_count: int, type: str = 'nodule'):
        self._updating = True  # 標記為更新狀態
        self.clear()

        for nodule_index in range(nodule_count):
            self.add_item(nodule_index, type=type)

        self._updating = False  # 結束更新狀態

    def set_item_index(self, index: int):
        self.setCurrentIndex(index)

    def box_item_clear(self):
        self._updating = True  # 暫停信號發送
        self.clear()
        self._updating = False
        
class BboxTypeButtons(QtWidgets.QWidget):
    bbox_type_button_clicked = QtCore.pyqtSignal(int)
    def __init__(self, parent=None):
        super(BboxTypeButtons, self).__init__(parent)
        self.button_texts = ['Match', 'Combine', 'Delete', 'Other']
        self.buttons = [BboxTypeButton(text) for text in self.button_texts]
        self.button_index = 0
        
        button_layout = QtWidgets.QHBoxLayout(self)
        for button in self.buttons:
            button.bbox_type_button_clicked.connect(self.bbox_type_button_clicked_func)
            button_layout.addWidget(button)
    
    def bbox_type_button_clicked_func(self, text:str):
        for button, t in zip(self.buttons, self.button_texts):
            if t == text:
                button.set_checked(True)
            else:
                button.set_checked(False)
        self.button_index = self.button_texts.index(text)
        self.bbox_type_button_clicked.emit(self.button_texts.index(text))
    
    def empty(self):
        for button in self.buttons:
            button.set_checked(False)
    
    def set_button_index(self, index:int):
        self.button_index = index
        self.empty()
        if index != -1 and index < len(self.buttons):
            self.buttons[index].set_checked(True)
              
class BboxInfoWidget(QtWidgets.QWidget):
    bbox_type_button_clicked = QtCore.pyqtSignal(int)
    bbox_index_changed = QtCore.pyqtSignal(int, int)
    def __init__(self):
        super(BboxInfoWidget, self).__init__()
        self.initWidget()
    
    def initWidget(self):
        self.bbox_type_buttons = BboxTypeButtons()
        self.box = Box()
        self.bbox_type_buttons.bbox_type_button_clicked.connect(lambda index: self.bbox_type_button_clicked.emit(index))
        self.box.bbox_index_changed.connect(self.bbox_index_changed_func)
        info_layout = QtWidgets.QVBoxLayout(self)
        info_layout.addWidget(self.bbox_type_buttons)
        info_layout.addWidget(self.box)
    
    def bbox_index_changed_func(self, index:int):
        if index != -1:
            self.bbox_index_changed.emit(index, self.bbox_type_buttons.button_index)
    
    def add_box_items(self, item_count:int, type:str='nodule', index:int=0):
        self.box.add_items(item_count, type=type)
        self.box.set_item_index(index)
    
    def rest_box(self, box:Manager.Bbox):
        if box is not None:
            type_index = box.get_bbox_type()
            if type_index == 0:
                self.add_box_items(10, 'nodule', box.get_nodule_index())
            elif type_index == 1:
                self.add_box_items(10, 'bbox', box.get_box_group())
                
            self.bbox_type_buttons.set_button_index(type_index)

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

class NextBboxButton(QtWidgets.QPushButton):
    next_bbox_clicked = QtCore.pyqtSignal()
    def __init__(self, parent=None):
        super(NextBboxButton, self).__init__(parent)
        self.setText('Next Bbox')
        self.clicked.connect(self.next_bbox_clicked.emit)

class PreviousBboxButton(QtWidgets.QPushButton):    
    previous_bbox_clicked = QtCore.pyqtSignal()
    def __init__(self, parent=None):
        super(PreviousBboxButton, self).__init__(parent)
        self.setText('Previous Bbox')
        self.clicked.connect(self.previous_bbox_clicked.emit)

class ConfirmButton(QtWidgets.QPushButton):
    confirm_clicked = QtCore.pyqtSignal()
    def __init__(self, parent=None):
        super(ConfirmButton, self).__init__(parent)
        self.setText('Confirm')
        self.clicked.connect(self.confirm_clicked.emit)
        
class DisplayNoduleTable(QtWidgets.QLabel):
    def __init__(self):
        super(DisplayNoduleTable, self).__init__()
        font = QtGui.QFont()
        font.setFamily("Arial") #括号里可以设置成自己想要的其它字体
        font.setPointSize(18)   #括号里的数字可以设置成自己想要的字体大小
        self.setFixedSize(QtCore.QSize(200, 50))
        self.setText('Display Table')
        self.setFont(font)
    
    def set_text(self, nodule_id:int):
        self.setText('Nodule {}'.format(nodule_id))

class DisplayBBoxTable(QtWidgets.QLabel):
    def __init__(self):
        super(DisplayBBoxTable, self).__init__()
        font = QtGui.QFont()
        font.setFamily("Arial") #括号里可以设置成自己想要的其它字体
        font.setPointSize(18)   #括号里的数字可以设置成自己想要的字体大小
        self.setFixedSize(QtCore.QSize(200, 50))
        self.setText('Display Table')
        self.setFont(font)
    
    def set_text(self, bbox_id:int):
        self.setText('Bbox {}'.format(bbox_id))

class OutputButton(QtWidgets.QPushButton):
    button_clicked = QtCore.pyqtSignal()
    def __init__(self):
        super(OutputButton, self).__init__()
        self.setFixedSize(QtCore.QSize(200, 50))
        self.setText('Output')
        self.clicked.connect(lambda: self.button_clicked.emit())