"""
Keras Network with Tensorflow
"""
from classes.common import *

from PyQt5 import QtCore
from PyQt5.uic import loadUi 
from PyQt5.QtWidgets import QWidget, QMessageBox
from PyQt5.QtWidgets import QApplication

import time
import warnings

import numpy as np
import matplotlib.pyplot as plt

import os # disable GPU
os.environ["CUDA_VISIBLE_DEVICES"] = "-1" #  прямой путь disable GPU

import tensorflow as tf
# использую tensorflow.keras а не keras как рекомендовано https://www.tensorflow.org/guide/effective_tf2
from tensorflow.keras import backend as K
from tensorflow.keras import models
from tensorflow.keras import layers

import classes.common as common
from classes.settings import Settings

wav_file_on_end = '' # файл проигрываемый по окончанию обучения

class KerasNet(QWidget):
    stop_process=False # остановка процесса обучения

    def __init__(self, database):
        super(KerasNet, self).__init__()
        self.widget = loadUi('plugins\\kerasnet.ui', self)
        self.db=database # общая база данных
        self.network=None # нейронная сеть
        self.check_by_position= False # проверять совпадения по позициям
        # Connect the trigger signal to a slot.
        self.db.databaseOpened[str].connect(self.onDatabaseOpened)
        self.db.databaseClosed[str].connect(self.onDatabaseClosed)
        self.db.databaseUpdated[str].connect(self.onDatabaseUpdated)

        self.loss_function="mean_squared_error"
        self.widget.pushButtonPredict.clicked.connect(self.onPredictClick)
        self.widget.pushButtonCreateModel.clicked.connect(self.onCreateModelClick)
        self.widget.pushButtonStopProcess.clicked.connect(self.onStopProcessClick)
        

        self.widget.comboBoxLossType.addItems(["mean_squared_error", "mean_absolute_error", "hinge", "poisson", "binary_crossentropy"])
        self.widget.comboBoxLossType.activated[str].connect(self.onLossTypeSelected)
        self.widget.labelLossType.setText(self.loss_function)

        self.widget.spinBoxIterations.setValue(100)
        self.widget.spinBoxPredictCount.setValue(1)

