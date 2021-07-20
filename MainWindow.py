import os
import time

import cv2
import numpy as np
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtWidgets import QMainWindow, QMessageBox, QFileDialog

from UI.test import Ui_MainWindow


class MainWindow(QMainWindow, Ui_MainWindow):
    __url = ""
    __cvImg = None
    __cvTransparentLayerInit = None
    __cvTransparentLayer = None
    __combinedImg = None
    __point_list = []

    def __init__(self):
        super(MainWindow, self).__init__()
        self.setupUi(self)
        self.setWindowTitle("龟速打点工具")
        self.fileSelectButton.clicked.connect(self.select_file)
        self.undoButton.clicked.connect(self.delete_point)
        self.saveButton.clicked.connect(self.save_to_file)
        self.label.setText("先选文件好吗")

        self.label.mousePressEvent = self.get_pos

    def print_all_points(self):
        if len(self.__point_list) == 0:
            self.show_pic_in_label(self.__cvImg)
        self.init_transparent_layer()
        for (x, y) in self.__point_list:
            self.print_single_point(x, y)

    def init_transparent_layer(self):
        self.__cvTransparentLayer = self.__cvTransparentLayerInit.copy()

    def load_pic_file(self):
        self.__cvImg = cv2.imdecode(np.fromfile(self.__url, dtype=np.uint8), -1)
        image_height, image_width, image_depth = self.__cvImg.shape
        if image_depth < 4:
            self.__cvImg = cv2.cvtColor(self.__cvImg, cv2.COLOR_RGB2BGRA)
        self.__cvTransparentLayerInit = np.full((image_height, image_width, 4), (0, 0, 0, 0), dtype=np.uint8)
        self.show_pic_in_label(self.__cvImg)

    def delete_point(self):
        if self.__point_list:
            self.__point_list.pop()
        if len(self.__url) > 0:
            self.print_all_points()

    def print_single_point(self, x=None, y=None):
        if x and y:
            cv2.circle(self.__cvTransparentLayer, (x, y), 5, (0, 0, 255, 255), cv2.FILLED)
            self.print_pos_text(self.__cvTransparentLayer, x, y)

        lower = np.array([0, 0, 0, 250])
        upper = np.array([255, 255, 255, 255])

        mask = cv2.inRange(self.__cvTransparentLayer, lower, upper)
        mask_not = cv2.bitwise_not(mask)
        combined_bg = cv2.bitwise_and(self.__cvImg, self.__cvImg, mask=mask_not)
        self.__combinedImg = cv2.add(combined_bg, self.__cvTransparentLayer)

        self.show_pic_in_label(self.__combinedImg)

    def save_to_file(self):
        filename = "RESULT-{}.png".format(time.strftime("%Y%m%d-%H%M%S"), time.localtime())
        custom_filename, _ = QFileDialog.getSaveFileName(self, "保存文件", filename, "Text Files (*.png)")
        if custom_filename and len(self.__url) > 0:
            # print(custom_filename)
            cv2.imwrite(custom_filename, self.__combinedImg)
            QMessageBox.about(self, "Title", "文件已保存在：{}".format(custom_filename))

    def show_pic_in_label(self, img):
        image_height, image_width, image_depth = self.__cvImg.shape
        q_im = cv2.cvtColor(img, cv2.COLOR_BGRA2RGBA)
        q_im = QImage(q_im.data, image_width, image_height,
                      image_width * image_depth,
                      QImage.Format_RGBA8888)
        pixmap = QPixmap.fromImage(q_im)
        self.label.setPixmap(pixmap)
        self.label.resize(pixmap.width(), pixmap.height())

    def get_pos(self, event):
        x = event.pos().x()
        y = event.pos().y()
        if len(self.__url) > 0:
            self.__point_list.append((x, y))
            self.print_all_points()

    def print_pos_text(self, img, x, y):
        pos_text = "(" + str(x) + "," + str(y) + ")"
        font = cv2.FONT_HERSHEY_DUPLEX
        org = (x - 47, y + 25)
        font_scale = 0.6
        color = (0, 0, 255, 255)
        thickness = 1
        cv2.putText(img, pos_text, org, font, font_scale, color, thickness)
        self.label_res.setText(pos_text)

    def select_file(self):
        file_name, file_type = QFileDialog.getOpenFileName(self, "选取文件", os.getcwd(), "Image Files(*.jpg *.png)")
        if file_name:
            self.__url = file_name
            self.load_pic_file()
            # print(file_name)
            # print(file_type)
