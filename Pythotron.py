#############################################################################
##
## Copyright (C) 2020 HomeSoft.ru
## All rights reserved.
#
#############################################################################

#from PyQt5.QtCore import QEventLoop, QTime
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QSize, QCoreApplication, QSettings
from mainwindow import MainWindow
import classes.constants as constants

if __name__ == '__main__':

    import sys

    # Для того, чтобы каждый раз при вызове QSettings не вводить данные вашего приложения
    # по которым будут находиться настройки, можно
    # установить их глобально для всего приложения
    QCoreApplication.setApplicationName(constants.ORGANIZATION_NAME)
    QCoreApplication.setOrganizationDomain(constants.ORGANIZATION_DOMAIN)
    QCoreApplication.setApplicationName(constants.APPLICATION_NAME)

    app = QApplication(sys.argv)

    mainWindow = MainWindow()
    mainWindow.setFocus()
    mainWindow.show()
    sys.exit(app.exec_())
  
