"""
Hidden Markov Models
"""
from PyQt5 import QtCore
from PyQt5.uic import loadUi 
from PyQt5.QtWidgets import QWidget, QMessageBox

import time
import warnings

import numpy as np
from hmmlearn.hmm import GaussianHMM


from classes.common import *

class HMM(QWidget):

    def __init__(self, database):
        super(HMM, self).__init__()
        self.widget = loadUi('plugins\\hmm.ui', self)
        self.db=database
        # Connect the trigger signal to a slot.
        self.db.databaseOpened[str].connect(self.onDatabaseOpened)
        self.db.databaseClosed[str].connect(self.onDatabaseClosed)
        self.db.databaseUpdated[str].connect(self.onDatabaseUpdated)

        self.widget.pushButtonPredict.clicked.connect(self.onPredictClick)
        self.widget.comboBoxCovarianceType.addItems(["tied", "spherical", "diag", "full"])
        self.widget.comboBoxCovarianceType.activated[str].connect(self.onCovarianceTypeSelected)
        self.widget.labelCovarianceType.setText("tied")

    @QtCore.pyqtSlot(str, name='onDatabaseOpened')
    def databaseOpened(self,name):
        #self.widget.plainTextEdit.appendPlainText('File {} opened. NumberOfBalls2 {}'.format(name,self.db.lottery_config.NumberOfBalls2));
        self.widget.setEnabled(True)
        self.widget.spinBoxCheckToDraw.setValue(self.db.lottery_config.LastDrawNumber)
        self.widget.spinBoxCheckFromDraw.setValue(self.db.lottery_config.LastDrawNumber)
        self.widget.spinBoxToDraw.setValue(self.db.lottery_config.LastDrawNumber-1)
        self.widget.spinBoxFromDraw.setValue(self.db.lottery_config.LastDrawNumber-11)
        
        
    @QtCore.pyqtSlot(str, name='onDatabaseClosed')
    def databaseClosed(self,name):
        #self.widget.plainTextEdit.appendPlainText('File {} closed'.format(name));
        self.widget.setEnabled(False)
        pass

    @QtCore.pyqtSlot(str, name='onDatabaseUpdated')
    def databaseUpdated(self,name):
        #self.widget.plainTextEdit.appendPlainText('File {} updated'.format(name));
        pass

    @QtCore.pyqtSlot(name='onPredictClick')
    def calculateClick(self):
        try:
            self.widget.pushButtonPredict.setEnabled(False)
            self.hmm_calculate()
        finally:
            self.widget.pushButtonPredict.setEnabled(True)
        pass #end calculateClick
        
    def onCovarianceTypeSelected(self, text):

        self.widget.labelCovarianceType.setText(text)
        pass

    def hmm_calculate(self):
        """ Расчет Hidden Markov Models"""
        """ подготовим выбранные тиражи"""
        start = time.time()
        print("Начинаем считать в ", datetime.datetime.fromtimestamp(start).strftime("%d-%m-%y %H:%M:%S"))
        fromDraw= self.widget.spinBoxFromDraw.value()
        toDraw= self.widget.spinBoxToDraw.value()

        checkFromDraw= self.widget.spinBoxCheckFromDraw.value()
        checkToDraw= self.widget.spinBoxCheckToDraw.value()
        iter=self.widget.spinBoxIterations.value()

        if (toDraw-fromDraw)<=3:
            QMessageBox.warning(self, 'Предупреждение', "Обучающих примеров недостаточно", QMessageBox.Cancel )
            return

        predictCount=self.widget.spinBoxPredictCount.value()

        draws=self.db.get_draws_balls_numpy(fromDraw,toDraw)

        if draws.size == 0:
            QMessageBox.warning(self, 'Предупреждение', "Обучающих примеров нет", QMessageBox.Cancel )
            return

        checkDraws=self.db.get_draws_balls_numpy(checkFromDraw,checkToDraw)
        print("\n-checkDraws-\n")
        print(checkDraws)
        print(checkDraws.shape)
        if checkDraws.size == 0:
            QMessageBox.warning(self, 'Предупреждение', "Проверочных примеров нет", QMessageBox.Cancel )
            return
        # Create a Gaussian HMM 
        
        num_components = 7
        if (len(draws)/2)<num_components:
            num_components=int(len(draws)/2-1);

        if num_components<1:
            num_components=1
        print("num_components=",num_components)

        covar_type = str(self.widget.comboBoxCovarianceType.currentText())
        print("используем ",covar_type)
        """n_components — определяет число скрытых состояний. Относительно неплохие модели можно строить, используя 6-8 скрытых состояний. Habr. Но у меня при больших значениях
        могло выдать ошибку rows of transmat_ must sum to 1.0 - видимо зависит от числа обучающих примеров
        Остальные параметры отвечают за сходимость EM-алгоритма, ограничивая число итераций, точность и определяя тип ковариационных параметров состояний.
        https://habr.com/ru/post/351462/
        """
        try:
            hmm = GaussianHMM(n_components=num_components, covariance_type=covar_type, n_iter=iter) #tied дает ошибки для 4x20 при малом наборе
            # Train the HMM  https://ogrisel.github.io/scikit-learn.org/sklearn-tutorial/modules/generated/sklearn.hmm.GaussianHMM.html
            print('\nTraining the Hidden Markov Model...')
            with warnings.catch_warnings():
                warnings.simplefilter('ignore')
                hmm.fit(draws)
            # Print HMM stats
            print('\nMeans and variances:')
            for i in range(hmm.n_components):
                print('\nHidden state', i+1)
                print('Mean =', round(hmm.means_[i][0], 2))
                print('Variance =', round(np.diag(hmm.covars_[i])[0], 2))
            print("\n-Generate data using the HMM model-\n")
            # Generate data using the HMM model
            predicted_data, _ = hmm.sample(predictCount) 

            predicted_data=np.array(predicted_data,dtype=int) #преобразуем в int
            print('predicted_data:', predicted_data,", type/shape/ndim ", type(predicted_data),predicted_data.shape,predicted_data.ndim)

            self.print_results(predicted_data,checkDraws)
            end = time.time()
            print("затрачено: ",time.strftime('%H:%M:%S', time.gmtime(end - start))) 
        except Exception as e:
            print('HMM:HmmCalculate error: ', e)
            dbg_except()
            self.widget.plainTextEdit.setPlainText(str(e))
        pass #end HmmCalculate

    def print_results(self, draws,checkDraws):
        """ выводим прогноз и сравниваем с реальностью"""
        #print('draws:', draws,", type/shape/ndim ", type(draws),draws.shape,draws.ndim)
        self.widget.plainTextEdit.setPlainText('Прогноз')
        for draw in draws:
            if self.db.lottery_config.NumberOfBalls2==0: #если нет дополнительных
                coins=[]
                for checkDraw in checkDraws:
                    coins.append(compare_balls_detail(draw,checkDraw))
                self.widget.plainTextEdit.appendPlainText('{}, совпадений {}'.format(printf(draw),coins))
            else:
                coins1=[]
                coins2=[]
                for checkDraw in checkDraws:
                    coins1.append(compare_balls_detail(draw[0:self.db.lottery_config.NumberOfBalls1],checkDraw[0:self.db.lottery_config.NumberOfBalls1]))
                    coins2.append(compare_balls_detail(draw[self.db.lottery_config.NumberOfBalls1:],checkDraw[self.db.lottery_config.NumberOfBalls1:]))
                self.widget.plainTextEdit.appendPlainText('{}, совпадений основных {},дополнительных {}'.format(printf(draw),coins1,coins2))

        pass #printResults


