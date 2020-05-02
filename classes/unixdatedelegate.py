from PyQt5.QtWidgets import QStyledItemDelegate
from PyQt5.QtCore import Qt
import datetime
from classes.common import *

class UnixDateDelegate(QStyledItemDelegate):
    """ для отображения даты тиража в нормальном виде"""
    def __init__(self, parent, is_fulltime):
        super(UnixDateDelegate, self).__init__(parent)
        #??self.listwidget = listwidget
        self.is_fulltime = is_fulltime 

        self.time_format='%d-%m-%Y'
        if is_fulltime:
            self.time_format='%d.%m.%Y %H:%M'

    def paint(self, painter, option, index):
        painter.save()
        try:
            if index.column()==2:
                item = index.data(Qt.DisplayRole)
                painter.drawText(option.rect, Qt.AlignCenter | Qt.AlignVCenter, datetime.datetime.fromtimestamp(item).strftime(self.time_format) )
            else:
                QStyledItemDelegate.paint(self, painter, option, index) 
                pass
        except Exception as e:
            print('UnixDateDelegate error: ', e)
            dbg_except()
        painter.restore()
