from PyQt5.QtCore import Qt,QSettings,QPoint,QSize
from PyQt5.QtWidgets import QMainWindow

class Settings(QMainWindow):
    """ Настройки для программы """

    """ открывать ли автоматически последнюю открытую базу лотереи """
    load_last_opened_database = False

    """ последняя открытая база лотереи """
    last_opened_database = ''

    """ путь к звуковому файлу окончания обучения """
    wav_file_path = '' 

    def __init__(self, _main_window):
        self.main_window = _main_window
        self.settings = QSettings(self.main_window.root+"/settings.ini", QSettings.IniFormat)
        pass

    def write_settings(self):
        """ Сохранение настроек для программы """

        # сохраняем общие Settings
        self.settings.setValue('load_last_opened_database', Settings.load_last_opened_database)
        self.settings.setValue('last_opened_database', Settings.last_opened_database)
        self.settings.setValue('wav_file_path', Settings.wav_file_path)

        # сохраняем объекты основного окна
        self.settings.setValue('recentFileList', self.main_window.recentFiles)

        # сохраняем плагины
        self.settings.setValue('plugins/disabled', self.main_window.disabled_plugins)

        # сохраняем размеры/положение и элементы основного окна
        self.settings.setValue("pos", self.main_window.pos())
        self.settings.setValue("size", self.main_window.size())
        self.settings.setValue("maximized", self.main_window.windowState() == Qt.WindowMaximized)
        self.settings.setValue("minimized", self.main_window.windowState() == Qt.WindowMinimized)

    def read_settings(self):
        """ Восстановление настроек для программы """

        # читаем общие Settings
        Settings.load_last_opened_database=self.settings.value('load_last_opened_database', False, bool)
        Settings.last_opened_database=self.settings.value('last_opened_database', '')
        Settings.wav_file_path=self.settings.value('wav_file_path', '')

        # восстанавливаем объекты основного окна
        self.main_window.recentFiles = self.settings.value('recentFileList', [], 'QStringList')

        # восстанавливаем плагины
        self.main_window.disabled_plugins=self.settings.value('plugins/disabled', [], 'QStringList')

        # восстанавливаем размеры/положение основного окна
        #если сохраняется максимизированным то нужно размеры для возвращения в нормальное состояние менять
        pos1 = self.settings.value("pos", QPoint(100, 100))
        size1 = self.settings.value("size", QSize(800, 400))
        maximized=self.settings.value("maximized", False,bool)
        minimized=self.settings.value("minimized", False,bool)
        if maximized:
            self.main_window.setWindowState(Qt.WindowMaximized)
        elif minimized:
            self.main_window.setWindowState(Qt.WindowMinimized)
        else:
            self.main_window.resize(size1)
            self.main_window.move(pos1)