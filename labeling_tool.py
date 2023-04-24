import json
import sys
import cv2
import os
import datetime
from PyQt5 import QtCore
import numpy as np
from PyQt5.QtWidgets import QApplication, QFileDialog, QLabel, QLineEdit, QWidget, \
    QPushButton, QListWidget, QListWidgetItem, QGridLayout, QGroupBox, QGraphicsView, QGraphicsScene, QSlider, \
    QRadioButton
from PyQt5.QtGui import QPixmap, QIntValidator, QImage, QCursor, QColor
from PyQt5.QtCore import Qt


class MyApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        grid = QGridLayout()
        grid.addWidget(self.Group_getFrames(), 0, 0, 1, 1)
        grid.addWidget(self.Group_showVideoInfo(), 0, 1, 1, 2)
        grid.addWidget(self.Group_labelFrames(), 1, 0, 3, 1)
        grid.addWidget(self.Group_loadClassAndSave(), 1, 1, 3, 2)

        self.setLayout(grid)
        self.setWindowTitle('Image Labeling Tool')
        self.move(0, 0)
        self.show()

    # 비디오 파일 추출 또는 기존 디렉토리 통해 프레임 불러오는 그룹박스
    def Group_getFrames(self):
        groupbox = QGroupBox('Get Frames from Video/Directory')
        groupbox.setFixedHeight(100)

        openBtn = QPushButton('Open with', self)
        openBtn.clicked.connect(self.onOpenBtnClicked)
        openBtn.setFixedSize(150, 25)

        self.extractBtn = QPushButton('Extract every', self)
        self.extractBtn.setFixedSize(150, 25)
        self.extractBtn.setDisabled(True)
        self.extractBtn.clicked.connect(self.onExtractBtnClicked)

        self.videoRbtn = QRadioButton('New Video', self)
        self.videoRbtn.setChecked(True)
        self.videoRbtn.toggled.connect(self.extractBtnState)
        self.dirRbtn = QRadioButton('Existing Directory', self)

        self.perFrame = QLineEdit()
        self.perFrame.setValidator(QIntValidator(self))
        self.perFrame.setAlignment(Qt.AlignCenter)
        self.perFrame.setFixedWidth(50)
        self.perFrame.setText("30")
        self.frameInterval = int(self.perFrame.text())
        TEXT_frames = QLabel('frames', self)

        self.setSize = QLineEdit()
        self.setSize.setValidator(QIntValidator(self))
        self.setSize.setAlignment(Qt.AlignCenter)
        self.setSize.setFixedWidth(50)
        self.setSize.setText("720")
        self.setScaleSize = int(self.setSize.text())
        TEXT_scale = QLabel('height scale', self)

        grid = QGridLayout()
        grid.addWidget(openBtn, 0, 0)
        grid.addWidget(self.extractBtn, 1, 0)
        grid.addWidget(self.videoRbtn, 0, 1, 1, 3)
        grid.addWidget(self.dirRbtn, 0, 3, 1, 4)
        grid.addWidget(self.perFrame, 1, 1)
        grid.addWidget(TEXT_frames, 1, 2)
        grid.addWidget(self.setSize, 1, 3)
        grid.addWidget(TEXT_scale, 1, 4)

        groupbox.setLayout(grid)
        return groupbox

    # 비디오 정보 그룹박스
    def Group_showVideoInfo(self):
        grid = QGridLayout()
        groupbox = QGroupBox('Video Properties')
        groupbox.setLayout(grid)

        self.videoProperties = QLabel('Name : (None)\nFPS : (None)\nDimension : (None)\nDuration : (None)')

        grid.addWidget(self.videoProperties)
        return groupbox

    # 이미지 관련 그룹박스
    def Group_labelFrames(self):
        groupbox = QGroupBox('Labeling Section')
        self.imgLabel = ImgView(self)
        self.imgLabel.setCursor(QCursor(QtCore.Qt.CrossCursor))

        self.scene = QGraphicsScene()
        self.isVideoLoaded = False
        self.isDirLoaded = False
        self.isImgOpen = False

        self.imgList = QListWidget(self)
        self.imgList.setFixedWidth(300)
        self.imgList.currentRowChanged.connect(self.changeImg)

        self.brightnessSlider = QSlider(Qt.Horizontal, self)
        self.brightnessSlider.setRange(1, 20)
        self.brightnessSlider.setValue(10)
        self.brightnessSlider.valueChanged.connect(self.changeImg)
        self.brightnessValue = QLineEdit()
        self.brightnessValue.setText(str(self.brightnessSlider.value()))
        self.brightnessValue.setMaximumWidth(50)
        self.brightnessValue.setAlignment(Qt.AlignCenter)

        self.contrastSlider = QSlider(Qt.Horizontal, self)
        self.contrastSlider.setRange(1, 20)
        self.contrastSlider.setValue(10)
        self.contrastSlider.valueChanged.connect(self.changeImg)
        self.contrastValue = QLineEdit()
        self.contrastValue.setText(str(self.contrastSlider.value()))
        self.contrastValue.setMaximumWidth(50)
        self.contrastValue.setAlignment(Qt.AlignCenter)

        TEXT_Brightness = QLabel("Brightness :")
        TEXT_Brightness.setFixedWidth(80)
        TEXT_Contrast = QLabel("Contrast :")
        TEXT_Contrast.setFixedWidth(80)

        grid = QGridLayout()
        grid.addWidget(self.imgList, 0, 0, 1, 3)
        grid.addWidget(TEXT_Brightness, 1, 0)
        grid.addWidget(TEXT_Contrast, 2, 0)
        grid.addWidget(self.brightnessSlider, 1, 1)
        grid.addWidget(self.contrastSlider, 2, 1)
        grid.addWidget(self.brightnessValue, 1, 2)
        grid.addWidget(self.contrastValue, 2, 2)
        grid.addWidget(self.imgLabel, 0, 3, 3, 3)
        groupbox.setLayout(grid)
        return groupbox

    # 카테고리와 저장 버튼 그룹박스
    def Group_loadClassAndSave(self):
        groupbox = QGroupBox('Load classes')

        loadBtn = QPushButton('Load a Text File', self)
        loadBtn.clicked.connect(self.onLoadBtnClicked)

        saveBtn = QPushButton('&Save', self)
        saveBtn.clicked.connect(self.saveToJson)

        self.classList = QListWidget(self)
        self.classList.itemClicked.connect(self.imgLabel.changeRoiClass)
        self.classList.currentRowChanged.connect(self.imgLabel.changeRoiClass)
        self.isClassLoaded = False

        grid = QGridLayout()
        grid.addWidget(loadBtn, 0, 0)
        grid.addWidget(saveBtn, 2, 0)
        grid.addWidget(self.classList, 1, 0)

        groupbox.setLayout(grid)
        return groupbox

    # Extract 버튼 활성화 상태
    def extractBtnState(self):
        if self.videoRbtn.isChecked() == 0:
            self.extractBtn.setDisabled(True)
        elif self.videoRbtn.isChecked() == 1 and self.isVideoLoaded is True and self.isDirLoaded is False:
            self.extractBtn.setEnabled(True)

    # 영상 주소 따기
    def onOpenBtnClicked(self):
        self.isVideoLoaded = False
        self.isDirLoaded = False
        self.isImgOpen = False
        self.videoFilePath = ''
        self.dataSetPath = ''
        self.imagesPath = ''
        self.labelsPath = ''
        self.nameData = '(None)'
        self.rois = []
        self.imgList.clear()

        if self.videoRbtn.isChecked() == 1:
            fname = QFileDialog.getOpenFileName(self, 'Open file', './', "Video Files (*.mp4 *.flv *.ts *.mts *.avi)")
            if fname[0]:
                self.isVideoLoaded = True
                self.extractBtnState()
                self.videoFilePath = fname[0]
                self.nameData = os.path.basename(self.videoFilePath)
                self.dataSetPath = self.videoFilePath + '_dataset'
                self.imagesPath = self.dataSetPath + '/images'
                self.labelsPath = self.dataSetPath + '/labels'

        else:
            self.dataSetPath = QFileDialog.getExistingDirectory(self, "Open directory")
            if self.dataSetPath and self.dataSetPath.endswith('_dataset'):
                self.isDirLoaded = True
                self.extractBtnState()
                self.videoFilePath = self.dataSetPath.rsplit('_dataset')[0]
                self.isVideoLoaded = os.path.isfile(self.videoFilePath)
                self.nameData = os.path.basename(self.videoFilePath)
                self.imagesPath = self.dataSetPath + '/images'
                self.labelsPath = self.dataSetPath + '/labels'

        self.videoProperties.setText(f'Name : {self.nameData}\nFPS : (None)\nDimension : (None)\nDuration : (None)')

        if self.isVideoLoaded:
            self.cap = cv2.VideoCapture(self.videoFilePath)
            if self.cap.isOpened():
                self.frameInterval = int(self.perFrame.text())
                self.setScaleSize = int(self.setSize.text())
                self.w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                self.h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                self.scale = self.setScaleSize / self.h
                self.fpsData = int(self.cap.get(cv2.CAP_PROP_FPS))
                self.sizeData = str(self.w) + 'x' + str(self.h)
                seconds = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT) / int(self.cap.get(cv2.CAP_PROP_FPS)))
                video_time = str(datetime.timedelta(seconds=seconds))
                self.lengthData = video_time
                self.videoProperties.setText(f'Name : {self.nameData}\nFPS : {self.fpsData}\n'
                                             f'Dimension : {self.sizeData}\nDuration : {self.lengthData}')

        if self.isDirLoaded and os.path.isdir(self.imagesPath) and os.path.isdir(self.labelsPath):
            fileList = os.listdir(self.imagesPath)
            for file in fileList:
                itemName = file
                item = QListWidgetItem(itemName)
                jsonFilePath = self.labelsPath + '/' + itemName.rsplit('.')[0] + '.json'
                if os.path.isfile(jsonFilePath):
                    item.setBackground(QColor('#ffff99'))
                self.imgList.addItem(item)
            self.imgList.setCurrentRow(0)

    # 영상 정보 추출
    def onExtractBtnClicked(self):
        if self.isImgOpen is False:
            self.imgList.clear()

            if os.path.isdir(self.dataSetPath) is False:
                os.mkdir(self.dataSetPath)
                os.mkdir(self.imagesPath)
                os.mkdir(self.labelsPath)

            # 이미지 리스트
            numOfImg = round(self.cap.get(cv2.CAP_PROP_FRAME_COUNT) / self.frameInterval)
            for i in range(1, numOfImg + 1):
                itemName = "%s_%06d.jpg" % (self.nameData.rsplit('.')[0], 1 + (self.frameInterval * (i - 1)))
                item = QListWidgetItem(itemName)
                jsonFilePath = self.labelsPath + '/' + itemName.rsplit('.')[0] + '.json'
                if os.path.isfile(jsonFilePath):
                    item.setBackground(QColor('#ffff99'))
                self.imgList.addItem(item)
            self.imgList.setCurrentRow(0)

    # 이미지 바꾸기
    def changeImg(self):
        if self.isVideoLoaded or self.isDirLoaded:
            self.isImgOpen = True
            self.rois = []
            self.imgLabel.factor = self.scale
            self.imgLabel.sRoi = []
            self.imgLabel.setCursor(QCursor(QtCore.Qt.CrossCursor))
            check = os.path.isfile(self.imagesPath + '/' + self.imgList.currentItem().text())
            if check is False:
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 1 + (self.frameInterval * self.imgList.currentRow()))
                ret, image = self.cap.read()
                if ret:
                    cv2.imwrite(self.imagesPath + '/' + self.imgList.currentItem().text(), image)
            else:
                image = cv2.imread(self.imagesPath + '/' + self.imgList.currentItem().text())

            if not self.rois:
                jsonFilePath = self.labelsPath + '/' + self.imgList.currentItem().text().rsplit('.')[0] + '.json'
                if os.path.isfile(jsonFilePath):
                    with open(jsonFilePath, 'r') as f:
                        json_data = json.load(f)
                        for i in range(len(json_data['annotations'])):
                            temp_list = json_data['annotations'][i]['bbox']
                            temp_list[0] *= self.w
                            temp_list[1] *= self.h
                            temp_list[2] *= self.w
                            temp_list[3] *= self.h
                            temp_list[2] += temp_list[0]
                            temp_list[3] += temp_list[1]
                            box = (list(map(int, temp_list)))
                            box.append(json_data['annotations'][i]['class'])
                            self.rois.append(box)
            self.h, self.w, self.ch = image.shape
            self.brightnessValue.setText(str(self.brightnessSlider.value()))
            self.contrastValue.setText(str(self.contrastSlider.value()))
            blank = np.zeros([self.h, self.w, self.ch], image.dtype)
            self.showImg = cv2.addWeighted(image, (self.contrastSlider.value() / 10), blank,
                                           (self.contrastSlider.value() / 10),
                                           (self.brightnessSlider.value() - 10) * 10)
            self.imgLabel.setFixedWidth(int(self.scale * self.w))
            self.imgLabel.setFixedHeight(int(self.scale * self.h))
            self.copy = self.showImg.copy()

            for roi in self.rois:
                self.makeRoi(roi, self.copy, (63, 31, 0))

            self.loadImage(self.copy)
            self.imgLabel.resetTransform()
            self.imgLabel.scale(self.scale, self.scale)

    # 클래스 파일 가져오기
    def onLoadBtnClicked(self):
        self.classList.clear()
        fname = QFileDialog.getOpenFileName(self, 'Open file', './', "Text Files (*.txt)")
        if fname[0]:
            self.isClassLoaded = True
            data = open(fname[0], 'r')
            dataLine = data.readline().rstrip()
            while dataLine:
                self.classList.addItem(dataLine)
                dataLine = data.readline().rstrip()
            self.classList.setCurrentRow(0)
        else:
            self.isClassLoaded = False

    def keyPressEvent(self, e):
        # 선택한 roi 삭제
        if e.key() == Qt.Key_Delete and self.imgLabel.sRoi:
            img_draw = self.showImg.copy()
            self.selected = False
            self.rois.remove(self.imgLabel.sRoi)
            self.imgLabel.sRoi = []
            for roi in self.rois:
                self.makeRoi(roi, img_draw, (36, 31, 0))
            self.copy = img_draw
            self.loadImage(self.copy)
            self.imgLabel.setCursor(QCursor(QtCore.Qt.CrossCursor))

        # 클래스 리스트 w, s로 이동
        elif (e.key() == Qt.Key_W or e.key() == Qt.Key_Up) and self.isClassLoaded:
            currentRow = self.classList.currentRow()
            if currentRow > 0:
                self.classList.setCurrentRow(currentRow - 1)
        elif (e.key() == Qt.Key_S or e.key() == Qt.Key_Down) and self.isClassLoaded:
            currentRow = self.classList.currentRow()
            if currentRow < self.classList.count() - 1:
                self.classList.setCurrentRow(currentRow + 1)

        # 이미지 리스트 a,d로 이동
        elif (e.key() == Qt.Key_A or e.key() == Qt.Key_Left) and self.isImgOpen:
            currentRow = self.imgList.currentRow()
            self.saveToJson()
            if currentRow > 0:
                self.imgList.setCurrentRow(currentRow - 1)
        elif (e.key() == Qt.Key_D or e.key() == Qt.Key_Right) and self.isImgOpen:
            currentRow = self.imgList.currentRow()
            self.saveToJson()
            if currentRow < self.imgList.count() - 1:
                self.imgList.setCurrentRow(currentRow + 1)

    # 사각형 그리는 함수
    def makeRoi(self, roi, img, color):
        cv2.putText(img, roi[4], (roi[0], roi[1] - 8), cv2.FONT_HERSHEY_DUPLEX, 1, color, 2)
        cv2.rectangle(img, (roi[0], roi[1]), (roi[2], roi[3]), color, 2)

    # numpy 이미지 -> Q 이미지
    def loadImage(self, img):
        self.scene.clear()
        h, w, c = img.shape
        bytesPerLine = 3 * w
        q_img = QImage(img, w, h, bytesPerLine, QImage.Format_RGB888)
        q_img = QImage.rgbSwapped(q_img)
        self.q_pixmap_img = QPixmap.fromImage(q_img)
        self.scene.addPixmap(self.q_pixmap_img)
        self.imgLabel.setScene(self.scene)

    # json 파일로 저장
    def saveToJson(self):
        if self.isImgOpen and self.isClassLoaded:

            json_file = {"images": {}, "type": "instance", "annotations": []}
            json_file.update(
                images={'file_name': self.imgList.currentItem().text(), 'width': self.w, 'height': self.h})
            count = 1
            for roi in self.rois:
                json_file["annotations"].append({"bbox": [roi[0] / self.w, roi[1] / self.h,
                                                          (roi[2] - roi[0]) / self.w, (roi[3] - roi[1]) / self.h],
                                                 "class": "%s" % roi[4], "id": count})
                count += 1
            jsonFilePath = self.labelsPath + '/' + self.imgList.currentItem().text().rsplit('.')[0] + '.json'
            self.imgList.currentItem().setBackground(QColor('#FA8072'))
            with open(jsonFilePath, 'w') as f:
                json.dump(json_file, f)


