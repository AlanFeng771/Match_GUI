from PyQt5 import QtWidgets
import widgets
class Controller(QtWidgets.QWidget):
    def __init__(self):
        super(Controller, self).__init__()
        self.image_id = None
        self.patients = []
        self.image_file = None
        self.annotation_file = None
        self.initWidget()
        
    def initWidget(self):
        self.player = widgets.PlayerView()
        self.load_image_button = widgets.LoadImageButton()
        VBlayout = QtWidgets.QVBoxLayout(self)
        VBlayout.addWidget(self.player)
        VBlayout.addWidget(self.load_image_button)
        self.load_image_button.load_image_clicked.connect(self.player.load_image)
        
        

if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)
    controller = Controller()
    controller.setGeometry(500, 300, 1200, 600)
    controller.showMaximized()
    sys.exit(app.exec_())
        
