import sys
from PyQt5.QtWidgets import QApplication, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QMainWindow
from PyQt5.QtGui import QImage, QPixmap, QPainter, QColor
from PyQt5.QtCore import Qt
import cv2
import numpy as np

class ImageWindow(QMainWindow):
    def __init__(self, image_path, mask_path):
        super().__init__()

        # Load the original image and mask
        self.image = cv2.imread(image_path)
        self.mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
        self.mask = cv2.threshold(self.mask, 127, 255, cv2.THRESH_BINARY)[1]  # Ensure binary mask

        # Convert the original image to RGB format for PyQt
        self.image = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)

        # Resize the mask to match the image size (if necessary)
        if self.image.shape[:2] != self.mask.shape[:2]:
            self.mask = cv2.resize(self.mask, (self.image.shape[1], self.image.shape[0]))

        # Use Canny edge detection to find the edges in the mask
        self.edges = cv2.Canny(self.mask, 100, 200)
        
        # Set up the QGraphicsView and QGraphicsScene
        self.view = QGraphicsView(self)
        self.scene = QGraphicsScene(self)
        self.view.setScene(self.scene)
        self.setCentralWidget(self.view)

        # Display the original image
        self.display_image()

        # Display the mask edges on top of the image
        self.display_edges()

        # Set an initial zoom factor to enlarge the image
        self.zoom_factor = 1.5  # You can adjust this value for larger/smaller scaling
        self.view.scale(self.zoom_factor, self.zoom_factor)  # Apply scaling

    def display_image(self):
        # Convert the image to QImage
        height, width, channel = self.image.shape
        qimage = QImage(self.image.data, width, height, 3 * width, QImage.Format_RGB888)

        # Convert QImage to QPixmap and add to scene
        pixmap = QPixmap.fromImage(qimage)
        image_item = QGraphicsPixmapItem(pixmap)
        self.scene.addItem(image_item)

    def display_edges(self):
        # Create a QPixmap for the edges
        height, width = self.edges.shape
        edge_pixmap = QPixmap(width, height)
        edge_pixmap.fill(Qt.transparent)  # Start with a transparent pixmap

        # Use QPainter to draw the edges onto the QPixmap
        painter = QPainter(edge_pixmap)
        painter.setPen(QColor(255, 0, 0))  # Red color for edges
        for y in range(height):
            for x in range(width):
                if self.edges[y, x] == 255:  # If it's an edge
                    painter.drawPoint(x, y)
        painter.end()

        # Convert the edge pixmap to a QGraphicsPixmapItem and add to scene
        edge_item = QGraphicsPixmapItem(edge_pixmap)
        self.scene.addItem(edge_item)

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Replace 'image.jpg' and 'mask.png' with your image and mask file paths
    window = ImageWindow("ldct.jpg", "mask.jpg")
    window.show()

    sys.exit(app.exec_())