#GPU на 400 тиражах текущей конфигурации
#затрачено:  00:00:33 - 100 эпох
#затрачено:  00:05:51 - 1000 эпох
#CPU
#затрачено:  00:00:13 - 100 эпох
#затрачено:  00:02:30 - 1000 эпох

        self.physical_devices = tf.config.list_physical_devices('GPU')
        visible_devices = tf.config.get_visible_devices() 
        if (any(device.device_type == 'GPU' for device in visible_devices)):
            self.widget.checkBoxUseGpu.setChecked(True)
        else:
            self.widget.checkBoxUseGpu.setChecked(False)

        # и только сейчас подключим слот чтобы не сработал на код выше
        self.widget.checkBoxUseGpu.stateChanged.connect(self.onUseGpuStateChanged)

        # если загружаем плагин уже при открытой базе данных
        if not self.db.isClosed:
            self.databaseOpened(self.db.path)


    def status_message(self,*args):
        self.widget.plainTextEdit.appendPlainText("status:"+''.join(map(str, args)) )
        pass #end statusMessage

    def error_message(self,*args):
        self.widget.plainTextEdit.appendPlainText("error:"+''.join(map(str, args)) )
        pass #end errorMessage

    @QtCore.pyqtSlot(int, name='onUseGpuStateChanged')
    def useGpuStateChanged(self, int):
        if self.widget.checkBoxUseGpu.isChecked():
            self.enable_gpu(True)
        else:
            self.enable_gpu(False)

    @QtCore.pyqtSlot(str, name='onDatabaseOpened')
    def databaseOpened(self, name):
        self.widget.setEnabled(True)
        self.widget.spinBoxCheckToDraw.setValue(self.db.lottery_config.LastDrawNumber)
        self.widget.spinBoxCheckFromDraw.setValue(self.db.lottery_config.LastDrawNumber)
        self.widget.spinBoxToDraw.setValue(self.db.lottery_config.LastDrawNumber-1)
        self.widget.spinBoxFromDraw.setValue(self.db.lottery_config.LastDrawNumber-11)
        self.widget.spinBoxInputDraw.setValue(self.db.lottery_config.LastDrawNumber-1)

        self.check_by_position =(self.db.lottery_config.IsFonbet or self.db.lottery_config.IsTop3)
        
    @QtCore.pyqtSlot(str, name='onDatabaseClosed')
    def databaseClosed(self,name):
        self.widget.setEnabled(False)
        pass

    @QtCore.pyqtSlot(str, name='onDatabaseUpdated')
    def databaseUpdated(self,name):
        pass

    @QtCore.pyqtSlot(name='onStopProcessClick')
    def stopProcessClick(self):
        ''' остановить процесс обучения '''
        KerasNet.stop_process=True
        pass

    @QtCore.pyqtSlot(name='onPredictClick')
    def predictClick(self):
        try:
            self.widget.pushButtonPredict.setEnabled(False)
            self.predict()
        finally:
            self.widget.pushButtonPredict.setEnabled(True)
        pass #end predictClick

    @QtCore.pyqtSlot(name='onCreateModelClick')
    def createModelClick(self):
        try:
            KerasNet.stop_process=False

            self.widget.pushButtonCreateModel.setEnabled(False)
            self.widget.pushButtonStopProcess.setEnabled(True)
            QApplication.processEvents()
            self.keras_create_model()
        finally:
            self.widget.pushButtonCreateModel.setEnabled(True)
            self.widget.pushButtonStopProcess.setEnabled(False)
        pass #end onCreateModelClick
        
    def onLossTypeSelected(self, text):
        self.loss_function=text
        self.widget.labelLossType.setText(text)
        pass

    def predict(self):
        """ Сделать прогноз на основе созданной модели"""
        try:
            if self.network==None:
                self.error_message("модель сети не обучена")
                return

            inputDrawNumber=self.widget.spinBoxInputDraw.value()
            checkFromDraw= self.widget.spinBoxCheckFromDraw.value()
            checkToDraw= self.widget.spinBoxCheckToDraw.value()

            nob1=self.db.lottery_config.NumberOfBalls1
            nob2=self.db.lottery_config.NumberOfBalls2

            inputDraws=self.db.get_draws_balls_numpy(inputDrawNumber,inputDrawNumber)
            checkDraws=self.db.get_draws_balls_numpy(checkFromDraw,checkToDraw)
            if checkDraws.size == 0:
                QMessageBox.warning(self, 'Предупреждение', "Проверочных примеров нет", QMessageBox.Cancel )
                return
            if inputDraws.size == 0:
                QMessageBox.warning(self, 'Предупреждение', "Входных тиражей нет", QMessageBox.Cancel )
                return

            input_draws=np.copy(inputDraws).astype('float32')

            prognoz_output=self.network.predict(input_draws)
            #print('prognoz_output:', prognoz_output,", type/shape/ndim ", type(prognoz_output),prognoz_output.shape,prognoz_output.ndim)
            self.print_results(np.array(prognoz_output,dtype=int),checkDraws)

        except Exception as e:
            print('KerasNet:predict error: ', e)
            dbg_except()
            self.widget.plainTextEdit.setPlainText(str(e))
        pass #end predict

    def enable_gpu(self, enable=False):
        visible_devices = tf.config.get_visible_devices() 
        if (any(device.device_type == 'GPU' for device in visible_devices)): #есть GPU в visible_devices
            if not enable: #но надо отключить
                try: 
                  tf.config.set_visible_devices([], 'GPU') 
                  visible_devices = tf.config.get_visible_devices() 
                  for device in visible_devices: 
                      assert device.device_type != 'GPU' 
                except Exception as e:
                  self.error_message('enable_gpu error disable GPU: ', e)
                  pass 
        elif enable: #надо включить при отсутствии в visible_devices
                try: 
                  tf.config.set_visible_devices(self.physical_devices[:], 'GPU') 
                  visible_devices = tf.config.get_visible_devices() 
                  assert any(device.device_type == 'GPU' for device in visible_devices)
                except Exception as e:
                  self.error_message('enable_gpu error enable GPU: ', e)
                  pass 
        pass #enable_gpu end

    def keras_create_model(self):
        """ Создание и обучение нейросети """

        global wav_file_on_end

        wav_file_on_end = ''
        if self.widget.checkBoxWavOnEnd.isChecked() and Settings.wav_file_path and os.path.isfile(Settings.wav_file_path):
            wav_file_on_end = Settings.wav_file_path

        # подготовим выбранные тиражи
        self.widget.checkBoxUseGpu.setEnabled(False) #теперь сменить ЦПУ/ГПУ только при перезагрузке...или писать дополнительно код для fit и predict
       
        start = time.time()
        print("Начинаем в ", datetime.datetime.fromtimestamp(start).strftime("%d-%m-%y %H:%M:%S"))

        fromDraw= self.widget.spinBoxFromDraw.value()
        toDraw= self.widget.spinBoxToDraw.value()
        inputDrawNumber=self.widget.spinBoxInputDraw.value()
        batch = self.widget.spinBoxBatchSize.value() #пакетов для обучения,небольшой набор образцов (обычно от 8 до 128), обрабатываемых моделью одновременно

        checkFromDraw= self.widget.spinBoxCheckFromDraw.value()
        checkToDraw= self.widget.spinBoxCheckToDraw.value()
        epochs_count=self.widget.spinBoxIterations.value()
       
        if (toDraw-fromDraw)<=3:
            QMessageBox.warning(self, 'Предупреждение', "Обучающих примеров недостаточно", QMessageBox.Cancel )
            return

        predictCount=self.widget.spinBoxPredictCount.value()

        draws=self.db.get_draws_balls_numpy(fromDraw,toDraw)

        if draws.size == 0:
            QMessageBox.warning(self, 'Предупреждение', "Обучающих примеров нет", QMessageBox.Cancel )
            return

        inputDraws=self.db.get_draws_balls_numpy(inputDrawNumber,inputDrawNumber)
        checkDraws=self.db.get_draws_balls_numpy(checkFromDraw,checkToDraw)

        if checkDraws.size == 0:
            QMessageBox.warning(self, 'Предупреждение', "Проверочных примеров нет", QMessageBox.Cancel )
            return
        if inputDraws.size == 0:
            QMessageBox.warning(self, 'Предупреждение', "Входных тиражей нет", QMessageBox.Cancel )
            return

        draws_count=len(draws)
        if (draws_count/2)<batch:
            batch=int(draws_count/2-1);

        if batch<1:
            batch=1
        print("batch=",batch)

        try:
            nob1=self.db.lottery_config.NumberOfBalls1
            nob2=self.db.lottery_config.NumberOfBalls2

            input_size=nob1+nob2
            network = models.Sequential()
            # функции активации https://keras.io/activations/ 
            # elu, softmax, selu, softplus, softsign, relu, tanh, sigmoid, hard_sigmoid, exponential, linear, 
            hidden_neurons=input_size
            network.add(layers.Dense(hidden_neurons, activation='relu', input_shape=(input_size,)))
            network.add(layers.Dense(hidden_neurons, activation='relu'))
            #network.add(layers.Dense(64, kernel_regularizer=tf.keras.regularizers.l1(0.01)))
            # много простора для самодеятельности
            #network.add(layers.BatchNormalization())
            #network.add(layers.Dense(input_size*2, activation='relu'))
            #network.add(layers.Dropout(0.2))
            #network.add(layers.Dense(input_size*3, activation='relu'))
            #network.add(layers.Dropout(0.5))
            #network.add(layers.Dense(input_size*2, activation='relu'))
            network.add(layers.Dense(input_size, activation='relu'))
            #network.add(layers.Dense(input_size, activation='sigmoid'))
            #network.add(layers.Dense(input_size, activation='tanh'))
            network.summary()

            # метрики https://keras.io/metrics/ accuracy, binary_accuracy, categorical_accuracy, sparse_categorical_accuracy, top_k_categorical_accuracy, sparse_top_k_categorical_accuracy, cosine_proximity,clone_metric
            # https://www.tensorflow.org/api_docs/python/tf/keras/metrics
            # функции потери https://keras.io/losses/
            # compilation компиляция модели - и тут также можно порезвиться
            #network.compile(optimizer='rmsprop', loss='categorical_crossentropy', metrics=['accuracy']) 
            #network.compile(optimizer='rmsprop', loss=self.loss_function, metrics=['accuracy']) #понятие точности неприменимо для регрессии, поэтому для оценки качества часто применяется средняя абсолютная ошибка (Mean Absolute Error, MAE).
            network.compile(optimizer=tf.keras.optimizers.Adam(0.01), loss=self.loss_function, metrics=['mse'], run_eagerly=True)
  
            #Подготовка исходных данных - полностью используем тиражи на обучение

            train_images=np.copy(draws[:-1])
            train_labels=np.copy(draws[1:])
            input_draws=np.copy(inputDraws)
       
            callbacks_list =[MyCustomCallback()] # [StopTeachCallback()]
            predicted_data=[]
            for i in range(predictCount):
                #teach start
                history =network.fit(train_images, train_labels, epochs=epochs_count, batch_size=batch, callbacks=callbacks_list) #обучение модели
                #history_dict = history.history
                #print("history_dict.keys: ", history_dict.keys())
                prognoz_output=network.predict(input_draws)
                predicted_data.append(prognoz_output.flatten()) #уплощаем массив в одномерный
                pass #end teach

            self.network=network #для дальнейшего использования
            self.print_results(np.array(predicted_data,dtype=int),checkDraws)

            history_dict = history.history
            print("history_dict.keys: ", history_dict.keys())
            dict_arr=list(history_dict.keys())
            #loss = history.history['loss']
            #mae = history.history['mse']
            key0 = history.history[dict_arr[0]]
            key1 = history.history[dict_arr[1]]
            epochs = range(1, len(key0) + 1)

            plt.ion() #чтобы в PyQT выполнялось
            plt.clf()
            ## "bo" is for "blue dot"
            plt.plot(epochs, key0, 'bo', label=dict_arr[0])
            ## b is for "solid blue line"
            plt.plot(epochs, key1, 'b', label=dict_arr[1])
            plt.title('Training and validation')
            plt.xlabel('Epochs')
            plt.ylabel(dict_arr[0])
            plt.legend()

            #plt.show() #не нужно
            end = time.time()
            print("затрачено: ",time.strftime('%H:%M:%S', time.gmtime(end - start))) 

        except Exception as e:
            print('KerasNet:keras_create_model error: ', e)
            dbg_except()
            self.widget.plainTextEdit.setPlainText(str(e))

        pass #end keras_create_model

    def print_results(self, draws,checkDraws):
        """ выводим прогноз и сравниваем с реальностью"""
        #print('draws:', draws,", type/shape/ndim ", type(draws),draws.shape,draws.ndim)
               
        self.widget.plainTextEdit.setPlainText('Прогноз')
        for draw in draws:
            if self.db.lottery_config.NumberOfBalls2==0: #если нет дополнительных
                coins=[]
                for checkDraw in checkDraws:
                    coins.append(compare_balls_detail(draw,checkDraw, self.check_by_position))
                self.widget.plainTextEdit.appendPlainText('{}, совпадений {}'.format(printf(draw),coins))
            else:
                coins1=[]
                coins2=[]
                for checkDraw in checkDraws:
                    coins1.append(compare_balls_detail(draw[0:self.db.lottery_config.NumberOfBalls1],checkDraw[0:self.db.lottery_config.NumberOfBalls1], self.check_by_position))
                    coins2.append(compare_balls_detail(draw[self.db.lottery_config.NumberOfBalls1:],checkDraw[self.db.lottery_config.NumberOfBalls1:], self.check_by_position))
                self.widget.plainTextEdit.appendPlainText('{}, совпадений основных {},дополнительных {}'.format(printf(draw),coins1,coins2))

        pass #printResults

