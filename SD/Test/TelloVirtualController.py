import sys
import tkinter
import threading
from PIL import ImageTk
from time import sleep
import traceback
from pynput import keyboard  # 여러 키 입력을 처리하기 위한 라이브러리 추가s


class TelloVirtualController:
    """
    가상의 컨트롤러를 의미하는 클래스
    -GUI 화면을 띄움
    -Tello의 ToF값을 화면에 출력
    -YOLO의 감지화면을 화면에 출력
    -키보드 및 화면의 버튼을 통해 Tello를 조작
    -thread_stay_connection 스레드를 통해 지속적으로 Tello에게 "command" 메세지를 전달
    -종료시 stop_event를 실행
    """



    #=====VirtualController의 인스턴스를 생성시 실행될 함수=====
    def __init__(self, main):
        self.__printc("생성")
        
        #Planner
        self.__socket8889 = main.socket8889
        self.__tello_address = main.tello_address
        self.__planner = main.planner

        #종료를 위한 stop_event
        self.__stop_event:threading.Event = main.stop_event
        self.__thread_stop_event = threading.Event()

        #Tello 조작시 가해질 힘(0~100)
        self.__speed = 50
        self.__shift_multiplier = 1  # Shift로 가속 시 1.5배 속도를 반영하기 위한 변수
        self.__pre_cmd = ""
        
        # 현재 누르고 있는 키들을 저장할 메모리
        self.keys_pressed = set()
        
        #화면 기본 설정
        self.root = tkinter.Tk()  # GUI 화면 객체 생성
        self.root.geometry("-10+0")
        # self.root.attributes('-fullscreen',True)
        self.root.wm_title("DRL TEST for RMTT") #GUI 화면의 title 설정  
        self.root.wm_protocol("WM_DELETE_WINDOW", self.onClose) #종료버튼을 클릭시 실행할 함수 설정

        #화면에 띄울 문구 설정
        self.__text_speed = tkinter.Label(self.root, text=f"SPEED: {self.__speed}")
        self.__text_speed.pack(side="top")
        self.__text_keyboard = tkinter.Label(self.root, justify="left", text="""
        Straight Moving: Arrow
        Up and Down: W,S
        Rotate: A,D
        Takeoff-Lading: K,L
        Stop: ESC
        Speed-UP and down: P,O
        Shift+: Acceleration
        """)
        self.__text_keyboard.pack(side="top")

        #영상을 출력하기 위한 panel 선언
        self.__panel_image = None
        
        # 키보드 입력 감지 시작
        self.listener = keyboard.Listener(on_press=self.on_keypress, on_release=self.on_keyrelease)
        self.listener.start()

        # 카메라 스트리밍 시작 스레드
        if hasattr(self.__planner, 'get_info_11111Sensor_frame'):
            self.__thread_print_video = threading.Thread(target=self.func_print_video, daemon=True)
            self.__thread_print_video.start()
    


    #=====버튼을 클릭했을 때 실행될 함수들=====
    def land(self): #return: Tello의 receive 'OK' or 'FALSE'
        self.send_cmd('land')

    def takeoff(self): #return: Tello의 receive 'OK' or 'FALSE'
         self.send_cmd('takeoff')



    #=====키보드 입력 처리 함수들=====
    def on_keypress(self, key):

        # 속도 조절 및 기타 기능
        if key == keyboard.KeyCode.from_char('p'):
            self.__speed = min(self.__speed + 10, 100)  # 최대 100까지 속도 증가
            self.__text_speed.config(text=f"SPEED: {self.__speed}")  # 속도 라벨 업데이트
        elif key == keyboard.KeyCode.from_char('o'):
            self.__speed = max(self.__speed - 10, 10)   # 최소 10까지 속도 감소
            self.__text_speed.config(text=f"SPEED: {self.__speed}")  # 속도 라벨 업데이트
            
        elif key == keyboard.KeyCode.from_char('t'):
            self.send_cmd(f"takeoff")
        elif key == keyboard.KeyCode.from_char('l'):
            self.send_cmd(f"land")
        elif key == keyboard.Key.esc:
            self.send_cmd(f"stop")

        # Shift 누르면 속도 배율 증가
        elif key == keyboard.Key.shift:
            self.__shift_multiplier = 1.5
            
        # 키가 눌릴 때
        elif key not in self.keys_pressed:
            self.keys_pressed.add(key)
            self.update_rc_control()

        


    def on_keyrelease(self, key):
        # 키가 떼어졌을 때
        if key in self.keys_pressed:
            self.keys_pressed.remove(key)

        # Shift 떼면 속도 배율 원상복구
        elif key == keyboard.Key.shift:
            self.__shift_multiplier = 1.0

        self.update_rc_control()


    # 다중 키 입력을 받아 RC 명령을 업데이트하는 함수 (rc a b c d)
    def update_rc_control(self):
        lr = 0  # 좌우 이동 (a, d) => roll(a)
        fb = 0  # 전방/후방 이동 (w, s) => pitch(b)
        ud = 0  # 상하 이동 (위/아래 화살표) => throttle(c)
        yaw = 0  # 회전 (좌/우 화살표) => yaw(d)

        if keyboard.Key.left in self.keys_pressed:
            lr -= self.__speed
        if keyboard.Key.right in self.keys_pressed:
            lr += self.__speed

        if keyboard.Key.up in self.keys_pressed:
            fb += self.__speed
        if keyboard.Key.down in self.keys_pressed:
            fb -= self.__speed

        if keyboard.KeyCode.from_char('w') in self.keys_pressed or keyboard.KeyCode.from_char('W') in self.keys_pressed:
            ud += self.__speed
        if keyboard.KeyCode.from_char('s') in self.keys_pressed or keyboard.KeyCode.from_char('S') in self.keys_pressed:
            ud -= self.__speed

        if keyboard.KeyCode.from_char('a') in self.keys_pressed or keyboard.KeyCode.from_char('A') in self.keys_pressed:
            yaw -= self.__speed
        if keyboard.KeyCode.from_char('d') in self.keys_pressed or keyboard.KeyCode.from_char('D') in self.keys_pressed:
            yaw += self.__speed

        # Shift 적용 속도 조절
        lr = int(lr * self.__shift_multiplier)
        fb = int(fb * self.__shift_multiplier)
        ud = int(ud * self.__shift_multiplier)
        yaw = int(yaw * self.__shift_multiplier)

        # RC 제어 전송
        self.send_rc_control(lr, fb, ud, yaw)

    def send_rc_control(self, lr, fb, ud, yaw):
        self.send_cmd(f"rc {lr} {fb} {ud} {yaw}")

    #=====카메라 스트리밍을 화면에 출력하는 함수=====
    def func_print_video(self):
        self.__printf("실행",sys._getframe().f_code.co_name)
        try:
            while not self.__thread_stop_event.is_set():
                # ORIGIN START
                image:ImageTk.PhotoImage = self.__planner.get_info_11111Sensor_image()
                # ORIGIN END

                if self.__panel_image is None: 
                    self.__panel_image:tkinter.Label = tkinter.Label(image=image)
                    self.__panel_image.image = image
                    self.__panel_image.pack(side="right", padx=10, pady=10)
                
                else:
                    self.__panel_image.configure(image=image)
                    self.__panel_image.image = image


        except Exception as e:
            self.__printf("ERROR {}".format(e),sys._getframe().f_code.co_name)
            print(traceback.format_exc())
        
        self.__printf("종료",sys._getframe().f_code.co_name)
    


    #=====Tello에게 명령을 전송하는 함수=====
    def send_cmd(self, msg:str):
        # self.__lock.acquire() #락 획득
        try:
            if self.__pre_cmd != msg:
                self.__socket8889.sendto(msg.encode('utf-8'), self.__tello_address)
                self.__pre_cmd = msg
                self.__printf(msg,"send_cmd")
        except Exception as e:
            self.__printf("ERROR {}".format(e),sys._getframe().f_code.co_name)
            print(traceback.format_exc())
        # self.__lock.release() #락 해제
    

    #=====종료버튼을 클릭시 실행할 함수=====
    def onClose(self):
        self.send_cmd("land")
        sleep(0.5)
        self.send_cmd("motoroff")
        sleep(0.5)
        
        #update_tof, print_video를 종료
        self.__thread_stop_event.set()
        self.__printc("종료중... >> thread stop event 실행")    
        
        #모든 스레드 종료 명령인 stop_event를 실행
        self.__stop_event.set()
        self.__printc("종료중... >> global stop event 실행")
        
        #화면 종료 
        self.root.quit() 
        self.__printc("종료")
        
        #현 스레드 종료
        exit()


    #=====실행내역 출력을 위한 함수=====
    #클래스명을 포함하여 출력하는 함수
    def __printc(self,msg:str):
        print("[{}] {}".format(self.__class__.__name__,msg))
    
    
    #클래스명 + 함수명을 출력하는 함수
    def __printf(self,msg:str,fname:str):
        self.__printc("[{}]: {}".format(fname, msg))