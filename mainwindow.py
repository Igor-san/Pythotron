from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5 import uic
from PyQt5.QtCore import Qt,QFileInfo,QSettings,QPoint,QSize

import os
import sys
import pathlib
from glob import glob
from functools import partial
import importlib

from forms.historyform import HistoryForm
from forms.placeholderform import PlaceHolderForm
from forms.messageform import MessageForm
from classes.common import *
from classes.database import Db
from classes.importhelper import import_plugins

class MainWindow(QMainWindow):
    """This is the class of the MainApp GUI system"""
    MaxRecentFiles = 5

    def __init__(self):
        """Constructor method that inherits methods from QWidgets"""
        super().__init__()
        #self.root=pathlib.Path().absolute()
        self.database=Db()
        self.root = QFileInfo(__file__).absolutePath()
        self.default_open_dir=self.root+"/"+DATABASES_FOLDER
        self.settings = QSettings(self.root+"/settings.ini", QSettings.IniFormat)
        self.recentFileActs = []
        self.curFile = ''

        self.initUI()
        
        self.open_test_file()

    def open_test_file(self):
        #self.open_file(self.default_open_dir+"/4x20.ntr")
        self.open_file(self.default_open_dir+"/eurojackpot.sqlite")

    def closeEvent(self, event):
        """ случается при попытке закрыть виджет"""
        if self.maybe_exit():
            self.write_settings()
            event.accept()
        else:
            event.ignore()

    def maybe_exit(self):
        return True

    def mock(self):
        pass

    def load_file(self,file):
        print(file)

    def close_file(self):
        self.updateAct.setEnabled(False)
        self.historyForm.closeFile()
        self.statusBar().showMessage('')
        self.setWindowTitle(APPLICATION_NAME)

    def open_file(self, fileName=''):

        if not fileName:
            fileName, _ = QFileDialog.getOpenFileName(self,'Open file', self.default_open_dir, FILES_TYPES)

        if fileName:
           self.historyForm.openFile(fileName)
           self.set_current_file(fileName)
           self.updateAct.setEnabled(self.historyForm.updateEnabled)

        self.statusBar().showMessage('File {}'.format(fileName))
        self.setWindowTitle('{} {}'.format(APPLICATION_NAME, self.stripped_name(self.curFile)))
        
    def open_recent_file(self):
        action = self.sender()
        if action:
            self.open_file(action.data())

    def about(self):
        QMessageBox.about(self, "About Pythotron",
                "Программа <b>Pythotron</b> для анализа лотерей. <a href='"+HELP_URL+"'>Подробнее на форуме Upad.ru</a>")

    def play_lottery(self):
        openurl(LOTTERY_PLAY_URL)

    def update_lottery(self):
        try:
            if self.database.isClosed: return
            
            module = importlib.import_module("." + self.database.lottery_config.DataImportPlugin, package='dataimport')
            form=module.DataImport(self,self.database)
            #form.show()
            form.exec_()
            if form.added>0: #обновлено больше 0 тиражей нужно грид обновить
                self.database.update_history_view()
           

        except Exception as e:
            print('MainWindow:update_lottery error: ', e)
            dbg_except()
        pass
        

    def open_recent_file(self):
        action = self.sender()
        if action:
            self.open_file(action.data())

    def initUI(self):
        """ Создание GUI  """
        self.historyForm =  HistoryForm(self.database)
        self.placeHolder =  PlaceHolderForm()
        self.messageForm =  MessageForm()

        splitterV = QSplitter(Qt.Vertical)
        splitterV.setStyleSheet('background-color:beige')
        self.setCentralWidget(splitterV)

        splitterH = QSplitter(Qt.Horizontal)
        splitterH.setStyleSheet('background-color:beige')
        splitterH.addWidget(self.historyForm)
        splitterH.addWidget(self.placeHolder);
       
        splitterV.addWidget(splitterH);
        #splitterV.addWidget(self.messageForm);

        self.create_actions()
        self.create_menus()
        self.create_tool_bars()
        self.create_status_bar()
        self.create_plugins()

        self.setGeometry(50, 50, 900, 500)
        #self.setFixedSize(self.size())
        self.setWindowTitle(APPLICATION_NAME)
        self.setWindowIcon(QIcon(self.root + '/images/logo.png'))

        desktop = QApplication.desktop()
        self.move(desktop.availableGeometry().center()- self.rect().center()) #по умолчению в центре экрана

        self.read_settings() #восстанавливаем настройки, положение

        splitterV.setStretchFactor(0, 200);
        splitterV.setStretchFactor(1, 1);

        splitterH.setHandleWidth(0)
        splitterV.setHandleWidth(0)
        #splitterV.setSizes([200, 1]);

        self.show()

    def create_plugins(self):
        SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
        plugins_directory_path = os.path.join(SCRIPT_DIR, 'plugins')
        plugins = import_plugins(self.database, plugins_directory_path)

        lasIndex=0
        for plugin in plugins:
           lasIndex= self.placeHolder.addForm(plugin)

        self.placeHolder.setCurrentIndex(1)    

    def create_actions(self):
        for i in range(MainWindow.MaxRecentFiles):
            self.recentFileActs.append(QAction(self, visible=False, triggered=self.open_recent_file)) #последние файлы

        self.closeAct = QAction(QIcon(self.root + '/images/close.png'), "&Close", self,
                shortcut=QKeySequence.Close, statusTip="Закрыть базу данных", triggered=self.close_file)

        self.openAct = QAction(QIcon(self.root + '/images/open.png'), "&Open...",
                self, shortcut=QKeySequence.Open, statusTip="Открыть базу данных", triggered=self.open_file)


        self.playAct = QAction(QIcon(self.root + '/images/chips.png'), "Play lottery", self,
                statusTip="Играть в полулярные мировые лотереи", triggered=self.play_lottery)

        self.exitAct = QAction(QIcon(self.root + '/images/exit.png'), "E&xit", self, shortcut="Ctrl+Q",
                statusTip="Выйти из программы", triggered=self.close)

        self.aboutAct = QAction("&About", self, statusTip="О программе", triggered=self.about)

        self.updateAct = QAction(QIcon(self.root + '/images/update.png'), "&Update", self, statusTip="Обновить лотерею", triggered=self.update_lottery)

    def play_menu_action(self, item):
        try:
            openurl(item.data()[1])
        except:
            pass
        

    def create_menus(self):
        self.fileMenu = self.menuBar().addMenu("&File")
        self.fileMenu.addAction(self.openAct)
        self.fileMenu.addAction(self.closeAct)
        self.separatorAct = self.fileMenu.addSeparator()
        for i in range(MainWindow.MaxRecentFiles):
            self.fileMenu.addAction(self.recentFileActs[i])

        self.fileMenu.addSeparator();
        self.fileMenu.addAction(self.exitAct)

        self.play_menu = self.menuBar().addMenu("&Play")
        items = [("Eurojackpot",EUROJACKPOT_PLAY_URL),("Euromillions",EUROMILLIONS_PLAY_URL),("Мировые лотереи",LOTTERY_PLAY_URL)]

        # play_menu
        for item in items:
            fancyName = "%s" % (item[0])
            action = self.play_menu.addAction(fancyName )
            action.setData(item)
            action.triggered.connect(partial(self.play_menu_action, action))

        self.menuBar().addSeparator()

        self.helpMenu = self.menuBar().addMenu("&Help")
        self.helpMenu.addAction(self.aboutAct)

        self.update_recent_file_actions()

    def set_current_file(self, fileName):
        self.curFile = fileName

        files = self.settings.value('recentFileList', [])

        try:
            files.remove(fileName) #TODO удаление независимо от регистра
        except ValueError:
            pass

        files.insert(0, fileName)
        del files[MainWindow.MaxRecentFiles:]

        self.settings.setValue('recentFileList', files)

        self.update_recent_file_actions()

    def update_recent_file_actions(self):
        files = self.settings.value('recentFileList', [])

        numRecentFiles = min(len(files), MainWindow.MaxRecentFiles)

        for i in range(numRecentFiles):
            text = "&%d %s" % (i + 1, self.stripped_name(files[i]))
            self.recentFileActs[i].setText(text)
            self.recentFileActs[i].setData(files[i])
            self.recentFileActs[i].setVisible(True)

        for j in range(numRecentFiles, MainWindow.MaxRecentFiles):
            self.recentFileActs[j].setVisible(False)

        self.separatorAct.setVisible((numRecentFiles > 0))

    def stripped_name(self, fullFileName):
        return QFileInfo(fullFileName).fileName()

    def create_tool_bars(self):
        self.fileToolBar = self.addToolBar("File")
        
        self.fileToolBar.addAction(self.openAct)
        self.fileToolBar.addAction(self.closeAct)
        self.fileToolBar.addAction(self.updateAct)

        self.playToolBar = self.addToolBar("Play")
        self.playToolBar.addAction(self.playAct)

        self.exitToolBar = self.addToolBar("Exit")
        self.exitToolBar.addAction(self.exitAct)

    def create_status_bar(self):
        self.statusBar().showMessage("Ready")

    def read_settings(self):
        """
        если сохраняется максимизированным то нужно размеры для возвращения в нормальное состояние менять
        """
        pos = self.settings.value("pos", QPoint(100, 100))
        size = self.settings.value("size", QSize(800, 400))
        maximized=self.settings.value("maximized", False,bool)
        minimized=self.settings.value("minimized", False,bool)
        if maximized:
           self.setWindowState(Qt.WindowMaximized)
        elif minimized:
           self.setWindowState(Qt.WindowMinimized)
        else:
           self.resize(size)
           self.move(pos)

    def write_settings(self):
        self.settings.setValue("pos", self.pos())
        self.settings.setValue("size", self.size())
        self.settings.setValue("maximized", self.windowState() == Qt.WindowMaximized)
        self.settings.setValue("minimized", self.windowState() == Qt.WindowMinimized)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = MainWindow()
    sys.exit(app.exec_())