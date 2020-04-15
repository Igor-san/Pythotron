import sys
from PyQt5 import QtCore, QtWidgets
from PyQt5.uic import loadUi 
from PyQt5.QtWidgets import QWidget, QApplication, QHBoxLayout
from PyQt5.QtCore import Qt
#from PyQt5.QtSql import QSqlDatabase, QSqlQuery, QSqlTableModel
from pathlib import Path

from classes.common import *
from classes.unixdatedelegate import UnixDateDelegate

class HistoryForm(QWidget):

    def __init__(self, database, *args, **kwargs):
        super(HistoryForm, self).__init__(*args, **kwargs)
        #print(Path().absolute())
        self.widget = loadUi('forms\\history.ui', self) #, self обязательно иначе  QBasicTimer can only be used with threads started with QThread
        self.db =database 
        self.updateEnabled=False
        self.dataImportPath=Path().absolute().joinpath(DATAIMPORT_FOLDER)
        #print(self.dataImportPath)

    def closeEvent(self, event):
        self.db.close()

    def closeFile(self):
        self.db.close()
        self.updateEnabled=False

    def openFile(self,file):
        self.closeFile() #закрываем предыдущий
        try:
            self.db.open(file)
            self.__prepareViewHistory()
            self.__prepareViewConfig()
            if self.db.lottery_config.DataImportPlugin and self.dataImportPath.joinpath(self.db.lottery_config.DataImportPlugin+'.py').is_file():
                self.updateEnabled=True

        except Exception as e:
            print('HistoryForm error: ', e)
            dbg_except()

    def __prepareViewConfig(self):
        self.widget.tableViewConfig.setModel(self.db.configmodel)

    def __prepareViewHistory(self):
       
        self.widget.tableViewHistory.setModel(self.db.historymodel)
        self.widget.tableViewHistory.setSortingEnabled(True)
        self.widget.tableViewHistory.sortByColumn(1,Qt.DescendingOrder)

        self.widget.tableViewHistory.setColumnHidden(0, True) #скрываем столбец с индексом записи
        #настраиваем ширины
        self.widget.tableViewHistory.setColumnWidth(DRAWNUMBER_COLUMN_INDEX,45)
 
        self.widget.tableViewHistory.setColumnWidth(UNIXTIME_COLUMN_INDEX,80)
        step=UNIXTIME_COLUMN_INDEX+1
        for i in range (UNIXTIME_COLUMN_INDEX+1,self.db.lottery_config.NumberOfBalls1+UNIXTIME_COLUMN_INDEX+1):
            self.widget.tableViewHistory.setColumnWidth(step,35)
            step+=1

        for i in range (step,self.db.lottery_config.NumberOfBalls2+step+1):
            self.widget.tableViewHistory.setColumnWidth(step,30)
            step+=1

        #if not self.db.IsNtr: #в НТР у нас обычные даты - но тогда сортировка не так работает по дате
        self.widget.tableViewHistory.setItemDelegate(UnixDateDelegate(self, self.widget.tableViewHistory)) #преобразовывать юниксдату
        
        self.widget.tableViewHistory.setAlternatingRowColors(True);
    pass #compareDraws
