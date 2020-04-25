from PyQt5 import QtCore, QtWidgets
from PyQt5.uic import loadUi 
from PyQt5.QtWidgets import QWidget,QDialog, QApplication, QHBoxLayout
from PyQt5.QtCore import Qt

import sys
import csv
import codecs
import datetime
import time

import requests
import json

from classes.common import *
from classes.drawresult import DrawResult

class DataImport(QDialog):

    def __init__(self, parent, database):
        super(DataImport, self).__init__(parent,Qt.WindowCloseButtonHint)
        
        if (parent is None) and (database is None):
            return # для тестирования отдельно

        self.widget = loadUi('dataimport\\eurojackpot.ui', self)
        self.db=database
        self.datalist=None #тут будут отпарсенные тиражи для записи в базу
        self.stop_progress=False
        self.added = 0 # сколько обновлено тиражей

        # Connect the trigger signal to a slot. - нельзя подписываться к базе так как форма может уничтожится а сигнал останется, а отписаться на destroyed неполучится
        self.widget.pushButtonUpdate.clicked.connect(self.onUpdateClick)
        self.widget.pushButtonDiscoverLast.clicked.connect(self.onDiscoverLastClick)
        self.widget.pushButtonStop.clicked.connect(self.onButtonStopClick)
        self.widget.pushButtonClose.clicked.connect(self.onButtonCloseClick)

        if self.db.lottery_config.LastDrawDate==datetime.date.min:
            next_week= datetime.datetime(2012, 3, 23) #23.03.2012 первый тираж евроджекпота
        else:
            next_week=self.db.lottery_config.LastDrawDate+datetime.timedelta(weeks = 1)
        self.widget.comboBoxFromDate.addItem(next_week.strftime("%d.%m.%Y"),next_week.date())

        self.get_last_draw()


    @QtCore.pyqtSlot(name='onButtonCloseClick')
    def buttonCloseClick(self):
        self.widget.accept()

    @QtCore.pyqtSlot(name='onButtonStopClick')
    def buttonStopClick(self):
        self.stop_progress=True

    @QtCore.pyqtSlot(name='onDiscoverLastClick')
    def discoverLastClick(self):
        try:
            self.widget.pushButtonDiscoverLast.setEnabled(False)
            self.get_last_draw()

        finally:
            self.widget.pushButtonDiscoverLast.setEnabled(True)
        pass #end 

    @QtCore.pyqtSlot(name='onUpdateClick')
    def updateClick(self):
        try:
            self.widget.pushButtonUpdate.setEnabled(False)
            self.update()
        finally:
            self.widget.pushButtonUpdate.setEnabled(True)
        pass #end updateClick

    def status_message(self,*args):
        self.widget.plainTextEdit.appendPlainText("status:"+''.join(map(str, args)) )
        pass #end statusMessage

    def error_message(self,*args):
        self.widget.plainTextEdit.appendPlainText("error:"+''.join(map(str, args)) )
        pass #end errorMessage

    def update(self):
        """ обновить тиражи"""
        start = time.time()
        #self.status_message("начинаем обновление в ", datetime.datetime.fromtimestamp(start).strftime("%d-%m-%y %H:%M:%S"))
        fromDrawDate=self.widget.comboBoxFromDate.currentData()
        toDrawDate=self.widget.comboBoxToDate.currentData()

        if fromDrawDate>toDrawDate:
            self.error_message(f"начальный тираж {fromDrawDate} больше конечного {toDrawDate}")
            return False
        try:
            self.status_message(f"Начинаем обновлять тиражи с {fromDrawDate} по {toDrawDate} в {datetime.datetime.fromtimestamp(start).strftime('%d-%m-%y %H:%M:%S')}")
            self.update_draws(fromDrawDate,toDrawDate)

        except Exception as e:
            self.error_message('ошибка обновления: ', e)

        end = time.time()
        self.status_message("затрачено: ",time.strftime('%H:%M:%S', time.gmtime(end - start)))    
        pass #end update

    def get_last_draw(self):
        """ Узнать последнюю дату тиража (номеров по порядку нет) - но тут мы сразу все тиражи с шарами получаем но без выигрышей

        """
        try:
           
            url='https://www.eurojackpot.com/data'
            text = requests.get(url).text
            #нужно привести к json
            i1=text.index('window.mrm.data.gewinnzahlen=') 
            i2=text.index('window.mrm=window.mrm||{};',i1)
            text=text[i1+29:i2-2] #29= len(window.mrm.data.gewinnzahlen=)
            lines=json.loads(text)
            self.datalist=[]
            for date_str in lines:
                draw=DrawResult()
                draw_date=datetime.datetime.strptime(date_str, '%d.%m.%Y') #тут нельзя date() иначе при записи timestamp() будет недоступен  #только год месяц день без времени!
                self.widget.comboBoxToDate.addItem(date_str,draw_date.date())
                draw.draw_date=draw_date

                for b in lines[date_str][0]['numbers']:
                    draw.balls1.append(int(b))
 
                for b in lines[date_str][1]['numbers']:
                    draw.balls2.append(int(b))

                self.datalist.append(draw)

            self.datalist=sorted(self.datalist, key=lambda res: res.draw_date) #сортируем по возрастанию даты чтобы назначить нумератор
            for i, draw in enumerate(self.datalist,1):
                draw.draw_number=i #Присвоим номер тиража 
       

            #проверим на всякий случай, если в базе уже есть тиражи
            if not self.db.lottery_config.LastDrawDate==datetime.date.min:
                my_last= next((x for x in self.datalist if x.draw_date.date() == self.db.lottery_config.LastDrawDate.date()), None)
                if my_last is None:
                    self.error_message(f"Среди полученных дат нет последней даты из базы {self.db.lottery_config.LastDrawDate} - проверьте!");
                else:
                    if my_last.draw_number!=self.db.lottery_config.LastDrawNumber:
                        self.error_message(f"Номер последней последнего тиража {self.db.lottery_config.LastDrawDate}/{self.db.lottery_config.LastDrawNumber} \
                        не соответствует номеру присвоенному по данным с сайта {my_last.draw_date}/{my_last.draw_number}- проверьте!");

            return self.datalist[len(self.datalist)-1].draw_date

        except Exception as e:
            self.error_message('get_last_draw error: ', e)
            dbg_except()
            return 0
        pass #end get_last_draw
     
    def update_draws(self, from_date=datetime.date.min, to_date=datetime.date.max):
        """ обновить тиражи,from_date - с какой даты, to_num - по какую дату включительно   """
        self.stop_progress=False
        try:

            self.widget.progressBar.setMaximum(weeks_between(from_date,to_date))
            if (self.db is not None):
                for draw in self.datalist:
                    if from_date<=draw.draw_date.date()<=to_date:
                        QApplication.processEvents()
                        if self.stop_progress: # юзер стоп нажал
                            break
                        #нужно получить выигрыши и распарсить
                        draw.wins= parse_win(draw.draw_date)
                        if draw.wins is None:
                            self.error_message(f"Не удалось получить выигрыши для тиража № {draw.draw_number}")
                            return False
                        if not self.db.add_draw(draw):
                            self.error_message(f"Не удалось записать тираж № {draw.draw_number}:{self.db.last_error}")
                            return False
                        self.added+=1
                        self.widget.progressBar.setValue(self.added)
                pass # end save to db

            self.widget.progressBar.setValue(0)
            self.status_message(f"Добавлено {self.added} тиражей")
            return True

        except Exception as e:
            self.error_message('update_draws error: ', e)
            dbg_except()
            
        pass #end update_draws


def parse_win(date):
    try:
        url='https://www.eurojackpot.com/quota?date='+ date.strftime('%d.%m.%Y')
        text = requests.get(url).text
        lines=json.loads(text)
        if not lines["success"]:
            return None

        wins = {} 
        for quota in lines["quota"]:
            win_cat= quota["winningCategoryShort"]
            win_cat=win_cat.replace(" ", "")
            winners= quota["winners"]
            winners=winners.replace(".", "")
            winners=int(winners) #количество выигрывших, нужно удалить точку
            if winners==0:
                wins[win_cat]=0.0
                continue
            amount= quota["amount"] #выигрыш, нужно удалить точку и символ евро
            amount = amount.encode('ascii',errors='ignore').decode("utf-8")
            amount=amount.replace(".", "")
            amount=string_to_float(amount)
            wins[win_cat]=amount

        return wins
    except Exception as e:
        print('parse_win error: ', e)
        dbg_except()
        return None
    pass

if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    date=datetime.datetime(2020, 4, 18)
    print(parse_win(date))
    sys.exit(app.exec_())