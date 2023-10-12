import cv2
from datetime import datetime

class Webcam():
    def __init__(self, cam):
        self.vid = cv2.VideoCapture(cam)

    def get_frame(self):
        # if not self.vid.isOpened():
        #     return
        #

        while True:
            _, img = self.vid.read()
            img = cv2.putText(img, datetime.now().strftime("%H:%M:%S"), (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1,
                              (255, 255, 255), 2, cv2.LINE_AA)

            yield img