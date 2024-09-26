import torch
import numpy as np
from PIL import Image, ImageTk
import cv2
import ultralytics  # YOLOv8을 위해 필요한 라이브러리 (설치 필요: `pip install ultralytics`)

class YOLOv8:
    """
    객체인식을 담당하는 클래스(YOLOv8 사용)
    """
    
    def __init__(self):
        # 모델 객체 생성
        # YOLOv8 모델을 로드 (YOLOv8s)
        self.__model = ultralytics.YOLO('yolov8s.pt')  # 경로를 수정해서 직접 로컬 모델 사용 가능
        self.__classes = self.__model.names
        self.__device = 'cuda' if torch.cuda.is_available() else 'cpu'
        print(">>>>>>GPU 사용:", self.__device)
    
    def detect_from_frame(self, frame: np.ndarray, tof: int): 
        """
        frame에서 객체를 감지하고, 윈도우를 적용한 image와 윈도우 리턴
        """
        # 감지한 객체 윈도우들의 좌표를 저장할 리스트
        window_coor_list = []
        
        # 프레임에서 감지한 객체들의 레이블들, 좌표들이 들어있는 리스트
        results = self.__model(frame, stream=True, verbose=False)        
        
        for result in results:
            # 객체 검출 모드
            boxes = result.boxes.xyxy.cpu().numpy().astype(int)  # 검출된 객체의 바운딩 박스 좌표
            confs = result.boxes.conf.cpu().numpy()  # 검출된 객체의 신뢰도
            classes = result.boxes.cls.cpu().numpy().astype(int)  # 검출된 객체의 클래스
            
            for box, conf, cls in zip(boxes, confs, classes):
                # 바운딩 박스 그리기
                x1 = box[0]
                y1 = box[1]
                x2 = box[2]
                y2 = box[3]
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                # 클래스와 신뢰도 표시
                label = f'{self.__model.names[cls]} {conf:.2f}'
                cv2.putText(frame, label, (box[0], box[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                # text = "{}: ({},{}), ({},{})".format(name, x1, y1, x2, y2)
                text = f"{label}: {conf:.2f}"
                
                # 텍스트의 위치 설정 (바운딩 박스 하단 중앙)
                text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.9, 2)[0]
                text_x = x1 + (x2 - x1) // 2 - text_size[0] // 2  # 바운딩 박스 가로 중심
                text_y = y2 + text_size[1] + 10  # 바운딩 박스 바로 아래
                
                # 프레임에 텍스트 추가
                cv2.putText(frame, text, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2)
        
        
        # frame을 image로 변환
        image = Image.fromarray(frame)
        
        # image를 imagetk 형식으로 변환
        image = ImageTk.PhotoImage(image)
        
        return image