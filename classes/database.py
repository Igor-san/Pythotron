from PyQt5.QtSql import QSqlDatabase, QSqlQuery, QSqlTableModel
from PyQt5.QtCore import Qt, QObject, pyqtSignal, QSortFilterProxyModel
import numpy as np
import collections, datetime
#from datetime import date, time, datetime
from classes.database_ntr import *
from classes.common import *
from classes.drawresult import DrawResult

class Db(QObject): #QObject а не object для pyqtSignal
    """ основная работа с базой SQLITE """
    databaseOpened = pyqtSignal(str) #сигналы открытия, закрытия, модификации базы (полный путь текущей базы)
    databaseClosed = pyqtSignal(str)
    databaseUpdated = pyqtSignal(str)

    def __init__(self):
        super(Db, self).__init__()
        self.db = QSqlDatabase.addDatabase("QSQLITE")
        self.IsNtr=False;
        self.last_error=''
        self.lottery_config=self.LotteryConfig()
        self.path = ''
        self.isClosed = True
        self.configmodel = QSqlTableModel()
        self.historymodel =QSqlTableModel()

    def __initialized_history_model(self):
        self.historymodel.setTable("history")
        self.historymodel.select()
        self.historymodel.setHeaderData(DRAWNUMBER_COLUMN_INDEX, Qt.Horizontal, "Draw");
        self.historymodel.setHeaderData(UNIXTIME_COLUMN_INDEX, Qt.Horizontal, "Date");

    def __initialized_config_model(self):
        self.configmodel.setTable("config")
        self.configmodel.select()

    def update_history_view(self):
        """ перечитаем историю , может быть после обновления

        """
        self.__get_limit_values()
        self.historymodel.select()


    def open(self, path):
        self.path = path
        filename, file_extension = os.path.splitext(path)
        if file_extension.lower()=='.ntr':
            """ открываем как ntr. Нужно создать виртуальные history и config """
            self.db.setDatabaseName(":memory:")
            if not self.db.open():
                raise Exception('Ошибка создания базы в памяти')
            NtrDb(self.db, path); 
            self.IsNtr=True;
        else:
            """ открываем как sqlite """
            self.db.setDatabaseName(path)
            if not self.db.open():
                raise Exception('Ошибка создания открытия базы')
            self.IsNtr=False; 

        self.__load_config()
        self.__get_limit_values()

        self.__initialized_config_model()
        self.__initialized_history_model()

        self.insert_history_sql=self.__prepare_history_insert_sql() # подготовим строку запроса на будущее
        # эмитируем сигнал открытия
        self.databaseOpened.emit(self.path)
        self.isClosed = False

    def close(self):
        self.isClosed = True
        self.db.close()
        self.configmodel.clear()
        self.historymodel.clear()
        self.lottery_config=self.LotteryConfig() #aka clear()
        # Emit the signal.
        self.databaseClosed.emit(self.path)
        
    def __prepare_history_insert_sql(self):
        """ Подготовим строку для вставки нового тиража

        """
        try:
            str_list_insert = ['INSERT INTO [History] ([DrawNumber],[Timestamp]']

            for i in range(self.lottery_config.NumberOfBalls1):
                str_list_insert.append(',[P'+str(i+1)+']')

            for i in range(self.lottery_config.NumberOfBalls2):
                str_list_insert.append(',[S'+str(i+1)+']')

            str_list_insert.append(') VALUES (:DrawNumber,:Timestamp') 
            for i in range(self.lottery_config.NumberOfBalls1):
                str_list_insert.append(',:P'+str(i+1)+'')

            for i in range(self.lottery_config.NumberOfBalls2):
                str_list_insert.append(',:S'+str(i+1)+'')

            str_list_insert.append(')')

            return ''.join(str_list_insert)
        except Exception as e:
            print('__prepare_history_insert_sql error: ', e)
            return ''
        pass #end __prepare_history_insert_sql

    def __get_limit_values(self):
        """определяем первые и конечные тиражи"""
        try:
            query = QSqlQuery("SELECT * FROM history ORDER BY DrawNumber DESC LIMIT 1")
            while query.next():
                self.lottery_config.LastDrawNumber=query.value(DRAWNUMBER_COLUMN_INDEX)
                self.lottery_config.LastDrawDate=datetime.datetime.fromtimestamp(query.value(UNIXTIME_COLUMN_INDEX))

            query = QSqlQuery("SELECT * FROM history ORDER BY DrawNumber ASC LIMIT 1")
            while query.next():
                self.lottery_config.FirstDrawNumber=query.value(DRAWNUMBER_COLUMN_INDEX)
                self.lottery_config.FirstDrawDate=datetime.datetime.fromtimestamp(query.value(UNIXTIME_COLUMN_INDEX))
        except Exception as e:
            print('Db:getLimitValues error: ', e)
            dbg_except()
        pass #end getLimitValues

    def __load_config(self):
        """Загружаем настройки лотереи из таблицы config"""
        query = QSqlQuery("SELECT * FROM config")
        fieldKey = query.record().indexOf("key")
        fieldValue = query.record().indexOf("value")
        while query.next():
            key = query.value(fieldKey)
            value = query.value(fieldValue)
            self.lottery_config._parse_config_record(key,value)


    def get_draws_iter(self,fromDraw,toDraw):
        """Выбираем тиражи между fromDraw и toDraw включительно итерабельно"""
        query = QSqlQuery(f"SELECT * FROM history WHERE DrawNumber>={fromDraw} AND DrawNumber<={toDraw}")
        rec = query.record()
        fields = [rec.fieldName(i) for i in range(rec.count())]
        rowtype = collections.namedtuple('DrawResult', fields) 
        while query.next():
            rec = query.record()
            yield rowtype(*[rec.value(i) for i in range(rec.count())])

    def get_draws_balls_iter(self,fromDraw,toDraw):
        """Выбираем только шары в тиражах между fromDraw и toDraw включительно итерабельно"""
        query = QSqlQuery(f"SELECT * FROM history WHERE DrawNumber>={fromDraw} AND DrawNumber<={toDraw}")
        rec = query.record()
        fields = [rec.fieldName(i) for i in range(UNIXTIME_COLUMN_INDEX+1, rec.count())]
        rowtype = collections.namedtuple('DrawResult', fields) 
        while query.next():
            rec = query.record()
            yield [rec.value(i) for i in range(UNIXTIME_COLUMN_INDEX+1, rec.count())]

    def get_draws_balls_numpy(self,fromDraw,toDraw):
        """Выбираем только шары в тиражах между fromDraw и toDraw включительно и возвращаем в виде двумерного массива Numpy"""
        query = QSqlQuery(f"SELECT * FROM history WHERE DrawNumber>={fromDraw} AND DrawNumber<={toDraw}")
        rec = query.record()
        data = np.empty((0,rec.count()-UNIXTIME_COLUMN_INDEX-1), dtype=int)
        while query.next():
            rec = query.record()
            arr=[rec.value(i) for i in range(UNIXTIME_COLUMN_INDEX+1, rec.count())]
            data=np.append(data,[arr], axis=0)
        return data
        pass #getNumpyDrawsBalls

    def add_draw(self, draw):
        """ Записываем draw:DrawResult в базу
        
        """
        try:
            self.last_error=''
            query = QSqlQuery()
            query.prepare(self.insert_history_sql)
            query.bindValue(":DrawNumber", draw.draw_number)
            query.bindValue(":Timestamp",draw.draw_date.timestamp())
           
            #а теперь шары P
            for i in range(self.lottery_config.NumberOfBalls1):
                query.bindValue(":P"+str(i+1), draw.balls1[i])
                pass
            #а теперь шары S
            for i in range(self.lottery_config.NumberOfBalls2):
                query.bindValue(":S"+str(i+1), draw.balls2[i])
                pass
    
            # эмитируем сигнал 
            self.databaseUpdated.emit(self.path)
            return query.exec_()

        except Exception as e:
            self.last_error=printf('update_draws error: ', e)
            dbg_except()
            return false
        pass # add_draw

    class LotteryConfig(object):
        """ класс конфигурации лотереи из таблицы config """
        def __init__(self):
            """ это хранится в конфиге"""
            self.NumberOfBalls1=0
            self.StartOfBalls1=0
            self.EndOfBalls1=0
            self.NumberOfBalls2=0
            self.StartOfBalls2=0
            self.EndOfBalls2=0
            self.DataImportPlugin='' #имя файла без расширения .py

            """ это вспомогательное - вычисляется"""
            self.LastDrawNumber=0
            self.LastDrawDate=datetime.date.min
            self.FirstDrawNumber=0
            self.FirstDrawDate=datetime.date.min

            pass #end __init__

        def _parse_config_record(self, key,value):
            """ парсим параметры конфигурации """
            if key.lower() == 'NumberOfBalls1'.lower(): self.NumberOfBalls1=int(value)
            elif key.lower() == 'NumberOfBalls2'.lower(): self.NumberOfBalls2=int(value)
            elif key.lower() == 'StartOfBalls1'.lower(): self.StartOfBalls1=int(value)
            elif key.lower() == 'StartOfBalls2'.lower(): self.StartOfBalls2=int(value)
            elif key.lower() == 'EndOfBalls1'.lower(): self.EndOfBalls1=int(value)
            elif key.lower() == 'EndOfBalls2'.lower(): self.EndOfBalls2=int(value)
            elif key.lower() == 'DataImportPlugin'.lower(): self.DataImportPlugin=str(value)