#class StopTeachCallback(tf.keras.callbacks.Callback): 
#    """ обратный вызов для остановки обучения по кнопке """
#    def on_epoch_end(self, epoch, logs=None):
#        QApplication.processEvents()
#        if KerasNet.stop_process:  
#            print('останавливаю по запросу пользователя')
#            self.model.stop_training = True


class MyCustomCallback(tf.keras.callbacks.Callback):
    """ обратный вызов для остановки обучения по кнопке """
    def on_epoch_end(self, epoch, logs=None):
        QApplication.processEvents()
        if KerasNet.stop_process:  
            print('останавливаю по запросу пользователя')
            self.model.stop_training = True

    def on_train_end(self, logs=None):
        if wav_file_on_end:
            common.play_sound(wav_file_on_end)

    #def on_train_batch_begin(self, batch, logs=None):
    #    print('Training: batch {} begins at {}'.format(batch, datetime.datetime.now().time()))

    #def on_train_batch_end(self, batch, logs=None):
    #    print('Training: batch {} ends at {}'.format(batch, datetime.datetime.now().time()))

    #def on_test_batch_begin(self, batch, logs=None):
    #    print('Evaluating: batch {} begins at {}'.format(batch, datetime.datetime.now().time()))

    #def on_test_batch_end(self, batch, logs=None):
    #    print('Evaluating: batch {} ends at {}'.format(batch, datetime.datetime.now().time()))
