import threading
import sys
import traceback
from time import sleep



class Tello8889Sensor:
    """
    Tello 8889 port로 명령을 수신하는 클래스
    """
    
    #=====Tello8889Sensor의 인스턴스를 생성시 실행될 함수=====
    def __init__(self, main):
        self.__printc("생성")
        self.__stop_event = main.stop_event
        self.__main = main
        self.__planner = main.planner
        self.__socket = main.socket8889
        
        #스레드 실행
        self.__thr_sensor = threading.Thread(target=self.__func_sensor, daemon=True)
        self.__thr_sensor.start()
    
    
    
    #=====스레드에서 실행될 함수=====
    def __func_sensor(self):
        self.__printf("실행",sys._getframe().f_code.co_name)
        try:
            while not self.__stop_event.is_set() and not hasattr(self.__main, 'virtual_controller'):
                self.__printf("대기중",sys._getframe().f_code.co_name)
                sleep(1)
            
            self.__virtual_controller = self.__main.virtual_controller
            
            while not self.__stop_event.is_set():
                data = self.take_data_from_sensor()
                info = self.change_data_to_info(data)
                self.save_to_planner(info)
                    
        except Exception as e:
            self.__printf("ERROR {}".format(e),sys._getframe().f_code.co_name)
            print(traceback.format_exc())
        
        self.__printf("종료",sys._getframe().f_code.co_name)
        
        #virtual controller 종료
        try:
            self.__virtual_controller.onClose()
        except Exception as e:
            self.__printf("ERROR {}".format(e),sys._getframe().f_code.co_name)
            print(traceback.format_exc())
            
    
    
    def take_data_from_sensor(self): 
        """
        센서로부터 data를 가져온다
        """
        data:bytes = self.__socket.recv(1024)
        return data
    
    
    def change_data_to_info(self, data: bytes):
        """
        data를 Planner가 이해할 수 있는 info로 변경한다
        """
        info:str = data.decode('utf-8')
        return info
    
    
    def save_to_planner(self, info: str):
        """
        info를 출력한다.
        """
        
        #cmd return
        self.__planner.set_info_8889Sensor_cmd(info)
        if info != "ok":
            print("[Tello8889Sensor]",info)


    
    
    #=====실행내역 출력을 위한 함수=====
    #클래스명을 포함하여 출력하는 함수
    def __printc(self,msg:str):
        print("[{}] {}".format(self.__class__.__name__,msg))
    
    #클래스명 + 함수명을 출력하는 함수
    def __printf(self,msg:str,fname:str):
        self.__printc("[{}]: {}".format(fname, msg))