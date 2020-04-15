from PyQt5.uic import loadUi 
from PyQt5.QtWidgets import QWidget


class PlaceHolderForm(QWidget):
    """ держалка для плагинов """
    def __init__(self, *args, **kwargs):
        super(PlaceHolderForm, self).__init__(*args, **kwargs)
        self.widget = loadUi('forms\\placeholder.ui', self)
        self.widget.tabWidget.clear() 

    def addForm(self,form):
        return self.widget.tabWidget.addTab(form,form.windowTitle())

    def insertForm(self,form, index):
        self.widget.tabWidget.insertTab(index,form,form.windowTitle())
        self.widget.tabWidget.setCurrentIndex(index)

    def setCurrentIndex(self, index):
        self.widget.tabWidget.setCurrentIndex(index)
