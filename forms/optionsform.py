import sys
from PyQt5 import QtCore, QtWidgets
from PyQt5.uic import loadUi 
from PyQt5.QtWidgets import QDialog, QApplication, QHBoxLayout
from PyQt5.QtCore import Qt
from classes.database import Db
import classes.program_options as program_options

class OptionsForm(QDialog):

    def __init__(self,  *args, **kwargs):
        super(OptionsForm, self).__init__(*args, **kwargs)
        self.widget = loadUi('forms\\optionsform.ui', self)

        self.disabled_plugins=[]
        self.available_plugins=[]

        self._load_options()

        self.widget.buttonBox.accepted.connect(self.onAcceptClick)
        self.widget.buttonBox.rejected.connect(self.onRejectClick)

    @QtCore.pyqtSlot(name='onRejectClick')
    def rejectClick(self):
        self.reject()

    @QtCore.pyqtSlot(name='onAcceptClick')
    def acceptClick(self):
        ''' временное сохранение изменений, в конфиге сохранится при выходе из программы '''
        program_options.load_last_opened_database = self.widget.checkBoxLoadLastOpenedDatabase.isChecked()
        self._set_disabled_plugins()
        self.accept()
        pass # end accept

    def _load_options(self):

        self.widget.checkBoxLoadLastOpenedDatabase.setChecked(program_options.load_last_opened_database)

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

        