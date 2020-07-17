import requests
import json
from datetime import datetime
from datetime import timezone
from classes.common import dbg_except

from classes.drawresult import DrawResult

DATASERVICE_UR='https://clientsapi11.bkfon-resource.ru/superexpress-info/DataService.svc/'

class DataImport():

    def __init__(self, parent, database):

        self.db=database
        self.added = 0 # сколько обновлено тиражей

        self.last_draw_number=self.db.lottery_config.LastDrawNumber
        self.last_draw_date=self.db.lottery_config.LastDrawDate
        self.last_fonbet_id=self.db.lottery_config.LastFonbetId
        
    def show_form(self):
        """ тут диалога нет, вывод идет в консоль""" 

        last_draw=GetLastDraw()
        print(f"Последний доступный тираж на сайте {last_draw.Id} от {last_draw.Expired}")
        self.update_draws(last_draw.Id)

    def update_draws(self, to_draw_id):
        """ обновить расчитанные тиражи c last_fonbet_id до последнего тиража to_draw_id"""

        self.added=0
        if to_draw_id<=self.last_fonbet_id:
            print("Обновления не требуется")
            return True

        try:
            for draw_id in range(self.last_fonbet_id+1, to_draw_id+1):
                print(f"Получаю данные тиража с ИД= {draw_id} ")
                raw=GetDrawing(draw_id)
                draw=Draw(raw['d'])
                print(draw)
                
                if draw.State==1:
                    # тут обрабатываем исходы и добавляем тираж
                    dr=DrawResult()
                    dr.draw_number=self.last_draw_number+1
                    dr.draw_date=draw.Expired
                    dr.fonbet_id=draw_id
                    dr.balls1=draw.Details.balls1
                    
                    if not self.db.add_draw(dr):
                        print(f"Не удалось записать тираж {draw_id}:{self.db.last_error}")
                        return False
                    
                    self.added+=1
                    self.last_draw_number+=1
                    self.last_draw_date=draw.Expired
                    self.last_fonbet_id=draw_id
                    print(f"Тираж {draw_id} добавлен")
                    continue
                elif draw.State==2:
                    print(f"Тираж {draw_id} идет прием, пропускаю")
                    continue
                elif draw.State==0:
                    print(f"Тираж {draw_id} отменен, пропускаю")
                    continue
                elif draw.State==3:
                    print(f"Тираж {draw_id} в ожидании, пропускаю")
                    continue
                pass

        except Exception as e:
            print('DataImport update_draws error: ', e)
            dbg_except()
            return False
        else:
            print('Удачно добавлено',self.added ,' тиражей')
            return True
        pass # end update_draws


def GetDrawing(id_number):
    """ Получить подробные результаты одного тиража с ИД id_number"""

    url=DATASERVICE_UR+'GetDrawing'
    data ={"id":id_number}
    response = requests.post(url, json=data)
    return response.json()
    pass

def SelectDrawings(start_from=0, count=20, sort_dir="DESC" ):
    """ Получить подробные результаты нескольких тиражей """

    url=DATASERVICE_UR+'SelectDrawings'
    data={
        "sp":{"StartFrom":start_from,"Count":count,"SortField":"Expired","SortDir":sort_dir,"Culture":"ru-RU","TimeZoneId":"","TimeZoneOffset":0,"State":[0,1,2]} #State тиража, 0 отменен, 1 расчитан, 2 идет прием, 3 в ожидании
        }
    response = requests.post(url, json=data)
    return response.json()
    pass

def GetLastDraw():
    """ Возвращает последний тираж с сайта """

    raw=SelectDrawings(0,3) # можно было и (0,1) задать
    items=raw['d']['Items']
    draws=[]
    for item in items:
        draw=Draw(item)
        draws.append(draw)

    last=sorted(draws, key=lambda res: res.Id, reverse=True)
    return last[0]
    pass


def parse_date(date_str):
    #так PEP8 не рекомендует l = lambda x: datetime.fromtimestamp(int(x[6:-2][:-3]))
    return datetime.fromtimestamp(int(date_str[6:-2][:-3]))

class Draw:
    """ Класс для тиража с сайта Фонбета"""

    class _Details:
        class _Event:
            class _Pred:
                def __init__(self, data):
                    self.Percentage=float(data['Percentage'])
                    self.Probability=float(data['Probability'])
                pass # end _Pred
            def __init__(self, data):
     
                self.Date=parse_date(data['Date'])
                self.ResultCode=str(data['ResultCode']) # "1" "X" "2"
                self.Score=str(data['Score'])
                self.Order=int(data['Order'])

                self.Draw=self._Pred(data['Draw'])
                self.Win1=self._Pred(data['Win1'])
                self.Win2=self._Pred(data['Win2'])

                self.UserDraw=self._Pred(data['UserDraw'])
                self.UserWin1=self._Pred(data['UserWin1'])
                self.UserWin2=self._Pred(data['UserWin2'])

                self.ball=0
                if self.ResultCode=="1":
                    self.ball=1
                elif self.ResultCode=="2":
                    self.ball=2
                elif self.ResultCode=="X":
                    self.ball=0
                elif self.ResultCode=="0":  # отменен
                    self.ball=-1 
                elif self.ResultCode=="None": # None еще не расчитан
                    self.ball=-1 
                else:
                    raise Exception(f"Не распознан ResultCode: {self.ResultCode}")

            pass # end _Event

        def __init__(self, data):
            self.balls1=[] # P1 P2...P15
            self.Events=[]
            order=0
            for e in data['Events']:
                event=self._Event(e)
                self.Events.append(event)
                self.balls1.append(event.ball)
                if order!=event.Order:
                    raise Exception(f"Порядок события {event.Order} не совпадает с индексом {order}")
                order+=1

            pass

        pass # end _Details

    def __init__(self, data):
        self.Details=None
        self.Complexity=float(data['Complexity'])

        if data['Details']:
            self.Details=self._Details(data['Details'])

        self.Id=int(data['Id'])
        self.CouponCount=int(data['CouponCount'])
        self.Expired=parse_date(data['Expired'])
        self.State=int(data['State'])
        self.IsBlocked=bool(data['IsBlocked'])
        self.Jackpot=float(data['Jackpot'])

        self.UnixTimestamp=int(data['Expired'][6:-2][:-3])

    def __str__(self):
        balls_str=""
        if self.Details:
            balls_str=",".join(str(x) for x in self.Details.balls1)
        return f"Id {self.Id}, Expired {self.Expired}/{self.UnixTimestamp}, State {self.State}, Balls {balls_str}"

    pass # end Draw class