class ImgView(QGraphicsView):
    def __init__(self, parent):
        super().__init__(parent)
        self.ma = parent
        self.draw = False
        self.moveImg = False
        self.moveRoi = False
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setTransformationAnchor(self.AnchorUnderMouse)
        self.setResizeAnchor(self.AnchorUnderMouse)
        self.sRoi = []
        self.factor = 1

    # 마우스 이벤트
    def mousePressEvent(self, e):
        if self.ma.isVideoLoaded and self.ma.isImgOpen:
            if e.button() == Qt.LeftButton and self.ma.isClassLoaded:
                self.xStart = int(self.mapToScene(e.pos()).x())
                self.yStart = int(self.mapToScene(e.pos()).y())
                if self.sRoi and (self.sRoi[0] - 3 <= self.xStart <= self.sRoi[2] + 3) \
                        and (self.sRoi[1] - 3 <= self.yStart <= self.sRoi[3] + 3):
                    self.moveRoi = True
                    self.img_draw = self.ma.showImg.copy()
                    self.ma.rois.remove(self.sRoi)
                    for roi in self.ma.rois:
                        self.ma.makeRoi(roi, self.img_draw, (63, 31, 0))
                else:
                    self.draw = True
                    self.sRoi = []

            # 이미지 이동
            if e.button() == Qt.RightButton:
                self.moveImg = True
                self.moveStartPos = e.pos()

    def mouseMoveEvent(self, e):
        if self.sRoi:
            self.currentX = int(self.mapToScene(e.pos()).x())
            self.currentY = int(self.mapToScene(e.pos()).y())
            if ((self.sRoi[0] - 3 <= self.currentX <= self.sRoi[0] + 3) and
                (self.sRoi[1] - 3 <= self.currentY <= self.sRoi[1] + 3)) or \
                    ((self.sRoi[2] - 3 <= self.currentX <= self.sRoi[2] + 3) and
                     (self.sRoi[3] - 3 <= self.currentY <= self.sRoi[3] + 3)):
                self.setCursor(QCursor(QtCore.Qt.SizeFDiagCursor))
            elif ((self.sRoi[0] - 3 <= self.currentX <= self.sRoi[0] + 3) and
                  (self.sRoi[3] - 3 <= self.currentY <= self.sRoi[3] + 3)) or \
                    ((self.sRoi[2] - 3 <= self.currentX <= self.sRoi[2] + 3) and
                     (self.sRoi[1] - 3 <= self.currentY <= self.sRoi[1] + 3)):
                self.setCursor(QCursor(QtCore.Qt.SizeBDiagCursor))
            elif ((self.sRoi[0] - 3 <= self.currentX <= self.sRoi[0] + 3) and
                  (self.sRoi[1] <= self.currentY <= self.sRoi[3])) or \
                    ((self.sRoi[2] - 3 <= self.currentX <= self.sRoi[2] + 3) and
                     (self.sRoi[1] <= self.currentY <= self.sRoi[3])):
                self.setCursor(QCursor(QtCore.Qt.SizeHorCursor))
            elif ((self.sRoi[0] <= self.currentX <= self.sRoi[2]) and
                  (self.sRoi[1] - 3 <= self.currentY <= self.sRoi[1] + 3)) or \
                    ((self.sRoi[0] <= self.currentX <= self.sRoi[2]) and
                     (self.sRoi[3] - 3 <= self.currentY <= self.sRoi[3] + 3)):
                self.setCursor(QCursor(QtCore.Qt.SizeVerCursor))
            elif (self.sRoi[0] < self.currentX < self.sRoi[2]) and (self.sRoi[1] < self.currentY < self.sRoi[3]):
                self.setCursor(QCursor(QtCore.Qt.SizeAllCursor))
            elif Qt.RightButton and self.moveImg:
                self.setCursor(QCursor(QtCore.Qt.ClosedHandCursor))
            else:
                self.setCursor(QCursor(QtCore.Qt.CrossCursor))

        if Qt.LeftButton:
            if self.moveRoi:
                # 좌상단
                if (self.sRoi[0] - 3 <= self.xStart <= self.sRoi[0] + 3) and \
                        (self.sRoi[1] - 3 <= self.yStart <= self.sRoi[1] + 3):
                    self.setCursor(QCursor(QtCore.Qt.SizeFDiagCursor))
                    self.sRoi[0] = int(self.mapToScene(e.pos()).x())
                    self.sRoi[1] = int(self.mapToScene(e.pos()).y())

                # 좌하단
                elif (self.sRoi[0] - 3 <= self.xStart <= self.sRoi[0] + 3) and \
                        (self.sRoi[3] - 3 <= self.yStart <= self.sRoi[3] + 3):
                    self.setCursor(QCursor(QtCore.Qt.SizeBDiagCursor))
                    self.sRoi[0] = int(self.mapToScene(e.pos()).x())
                    self.sRoi[3] = int(self.mapToScene(e.pos()).y())

                # 우상단
                elif (self.sRoi[2] - 3 <= self.xStart <= self.sRoi[2] + 3) and \
                        (self.sRoi[1] - 3 <= self.yStart <= self.sRoi[1] + 3):
                    self.setCursor(QCursor(QtCore.Qt.SizeBDiagCursor))
                    self.sRoi[2] = int(self.mapToScene(e.pos()).x())
                    self.sRoi[1] = int(self.mapToScene(e.pos()).y())

                # 우하단
                elif (self.sRoi[2] - 3 <= self.xStart <= self.sRoi[2] + 3) and \
                        (self.sRoi[3] - 3 <= self.yStart <= self.sRoi[3] + 3):
                    self.setCursor(QCursor(QtCore.Qt.SizeFDiagCursor))
                    self.sRoi[2] = int(self.mapToScene(e.pos()).x())
                    self.sRoi[3] = int(self.mapToScene(e.pos()).y())

                # 왼쪽 변
                elif (self.sRoi[0] - 3 <= self.xStart <= self.sRoi[0] + 3) and \
                        (self.sRoi[1] <= self.yStart <= self.sRoi[3]):
                    self.setCursor(QCursor(QtCore.Qt.SizeHorCursor))
                    self.sRoi[0] = int(self.mapToScene(e.pos()).x())
                # 오른쪽 변
                elif (self.sRoi[2] - 3 <= self.xStart <= self.sRoi[2] + 3) and \
                        (self.sRoi[1] <= self.yStart <= self.sRoi[3]):
                    self.setCursor(QCursor(QtCore.Qt.SizeHorCursor))
                    self.sRoi[2] = int(self.mapToScene(e.pos()).x())

                # 위쪽 변
                elif (self.sRoi[0] <= self.xStart <= self.sRoi[2]) and \
                        (self.sRoi[1] - 3 <= self.yStart <= self.sRoi[1] + 3):
                    self.setCursor(QCursor(QtCore.Qt.SizeVerCursor))
                    self.sRoi[1] = int(self.mapToScene(e.pos()).y())

                # 아래쪽 변
                elif (self.sRoi[0] <= self.xStart <= self.sRoi[2]) and \
                        (self.sRoi[3] - 3 <= self.yStart <= self.sRoi[3] + 3):
                    self.setCursor(QCursor(QtCore.Qt.SizeVerCursor))
                    self.sRoi[3] = int(self.mapToScene(e.pos()).y())

                # 옮기기
                elif self.sRoi[0] < self.xStart < self.sRoi[2] and self.sRoi[1] < self.yStart < self.sRoi[3]:
                    self.setCursor(QCursor(QtCore.Qt.ClosedHandCursor))
                    moveX = self.xStart - int(self.mapToScene(e.pos()).x())
                    moveY = self.yStart - int(self.mapToScene(e.pos()).y())
                    self.sRoi[0] -= moveX
                    self.sRoi[1] -= moveY
                    self.sRoi[2] -= moveX
                    self.sRoi[3] -= moveY
                self.xStart = int(self.mapToScene(e.pos()).x())
                self.yStart = int(self.mapToScene(e.pos()).y())
                copy = self.img_draw.copy()
                self.ma.makeRoi(self.sRoi, copy, (54, 65, 255))
                self.ma.loadImage(copy)

            elif self.draw and self.ma.isClassLoaded:
                x = int(self.mapToScene(e.pos()).x())
                y = int(self.mapToScene(e.pos()).y())
                img_draw = self.ma.copy.copy()
                cv2.rectangle(img_draw, (self.xStart, self.yStart), (x, y), (63, 31, 0), 2)
                self.ma.loadImage(img_draw)

        # 이미지 이동
        if Qt.RightButton and self.moveImg:
            self.setCursor(QCursor(QtCore.Qt.ClosedHandCursor))
            diff = e.pos() - self.moveStartPos
            self.moveStartPos = e.pos()
            self.horizontalScrollBar().setValue(int(self.horizontalScrollBar().value() - diff.x()))
            self.verticalScrollBar().setValue(int(self.verticalScrollBar().value() - diff.y()))

    def mouseReleaseEvent(self, e):
        if self.ma.isVideoLoaded:
            if e.button() == Qt.LeftButton:
                if self.moveRoi:
                    self.moveRoi = False
                    self.ma.rois.append(self.sRoi)
                    self.ma.copy = self.img_draw
                    for roi in self.ma.rois:
                        if roi == self.sRoi:
                            self.ma.makeRoi(roi, self.ma.copy, (54, 65, 255))
                        else:
                            self.ma.makeRoi(roi, self.ma.copy, (63, 31, 0))
                    self.ma.loadImage(self.ma.copy)
                    self.setCursor(QCursor(QtCore.Qt.CrossCursor))

                elif self.draw and self.ma.isClassLoaded:
                    self.draw = False
                    x = int(self.mapToScene(e.pos()).x())
                    y = int(self.mapToScene(e.pos()).y())
                    w = abs(self.xStart - x)
                    h = abs(self.yStart - y)
                    textX = min(self.xStart, x)
                    textY = min(self.yStart, y)
                    endX = max(self.xStart, x)
                    endY = max(self.yStart, y)
                    if w > 3 and h > 3:
                        for roi in self.ma.rois:
                            self.ma.makeRoi(roi, self.ma.copy, (63, 31, 0))
                        item = self.ma.classList.currentItem().text()
                        cv2.putText(self.ma.copy, item, (textX, textY - 8), cv2.FONT_HERSHEY_DUPLEX, 1, (63, 31, 0), 2)
                        cv2.rectangle(self.ma.copy, (self.xStart, self.yStart), (x, y), (63, 31, 0), 2)
                        self.ma.rois.append([textX, textY, endX, endY, item])
                        self.sRoi = []
                    else:
                        for roi in self.ma.rois:
                            if (roi[0] < x < roi[2]) and (roi[1] < y < roi[3]) and not self.sRoi:
                                self.ma.makeRoi(roi, self.ma.copy, (54, 65, 255))
                                self.sRoi = roi
                            else:
                                self.ma.makeRoi(roi, self.ma.copy, (63, 31, 0))
                    self.ma.loadImage(self.ma.copy)

        # 이미지 이동
        if e.button() == Qt.RightButton:
            self.moveImg = False
            self.moveStartPos = None
            self.setCursor(QCursor(QtCore.Qt.CrossCursor))

    # 줌인 아웃
    def wheelEvent(self, e):
        if self.ma.isVideoLoaded:
            if e.angleDelta().y() > 0:
                if self.factor < (5 * self.ma.scale):
                    self.factor *= 1.25
            else:
                if self.factor > self.ma.scale:
                    self.factor *= 0.8
                    if self.factor < self.ma.scale:
                        self.factor = self.ma.scale
            for roi in self.ma.rois:
                if self.sRoi == roi:
                    self.ma.makeRoi(self.sRoi, self.ma.copy, (54, 65, 255))
                else:
                    self.ma.makeRoi(roi, self.ma.copy, (63, 31, 0))
            self.ma.loadImage(self.ma.copy)
            scenePos = self.mapToScene(e.pos())
            self.resetTransform()
            self.scale(self.factor, self.factor)
            delta = self.mapToScene(e.pos()) - self.mapToScene(self.viewport().rect().center())
            self.centerOn(scenePos - delta)

    def changeRoiClass(self):
        if self.sRoi:
            img_draw = self.ma.showImg.copy()
            for roi in self.ma.rois:
                if roi == self.sRoi:
                    item = self.ma.classList.currentItem().text()
                    roi[4] = self.sRoi[4] = item
                    self.ma.makeRoi(self.sRoi, img_draw, (54, 65, 255))
                else:
                    self.ma.makeRoi(roi, img_draw, (63, 31, 0))
            self.ma.copy = img_draw
            self.ma.loadImage(self.ma.copy)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MyApp()
    sys.exit(app.exec_())
