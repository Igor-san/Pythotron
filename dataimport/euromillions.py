#-------
# pip install beautifulsoup4
# pip install lxml
#--------------

from PyQt5 import QtCore, QtWidgets
from PyQt5.uic import loadUi 
from PyQt5.QtWidgets import QWidget,QDialog, QApplication, QHBoxLayout
from PyQt5.QtCore import Qt

import sys
import csv
import codecs
import datetime
import time

from urllib.request import urlopen
from bs4 import BeautifulSoup

from classes.common import *
from classes.drawresult import DrawResult

class DataImport(QDialog):

    def __init__(self, parent, database):
        super(DataImport, self).__init__(parent,Qt.WindowCloseButtonHint)
        
        if (parent is None) and (database is None):
            return # для тестирования отдельно

        self.widget = loadUi('dataimport\\euromillions.ui', self)
        self.db=database
        self.stop_progress=False
        self.added = 0 # сколько обновлено тиражей
        # Connect the trigger signal to a slot.
        self.widget.pushButtonUpdate.clicked.connect(self.onUpdateClick)
        self.widget.pushButtonDiscoverLast.clicked.connect(self.onDiscoverLastClick)
        self.widget.pushButtonStop.clicked.connect(self.onButtonStopClick)
        self.widget.pushButtonClose.clicked.connect(self.onButtonCloseClick)

        self.widget.spinBoxFromDraw.setValue(self.db.lottery_config.LastDrawNumber+1)
        self.widget.spinBoxToDraw.setValue(self.get_last_draw())

    @QtCore.pyqtSlot(name='onButtonCloseClick')
    def buttonCloseClick(self):
        #self.widget.accept()
        self.accept()

    @QtCore.pyqtSlot(name='onButtonStopClick')
    def buttonStopClick(self):
        self.stop_progress=True

    @QtCore.pyqtSlot(name='onDiscoverLastClick')
    def discoverLastClick(self):
        try:
            self.widget.pushButtonDiscoverLast.setEnabled(False)
            self.widget.spinBoxToDraw.setValue(self.get_last_draw())
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

    def show_form(self):
        """ Для открытия диалога """
        self.exec_()
        pass

    def status_message(self,*args):
        self.widget.plainTextEdit.appendPlainText("status:"+''.join(map(str, args)) )
        pass #end statusMessage

    def error_message(self,*args):
        self.widget.plainTextEdit.appendPlainText("error:"+''.join(map(str, args)) )
        pass #end errorMessage

    def update(self):
        """ обновить тиражи"""
        start = time.time()
        self.status_message("начинаем обновление в ", datetime.datetime.fromtimestamp(start).strftime("%d-%m-%y %H:%M:%S"))
        fromDraw= self.widget.spinBoxFromDraw.value()
        toDraw= self.widget.spinBoxToDraw.value()
        if fromDraw>toDraw:
            self.error_message(f"начальный тираж {fromDraw} больше конечного {toDraw}")
            return False
        try:
            self.update_draws(fromDraw,toDraw)
            
        except Exception as e:
            self.error_message('ошибка обновления: ', e)

        end = time.time()
        self.status_message("затрачено: ",time.strftime('%H:%M:%S', time.gmtime(end - start)))    
        pass #end update

    def get_last_draw(self):
        """ Узнать последний номер тиража

        """
        try:
            url='http://lottery.merseyworld.com/Euro/'
            text = urlopen(url).read()
            rep1='/Euro/archive/Lott'
            rep2='.html' 
            nums=[]
            soup = BeautifulSoup(text,"lxml")
            for link in soup.find_all('a'):
                s=link.get('href')
                if s.startswith(rep1):
                    snum=s.replace(rep1, '').replace(rep2, '')
                    nums.append(int(snum))
            last_draw_num=max(nums)
            return last_draw_num
        except Exception as e:
            print('get_last_draw error: ', e)
            dbg_except()
            return 0
        pass #end get_last_draw
     
    def update_draws(self, from_num=0, to_num=0):
        """ обновить тиражи,from_num - с какого номера, to_num - по какой
    
        """
        self.stop_progress=False

        try:
            #url='http://lottery.merseyworld.com/cgi-bin/lottery?days=17&sales=0&Machine=Z&Ballset=0&order=0&show=1&year=0&display=CSV'# Только CSV нормально можно использовать
            url='http://lottery.merseyworld.com/cgi-bin/lottery?days=20&Machine=Z&Ballset=0&order=0&show=1&year=0&display=CSV'
            stream = urlopen(url)
            csvfile = csv.reader(codecs.iterdecode(stream, 'utf-8'))
            data=[]
            for line in csvfile:
                # No., Day,DD,MMM,YYYY, N1,N2,N3,N4,N5,L1,L2,  Jackpot,   Wins
                if len(line)>0 and line[0].strip().isdigit():
                    draw=DrawResult()
                    draw.draw_number=int(line[0].strip())

                    if to_num>0 and draw.draw_number>to_num: # этот тираж позднее необходимого
                        continue

                    day=(line[2].strip()).zfill(2)
                    month=line[3].strip()
                    year=line[4].strip()
                    datetime_str=year+'-'+month+'-'+day
                    draw.draw_date=datetime.datetime.strptime(datetime_str, '%Y-%b-%d')
                    draw.balls1.append(int(line[5].strip()))
                    draw.balls1.append(int(line[6].strip()))
                    draw.balls1.append(int(line[7].strip()))
                    draw.balls1.append(int(line[8].strip()))
                    draw.balls1.append(int(line[9].strip()))

                    draw.balls2.append(int(line[10].strip()))
                    draw.balls2.append(int(line[11].strip()))
                    
                    data.append(draw)
                    # на сайте номера идут по убыванию, и как только достигнем from_num можно прерывать
                    if draw.draw_number<=from_num:
                        break

            data=sorted(data, key=lambda res: res.draw_number) # отсортируем по возврастанию тиража для упорядочения записи

            self.widget.progressBar.setMaximum(len(data))
            if (self.db is not None):
                for draw in data:
                    QApplication.processEvents()
                    if self.stop_progress: # юзер стоп нажал
                        break
                    if not self.db.add_draw(draw):
                        self.error_message(f"Не удалось записать тираж № {draw.draw_number}:{self.db.last_error}")
                        return False
                    self.added+=1
                    self.widget.progressBar.setValue(self.added)
                pass # end save to db

            self.widget.progressBar.setValue(0)
            return True

        except Exception as e:
            print('update_draws error: ', e)
            dbg_except()
            
        pass #end update_draws

if __name__ == '__main__':
    app = QApplication(sys.argv)
    w=DataImport(None,None)
    #w.update_draws(1258)
    w.get_last_draw()

    sys.exit(app.exec_())