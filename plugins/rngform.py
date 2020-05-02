import sys
import time
import random
import itertools

from PyQt5 import QtCore, QtWidgets
from PyQt5.uic import loadUi 
from PyQt5.QtWidgets import QWidget, QApplication, QHBoxLayout
from PyQt5.QtCore import Qt

from classes.common import *

class RNGForm(QWidget):
    """ генератор случайных вариантов - пример плагина"""
    def __init__(self, database):
        super(RNGForm, self).__init__()

        self.widget = loadUi('plugins\\rngform.ui', self)
        self.db=database
        # Connect the trigger signal to a slot.
        self.db.databaseOpened[str].connect(self.onDatabaseOpened)
        self.db.databaseClosed[str].connect(self.onDatabaseClosed)

        # Connect the widgets signal to a slot.
        self.widget.pushButtonGenerate.clicked.connect(self.onGenerateClick) 

        # если загружаем плагин уже при открытой базе данных
        if not self.db.isClosed:
            self.databaseOpened(self.db.path)

    def status_message(self,*args):
        self.widget.plainTextEdit.appendPlainText("status:"+''.join(map(str, args)) )
        pass #end statusMessage

    def error_message(self,*args):
        self.widget.plainTextEdit.appendPlainText("error:"+''.join(map(str, args)) )
        pass #end errorMessage

    @QtCore.pyqtSlot(str, name='onDatabaseOpened')
    def databaseOpened(self,name):

        self.allow_multiple=self.db.lottery_config.IsFonbet or self.db.lottery_config.IsTop3

        self.widget.spinBoxNumberOfBalls1.setValue(self.db.lottery_config.NumberOfBalls1);
        self.widget.spinBoxNumberOfBalls2.setValue(self.db.lottery_config.NumberOfBalls2);

        self.widget.spinBoxStartOfBalls1.setValue(self.db.lottery_config.StartOfBalls1);
        self.widget.spinBoxStartOfBalls2.setValue(self.db.lottery_config.StartOfBalls2);

        self.widget.spinBoxEndOfBalls1.setValue(self.db.lottery_config.EndOfBalls1);
        self.widget.spinBoxEndOfBalls2.setValue(self.db.lottery_config.EndOfBalls2);


    @QtCore.pyqtSlot(str, name='onDatabaseClosed')
    def databaseClosed(self,name):
        #self.widget.plainTextEdit.setPlainText('File {} closed'.format(name));
        pass

    @QtCore.pyqtSlot(name='onGenerateClick')
    def pushButtonGenerateClick(self):
        self.widget.pushButtonGenerate.setEnabled(False)
        nob1= self.widget.spinBoxNumberOfBalls1.value()
        sob1= self.widget.spinBoxStartOfBalls1.value()
        eob1= self.widget.spinBoxEndOfBalls1.value()

        nob2= self.widget.spinBoxNumberOfBalls2.value()
        sob2= self.widget.spinBoxStartOfBalls2.value()
        eob2= self.widget.spinBoxEndOfBalls2.value()

        count= self.widget.spinBoxVariantsCount.value()

        sort=self.widget.checkBoxSort.isChecked()

        if self.allow_multiple: sort = False

        start = time.time()
        try:
            
            try:
                balls_list= generate(nob1, sob1, eob1, nob2, sob2, eob2, count, self.allow_multiple, sort)
                str_list = []
                for balls in balls_list:
                    str_list.append(printf(balls))

                self.widget.plainTextEdit.appendPlainText('\r\n'.join(str_list))
            except Exception as e:
                self.error_message('ошибка generate: ', e)
           
        finally:
            self.widget.pushButtonGenerate.setEnabled(True)
        end = time.time()
        self.status_message("затрачено: ",time.strftime('%H:%M:%S', time.gmtime(end - start))) 
        pass

def generate_random(nob=5,sob=1,eob=36, allow_multiple=False, sort=False):
    res=[]
    i=0
    while i<nob:
        val=random.randint(sob,eob)
        if not allow_multiple and val in res:
            continue
        res.append(val)
        i+=1

    if sort:
        res.sort()

    return res

def generate(nob1=5, sob1=1, eob1=36, nob2=0, sob2=0, eob2=0, count=3, allow_multiple=False, sort=False):
    """ Генерация случайных вариантов, возможно с дополнительными
    allow_multiple - можно повторять номера - Топ3, Тото
    sort - сортировка по возрастанию
    """
   
    balls=[]
    var_count=0
    while var_count<count:
        balls2=[]
        balls1=generate_random(nob1, sob1, eob1, allow_multiple, sort)
        if nob2>0:
                balls2=generate_random(nob2, sob2, eob2, allow_multiple, sort)
        balls.append([balls1,balls2])
        var_count+=1
        pass
     
    return balls

   
    pass #end generate

if __name__ == '__main__':
    app = QApplication(sys.argv)
    #w=RNGForm(None,None)
    balls=generate(nob1=5, sob1=1, eob1=36, nob2=0, sob2=0, eob2=0, count=3, allow_multiple=False, sort=False)
    #print(generate(5,1,36,2,2,9,2, False, False))
    for x in balls:
        for y in x:
            for p in y:
                print(p,',',end='')
            print(' | ',end='')
        print()

    sys.exit(app.exec_())