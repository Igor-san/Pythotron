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

from forms.optionsform import OptionsForm
from classes.common import *
from classes.constants import *
from classes.database import Db
from classes.importhelper import import_plugins, import_plugin

from classes.settings import Settings

from _version import __version__, __date__

class MainWindow(QMainWindow):
    """This is the class of the MainApp GUI system"""
    MaxRecentFiles = 5

    def __init__(self):
        """Constructor method that inherits methods from QWidgets"""
        super().__init__()

        self.root = QFileInfo(__file__).absolutePath()
        self.settings=Settings(self)
        ##self.settings = QSettings(self.root+"/settings.ini", QSettings.IniFormat)

        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.plugins_directory_path = os.path.join(script_dir, 'plugins')

        self.database=Db()
        
        self.default_open_dir=self.root+"/"+DATABASES_FOLDER
        
        self.recent_file_acts = [] # действия для открытия последних файлов
        self.available_plugins = [] # доступные в папке plugins плагины
        self.disabled_plugins = [] # не загружаемые плагины
        self.loaded_plugins = [] # загруженные плагины
        self.load_plugin_acts = [] # действия для открытия доступных плагинов
        self.recentFiles = [] # последние загруженные файлы
        self.curFile = ''

        self.initUI()

        if Settings.load_last_opened_database and Settings.last_opened_database:
            self.open_file(Settings.last_opened_database)
     
        #self.open_test_file()

    def open_test_file(self):
        return
        #self.open_file(self.default_open_dir+"/4x20.ntr")
        self.open_file(self.default_open_dir+"/eurojackpot.sqlite")

    def closeEvent(self, event):
        """ случается при попытке закрыть виджет"""
        if self.maybe_exit():
            self.settings.write_settings()
            event.accept()
        else:
            event.ignore()

    def maybe_exit(self):
        return True

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

    def load_plugin(self):
        action = self.sender()
        if action:
            module_name=action.data()
            plugin = import_plugin(self.database, self.plugins_directory_path, module_name)
            if plugin.plugin_name not in self.loaded_plugins:
                self.loaded_plugins.append(plugin.plugin_name)
            index=self.placeHolder.addForm(plugin)
            self.placeHolder.setCurrentIndex(index)

    def about(self):
        QMessageBox.about(self, "About Pythotron",
                "<p>Программа <b>Pythotron</b> для анализа лотерей. <a href='"+HELP_URL+"'>Подробнее на форуме Upad.ru</a></p> \
                <p><strong>Версия "+__version__+" от "+__date__+"</strong></p>")

    def show_options(self):
        dlg = OptionsForm(self)
        dlg.available_plugins=self.available_plugins
        dlg.disabled_plugins=self.disabled_plugins
        #dlg.loaded_plugins=self.loaded_plugins
        dlg.create_plugins_list()

        if dlg.exec_():
            self.disabled_plugins=dlg.disabled_plugins


    def play_lottery(self):
        openurl(LOTTERY_PLAY_URL)

    def update_lottery(self):
        try:
            if self.database.isClosed: return
            
            module = importlib.import_module("." + self.database.lottery_config.DataImportPlugin.lower(), package='dataimport')
            form=module.DataImport(self,self.database)
            form.show_form()
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

        splitterV = QSplitter(Qt.Vertical)
        splitterV.setStyleSheet('background-color:beige')
        self.setCentralWidget(splitterV)

        splitterH = QSplitter(Qt.Horizontal)
        splitterH.setStyleSheet('background-color:beige')
        splitterH.addWidget(self.historyForm)
        splitterH.addWidget(self.placeHolder);
       
        splitterV.addWidget(splitterH);
        #splitterV.addWidget(self.messageForm);

        desktop = QApplication.desktop()
        self.setGeometry(50, 50, 900, 500)
        self.move(desktop.availableGeometry().center()- self.rect().center()) #по умолчению в центре экрана

        self.settings.read_settings() # вначале восстанавливаем настройки, положение
        ##self.read_settings()

        self.create_plugins() # затем читаем и загружаем нужные плагины

        self.create_actions() # а затем создаем нужные действия
        self.create_menus()
        self.create_tool_bars()
        self.create_status_bar()


        self.setWindowTitle(APPLICATION_NAME)
        self.setWindowIcon(QIcon(self.root + '/images/logo.png'))

        splitterV.setStretchFactor(0, 200);
        splitterV.setStretchFactor(1, 1);

        splitterH.setHandleWidth(0)
        splitterV.setHandleWidth(0)
        #splitterV.setSizes([200, 1]);

        self.show()

    def create_plugins(self):
        self.available_plugins.clear()
        plugins = import_plugins(self.database, self.plugins_directory_path, self.disabled_plugins, self.available_plugins )
        
        lasIndex=0
        self.loaded_plugins.clear()
        for plugin in plugins:
            self.loaded_plugins.append(plugin.plugin_name)
            lasIndex= self.placeHolder.addForm(plugin)

        self.placeHolder.setCurrentIndex(1)    

    def create_actions(self):
        for i in range(MainWindow.MaxRecentFiles):
            self.recent_file_acts.append(QAction(self, visible=False, triggered=self.open_recent_file)) #последние файлы

        for i in range(len(self.available_plugins)):
            self.load_plugin_acts.append(QAction(self, visible=False, triggered=self.load_plugin))

        self.closeAct = QAction(QIcon(self.root + '/images/close.png'), "&Close", self,
                shortcut=QKeySequence.Close, statusTip="Закрыть базу данных", triggered=self.close_file)

        self.openAct = QAction(QIcon(self.root + '/images/open.png'), "&Open...",
                self, shortcut=QKeySequence.Open, statusTip="Открыть базу данных", triggered=self.open_file)

        self.optionsAct = QAction(QIcon(self.root + '/images/options.png'), "O&ptions...",
                self, statusTip="Настройка программы", triggered=self.show_options)

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
            self.fileMenu.addAction(self.recent_file_acts[i])

        self.fileMenu.addSeparator();
        self.fileMenu.addAction(self.exitAct)

        self.tools_menu = self.menuBar().addMenu("&Tools")
        self.tools_menu.addAction(self.optionsAct)
        
        self.plugins_menu = self.menuBar().addMenu("&Plugins")
        for i, plugin in enumerate(self.available_plugins):
            text = "%d %s" % ((i+1), plugin)
            self.load_plugin_acts[i].setText(text)
            self.load_plugin_acts[i].setData(plugin)
            self.load_plugin_acts[i].setVisible(True)
            self.plugins_menu.addAction(self.load_plugin_acts[i])

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
        Settings.last_opened_database = fileName

        #self.recentFiles = self.settings.value('recentFileList', [], 'QStringList')

        try:
            self.recentFiles.remove(fileName) #TODO удаление независимо от регистра
        except ValueError:
            pass

        self.recentFiles.insert(0, fileName)
        del self.recentFiles[MainWindow.MaxRecentFiles:]

        #self.settings.setValue('recentFileList', files)

        self.update_recent_file_actions()

    def update_recent_file_actions(self):
        #files = self.settings.value('recentFileList', [])

        numRecentFiles = min(len(self.recentFiles), MainWindow.MaxRecentFiles)

        for i in range(numRecentFiles):
            text = "&%d %s" % (i + 1, self.stripped_name(self.recentFiles[i]))
            self.recent_file_acts[i].setText(text)
            self.recent_file_acts[i].setData(self.recentFiles[i])
            self.recent_file_acts[i].setVisible(True)

        for j in range(numRecentFiles, MainWindow.MaxRecentFiles):
            self.recent_file_acts[j].setVisible(False)

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

        self.toolsToolBar = self.addToolBar("Tools")
        self.toolsToolBar.addAction(self.optionsAct)

        self.exitToolBar = self.addToolBar("Exit")
        self.exitToolBar.addAction(self.exitAct)

    def create_status_bar(self):
        self.statusBar().showMessage("Ready")
        

if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = MainWindow()
    sys.exit(app.exec_())