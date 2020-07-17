import sys
import os

from PyQt5 import QtCore, QtWidgets
from PyQt5.uic import loadUi 
from PyQt5.QtWidgets import QDialog, QApplication, QHBoxLayout, QFileDialog
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette
from classes.database import Db

import classes.common as common
from classes.settings import Settings

class OptionsForm(QDialog):

    def __init__(self,  *args, **kwargs):
        super(OptionsForm, self).__init__(*args, **kwargs)
        self.widget = loadUi('forms\\optionsform.ui', self)

        self.disabled_plugins=[]
        self.available_plugins=[]

        self._load_options()

        self.widget.buttonBox.accepted.connect(self.onAcceptClick)
        self.widget.buttonBox.rejected.connect(self.onRejectClick)

        self.widget.buttonOpenWavLocation.clicked.connect(self.onOpenWavLocationClick)
        self.widget.buttonPlayWav.clicked.connect(self.onPlayWavClick)


    @QtCore.pyqtSlot(name='onRejectClick')
    def rejectClick(self):
        self.reject()

    @QtCore.pyqtSlot(name='onAcceptClick')
    def acceptClick(self):
        ''' временное сохранение изменений, в конфиге сохранится при выходе из программы '''
        Settings.load_last_opened_database = self.widget.checkBoxLoadLastOpenedDatabase.isChecked()
        Settings.wav_file_path = self.widget.lineEditWavLocation.text()

        self._set_disabled_plugins()
        self.widget.accept()
        self.close()
        pass # end accept

    @QtCore.pyqtSlot(name='onOpenWavLocationClick')
    def openWavLocationClick(self):
        ''' выбор воспроизводимого файла '''
        try:

            file_name, _ = QFileDialog.getOpenFileName(parent=self, caption= 'Open file', directory=".", filter= "WAV files(*.wav)")
            if not file_name:
                return

            self.widget.lineEditWavLocation.setText(file_name)

        except Exception as e:
            print('OptionsForm:openWavLocationClick error: ', e)
            dbg_except()
        pass # end openWavLocationClick

    @QtCore.pyqtSlot(name='onPlayWavClick')
    def playWavClick(self):
        ''' проигрывание воспроизводимого файла '''

        try:
            palette = QPalette();
            path = self.widget.lineEditWavLocation.text()
            if os.path.isfile(path):
                common.play_sound(path)
                palette.setColor(QPalette.Text, Qt.black);
                self.widget.lineEditWavLocation.setPalette(palette);
            else:
                print(f"File {path} not exist")
                palette.setColor(QPalette.Text, Qt.red);
                self.widget.lineEditWavLocation.setPalette(palette);

        except Exception as e:
            print('OptionsForm:playWavClick error: ', e)
            dbg_except()
        pass # end playWavClick

    def _load_options(self):

        self.widget.checkBoxLoadLastOpenedDatabase.setChecked(Settings.load_last_opened_database)
        if Settings.wav_file_path: self.widget.lineEditWavLocation.setText(Settings.wav_file_path)

        pass # end _load_options

    def _set_disabled_plugins(self):
        self.disabled_plugins=[]
        for i in range(self.widget.listWidgetPlugins.count()):
            if self.widget.listWidgetPlugins.item(i).checkState() != QtCore.Qt.Checked:
                self.disabled_plugins.append(self.widget.listWidgetPlugins.item(i).text())
            pass

    def _create_checkbox(self, checked):
            item = QtWidgets.QListWidgetItem()
            item.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
            if checked:
                item.setCheckState(QtCore.Qt.Checked)
            else:
                item.setCheckState(QtCore.Qt.Unchecked)
            return item

    def create_plugins_list(self):
        
        self.widget.listWidgetPlugins.clear()
        
        for name in self.available_plugins:
                chkBox = self._create_checkbox(name not in self.disabled_plugins)
                chkBox.setText(name)
                self.widget.listWidgetPlugins.addItem(chkBox)

    #def create_plugins_listOld(self):
        
    #    self.widget.listWidgetPlugins.clear()
        
    #    for p in self.loaded_plugins:
    #            chkBox = self._create_checkbox(True)
    #            chkBox.setText(p)
    #            self.widget.listWidgetPlugins.addItem(chkBox)
                

    #    for p in self.disabled_plugins:
    #            chkBox = self._create_checkbox(False)
    #            chkBox.setText(p)
    #            self.widget.listWidgetPlugins.addItem(chkBox)

        