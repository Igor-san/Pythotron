from PyQt5.QtSql import QSqlDatabase, QSqlQuery, QSqlTableModel
from PyQt5.QtCore import Qt, QObject, pyqtSignal, QSortFilterProxyModel
import numpy as np
import collections
import datetime
import distutils.util

from classes.database_ntr import *
from classes.common import *
from classes.constants import *
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
        self.historymodel.setHeaderData(DRAWNUMBER_COLUMN_INDEX, Qt.Horizontal, "№");
        self.historymodel.setHeaderData(UNIXTIME_COLUMN_INDEX, Qt.Horizontal, "Дата");
        if self.lottery_config.IsFonbet:
            self.historymodel.setHeaderData(FONBETID_COLUMN_INDEX, Qt.Horizontal, "Id");

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

        self.select_balls_sql = '' # внутри self.__prepare_history_insert_sql()
        self.insert_history_sql = '' # внутри self.__prepare_history_insert_sql()
        self.__prepare_history_insert_sql() # подготовим некоторые строки запроса на будущее в зависимости от числа шаров

        self.insert_prizes_sql = '' # внутри self.__prepare_prizes_insert_sql()
        self.__prepare_prizes_insert_sql() # подготовим строку запроса на будущее

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
            str_list_insert = ['INSERT INTO [History] ([DrawNumber],[Timestamp]'] # запрос на вставку
            str_select_balls=[] # часть запроса номеров P1,P2....S2

            for i in range(self.lottery_config.NumberOfBalls1):
                str_list_insert.append(',[P'+str(i+1)+']')
                str_select_balls.append('P'+str(i+1))

            for i in range(self.lottery_config.NumberOfBalls2):
                str_list_insert.append(',[S'+str(i+1)+']')
                str_select_balls.append('S'+str(i+1))

            if self.lottery_config.IsFonbet:
                str_list_insert.append(',[FonbetId]')

            str_list_insert.append(') VALUES (:DrawNumber,:Timestamp') 
            for i in range(self.lottery_config.NumberOfBalls1):
                str_list_insert.append(',:P'+str(i+1)+'')

            for i in range(self.lottery_config.NumberOfBalls2):
                str_list_insert.append(',:S'+str(i+1)+'')

            if self.lottery_config.IsFonbet:
                str_list_insert.append(',:FonbetId')

            str_list_insert.append(')')

            self.select_balls_sql = ','.join(str_select_balls)
            self.insert_history_sql =  ''.join(str_list_insert)

        except Exception as e:
            print('__prepare_history_insert_sql error: ', e)
            dbg_except()
        pass #end __prepare_history_insert_sql

    def __prepare_prizes_insert_sql(self):
        """ Подготовим строку для вставки призов нового тиража

        """
        try:
            str_list_insert = ['INSERT INTO [Prizes] ([DrawId]']

            for i in range(len(self.lottery_config.WinCategoriesPrizesArray)):
                str_list_insert.append(f',[{self.lottery_config.WinCategoriesPrizesArray[i]}]')

            str_list_insert.append(') VALUES (:DrawId')

            for i in range(len(self.lottery_config.WinCategoriesPrizesArray)):
                str_list_insert.append(f',:{self.lottery_config.WinCategoriesPrizesArray[i]}')

            str_list_insert.append(')')

            self.insert_prizes_sql = ''.join(str_list_insert)
        except Exception as e:
            print('__prepare_prizes_insert_sql error: ', e)
            dbg_except()
        pass #end __prepare_prizes_insert_sql

    def __get_limit_values(self):
        """определяем первые и конечные тиражи"""
        try:
            query = QSqlQuery("SELECT * FROM history ORDER BY DrawNumber DESC LIMIT 1")
            while query.next():
                self.lottery_config.LastDrawNumber=query.value(DRAWNUMBER_COLUMN_INDEX)
                self.lottery_config.LastDrawDate=datetime.datetime.fromtimestamp(query.value(UNIXTIME_COLUMN_INDEX))
                if self.lottery_config.IsFonbet:
                    self.lottery_config.LastFonbetId=query.value(FONBETID_COLUMN_INDEX)

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
        #типа self.select_balls_sql='P 1, P2 .... S2'
        query = QSqlQuery(f"SELECT {self.select_balls_sql} FROM history WHERE DrawNumber>={fromDraw} AND DrawNumber<={toDraw}")
        rec = query.record()
        data = np.empty((0,rec.count()), dtype=int)
        while query.next():
            rec = query.record()
            arr=[rec.value(i) for i in range(rec.count())]
            data=np.append(data,[arr], axis=0)
        return data

        #data = np.empty((0,rec.count()-UNIXTIME_COLUMN_INDEX-1), dtype=int)
        #while query.next():
        #    rec = query.record()
        #    arr=[rec.value(i) for i in range(UNIXTIME_COLUMN_INDEX+1, rec.count())]
        #    data=np.append(data,[arr], axis=0)
        #return data
        pass # end get_draws_balls_numpy

    def get_last_fonbet_id(self):
        """ Для фонбетовской базы получаем fonbet_id для последнего тиража из базы"""
        """ Но также при загрузке базы получаю в __get_limit_values """
        try:
            query = QSqlQuery(f"SELECT FonbetId FROM history ORDER BY DrawNumber DESC LIMIT 1")
            while query.next():
                return query.record().value(0)
            return None
        except Exception as e:
            print('database error get_last_fonbet_id: ', e)
            dbg_except()
            return None
        pass  # end get_last_fonbet_id

    def add_draw(self, draw):
        """ Записываем draw:DrawResult в базу
        
        """
        try:
            self.last_error=''
            #History
            query = QSqlQuery()
            query.prepare(self.insert_history_sql)
            query.bindValue(":DrawNumber", draw.draw_number)
            query.bindValue(":Timestamp", draw.draw_date.timestamp())

            #а теперь шары P
            for i in range(self.lottery_config.NumberOfBalls1):
                query.bindValue(":P"+str(i+1), draw.balls1[i])
                pass
            #а теперь шары S
            for i in range(self.lottery_config.NumberOfBalls2):
                query.bindValue(":S"+str(i+1), draw.balls2[i])
                pass
            #а теперь FonbetId
            if self.lottery_config.IsFonbet:
                query.bindValue(":FonbetId", draw.fonbet_id)
                pass

            result=query.exec_()
            if not result:
                return False

            #Prizes а теперь выигрыши если есть
            if draw.wins:
                last_insert_id =query.lastInsertId();
                query = QSqlQuery()
                query.prepare(self.insert_prizes_sql)
                query.bindValue(":DrawId", last_insert_id)
                for i in range(len(self.lottery_config.WinCategoriesPrizesArray)):
                    newkey=self.lottery_config.WinCategoriesPrizesArray[i].replace('WP',"").replace('S','+')  #удалим WP и заменим S на +
                    query.bindValue(f':{self.lottery_config.WinCategoriesPrizesArray[i]}', draw.wins.get(newkey,0.0))
                result=query.exec_()
                pass

            # эмитируем сигнал 
            self.databaseUpdated.emit(self.path)

            return result

        except Exception as e:
            self.last_error=printf('update_draws error: ', e)
            dbg_except()
            return False
        pass # add_draw

    class LotteryConfig(object):
        """ класс конфигурации лотереи из таблицы config """
        def __init__(self):
            """ это хранится в конфиге"""
            self.LottoName = ""
            self.NumberOfBalls1=0
            self.StartOfBalls1=0
            self.EndOfBalls1=0
            self.NumberOfBalls2=0
            self.StartOfBalls2=0
            self.EndOfBalls2=0
            self.DataImportPlugin='' # имя файла отвечающего за обновление без расширения .py
            self.WinCategories=''
            self.DefaultWinCost=''
            self.GameType = "" # Toto для Фонбета
            self.IsTop3=False;
            self.IsFonbet=False;
            self.MultipleAppearance1=False;
            self.MultipleAppearance2=False;
            self.WithWins=False;

            """ это вспомогательное - вычисляется"""
            self.LastDrawNumber=0
            self.LastDrawDate=datetime.date.min
            self.FirstDrawNumber=0
            self.FirstDrawDate=datetime.date.min
            self.WinCategoriesPrizesArray=[]
            self.LastFonbetId=0 # Fonbet only
            pass #end __init__

        def _parse_config_record(self, key,value):
            """ парсим параметры конфигурации """
            if key.lower() == 'LottoName'.lower(): self.LottoName=str(value)
            elif key.lower() == 'NumberOfBalls1'.lower(): self.NumberOfBalls1=int(value)
            elif key.lower() == 'NumberOfBalls2'.lower(): self.NumberOfBalls2=int(value)
            elif key.lower() == 'StartOfBalls1'.lower(): self.StartOfBalls1=int(value)
            elif key.lower() == 'StartOfBalls2'.lower(): self.StartOfBalls2=int(value)
            elif key.lower() == 'EndOfBalls1'.lower(): self.EndOfBalls1=int(value)
            elif key.lower() == 'EndOfBalls2'.lower(): self.EndOfBalls2=int(value)
            elif key.lower() == 'DataImportPlugin'.lower(): self.DataImportPlugin=str(value)
            elif key.lower() == 'WinCategories'.lower():
                self.WinCategories=str(value)
                self._prepare_prizes_array()
            elif key.lower() == 'DefaultWinCost'.lower(): self.DefaultWinCost=str(value)     
            elif key.lower() == 'GameType'.lower(): self.GameType=str(value)
            elif key.lower() == 'IsFonbet'.lower(): self.IsFonbet=bool(distutils.util.strtobool(value))
            elif key.lower() == 'IsTop3'.lower():  self.IsTop3=bool(distutils.util.strtobool(value))
            elif key.lower() == 'WithWins'.lower(): self.WithWins=bool(distutils.util.strtobool(value))
            elif key.lower() == 'MultipleAppearance1'.lower(): self.MultipleAppearance1=bool(distutils.util.strtobool(value))
            elif key.lower() == 'MultipleAppearance2'.lower(): self.MultipleAppearance2=bool(distutils.util.strtobool(value))
        
        def _prepare_prizes_array(self):
            """из 4+1,5,...,8,8+1 сделать список['WP4S1,WP5,...WP8,WP8S1']  """
            arr=self.WinCategories.split(',')
            self.WinCategoriesPrizesArray.clear()
            for line in arr:
                line='WP'+line.replace('+','S')
                self.WinCategoriesPrizesArray.append(line)
            pass

   