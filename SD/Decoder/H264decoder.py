from SD.Decoder.h264_39 import h264decoder
import numpy as np

"""
H.264: 2003년에 발표된 동영상 표준 규격으로, 텔로에서도 사용
"""    
    
#입력된 bytes를 frame으로 디코딩 후, 이를 모아 list로 반환 
def decode(decoder: h264decoder, packet_data: bytes):
    
    res_frame_list = []
    frames = decoder.decode(packet_data) #입력받은 raw H.264 data 배열을 디코딩

    for framedata in frames: # framedata는 4개 요소의 튜플로 구성
        frame, width, height, linesize = framedata

        if frame is not None:
            frame = np.fromstring(frame, dtype=np.ubyte, count=len(frame), sep='') #UTF-8 인코딩을 통해 문자열을 바이트로 변환
            frame = frame.reshape((height, int(linesize / 3), 3)) #바이트 배열을 화면 크기에 맞게 변환
            frame = frame[:, :width, :]
            res_frame_list.append(frame) #frame을 변환 후 res_frame_list에 추가

    return res_frame_list