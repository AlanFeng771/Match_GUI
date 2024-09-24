from PyQt5 import QtCore, QtGui, QtWidgets
import numpy as np
import cv2
import json
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
    
    def load_image(self, image_path):
        self.images = np.load(image_path)
        self.image_index = 0
        self.scrollBar.setMaximum(self.images.shape[2]-1)
        self.show_image()
    
    def load_bbox(self, bbox_path):
        with open(bbox_path, 'r') as json_file:
            bboxes = json.load(json_file)['bboxes']
        
        for bbox in bboxes:
            left_top, right_bottom = bbox # left_top = [y_min, x_min, z_min], right_bottom = [y_max, x_max, z_max]
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
    
    def show(self, image_index=0):
        self.show_image(image_index)
        self.show_bbox(image_index)
        
    
class CustomRectItem(QtWidgets.QGraphicsItem):
    def __init__(self, size:list[int, int], position:QtCore.QRectF, slices:list, border_color=QtCore.Qt.red, parent=None):
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
        print(self.slices, slice)
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
        self.load_image_clicked.emit(filename)

class LoadAnnotationButton(QtWidgets.QPushButton):
    load_annotation_clicked = QtCore.pyqtSignal(str)
    def __init__(self, parent=None):
        super(LoadAnnotationButton, self).__init__(parent)
        self.setText('Load annotation')
        self.clicked.connect(self.load_annotation)
    
    def load_annotation(self):
        filename, filetype = QtWidgets.QFileDialog.getOpenFileName(self, "Open file", "./")
        self.load_annotation_clicked.emit(filename)
    
    