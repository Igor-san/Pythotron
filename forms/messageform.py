import sys
from PyQt5 import QtCore, QtWidgets
from PyQt5.uic import loadUi 
from PyQt5.QtWidgets import QWidget, QApplication, QHBoxLayout
from PyQt5.QtCore import Qt
from classes.database import Db

class MessageForm(QWidget):

    def __init__(self,  *args, **kwargs):
        super(MessageForm, self).__init__(*args, **kwargs)
        self.widget = loadUi('forms\\messageform.ui', self)

