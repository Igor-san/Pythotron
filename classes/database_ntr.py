"""
Загрузка файлов формата Lottoball NTR
"""

import os
import locale
import datetime

from PyQt5.QtSql import QSqlQuery
from PyQt5.QtWidgets import QApplication

from classes.common import *

_locale_radix = locale.localeconv()['decimal_point']

def string_to_float(value):
    '''
    Преобразуем флоат из строки NTR в float так как у меня , а в англоинтерфейсе используется.

    '''
    if _locale_radix != ',':
        value = value.replace(",", _locale_radix)
    return float(value)

class NtrDb:
    """
    Загружаем информацию из NTR в SQLITE в памяти

    """
    def __init__(self, database, file): #e:
        self.Version=0
        self.insert_history_sql='' #здесь будет запрос инсерта тиражей

        if not self.__load_ntr(file): #если проблемы с загрузкой файла внутри должно вызываться raise
            raise MyException('Не удалось создать базу из NTR!')

    def __parse_config(self, line):
        line= line.strip('[]')
        record=line.split("=")
        if len(record)==2:
            key=record[0].strip()
            value=record[1].strip()

            if key.lower()=='LastDrawNumberFromSiteUrl'.lower():
                self.LastDrawNumberFromSiteUrl= value
            elif key.lower()=='GameName'.lower():
                self.GameName= value       
            elif key.lower()=='DefaultWinCost'.lower():
                self.DefaultWinCost= str(value) 
            elif key.lower()=='NumberOfBalls1'.lower():
                self.NumberOfBalls1= int(value) 
            elif key.lower()=='NumberOfBalls2'.lower():
                self.NumberOfBalls2= int(value) 
            elif key.lower()=='EndOfBalls1'.lower():
                self.EndOfBalls1= int(value) 
            elif key.lower()=='EndOfBalls2'.lower():
                self.EndOfBalls2= int(value) 
            elif key.lower()=='StartOfBalls1'.lower():
                self.StartOfBalls1= int(value) 
            elif key.lower()=='StartOfBalls2'.lower():
                self.StartOfBalls2= int(value) 
            elif key.lower()=='DefaultVariantCost'.lower():
                self.DefaultVariantCost= string_to_float(value) 

            query = QSqlQuery()
            query.prepare("INSERT INTO [Config] ([Key],[Value]) VALUES (:key, :value)")
            query.bindValue(":key", key)
            query.bindValue(":value", value)
            query.exec_()
            pass #end 

    def __parse_version(self, line):
        line= line.strip('[]')
        record=line.split("=")
        if len(record)==2:
            if record[0].strip()=='Version':
                self.Version=int(record[1].strip())
                return True

        return False

    def __parse_data(self, line):
        """ парсим одну строку и вносим в базу

        """
        try:
            query = QSqlQuery()
            query.prepare(self.insert_history_sql)

            dict=line.split(';')
            draw_data=datetime.datetime.strptime(dict[0], '%d.%m.%Y')
            query.bindValue(":Timestamp", draw_data.timestamp())

            step_from=2
            if (self.Version<2):
                draw_number=int(dict[2])
                step_from=3
            else:
                draw_number=int(dict[1])

            query.bindValue(":DrawNumber", draw_number)

            #а теперь шары P
            for i in range(self.NumberOfBalls1):
                query.bindValue(":P"+str(i+1), dict[i+step_from])
                pass
            #а теперь шары S
            step_from +=self.NumberOfBalls1
            for i in range(self.NumberOfBalls2):
                query.bindValue(":S"+str(i+1), dict[i+step_from])
                pass

            query.exec_()
            return True
        except Exception as e:
            print('_create_history_table error: ', e)
            return False
        pass #end _parse_data

    def __create_history_table(self):
        try:
            str_list = []
            str_list_insert = []
            str_list.append('CREATE TABLE [History] ([Id] integer NOT NULL PRIMARY KEY AUTOINCREMENT,[DrawNumber] integer NOT NULL,[Timestamp] integer NOT NULL')
            str_list_insert.append('INSERT INTO [History] ([DrawNumber],[Timestamp]')

            for i in range(self.NumberOfBalls1):
                str_list.append(',[P'+str(i+1)+'] integer NOT NULL')
                str_list_insert.append(',[P'+str(i+1)+']')

            for i in range(self.NumberOfBalls2):
                str_list.append(',[S'+str(i+1)+'] integer NOT NULL')
                str_list_insert.append(',[S'+str(i+1)+']')

            str_list.append(')')
            sql=''.join(str_list)
            query = QSqlQuery()
            query.exec(sql)

            str_list_insert.append(') VALUES (:DrawNumber,:Timestamp') 
            for i in range(self.NumberOfBalls1):
                str_list_insert.append(',:P'+str(i+1)+'')

            for i in range(self.NumberOfBalls2):
                str_list_insert.append(',:S'+str(i+1)+'')

            str_list_insert.append(')')
            self.insert_history_sql=''.join(str_list_insert)

            return True
        except Exception as e:
            print('_create_history_table error: ', e)
            return False
        pass #end _create_history_table

    def __load_ntr(self, filename):
        """
        Загрузка из NTR
        """
        first_line=True #в 1 строке  должно быть [Version=2]
        self.history_count=0

        #создадим нужные таблицы
        query = QSqlQuery()
        query.exec("CREATE TABLE [Config] ([Id] integer NOT NULL PRIMARY KEY AUTOINCREMENT,[Key] string NOT NULL,[Value] string NOT NULL)")
        #вначале спарсим и заполним Config
        read_options=False
        read_history=False
        i=1
        with open(filename, "r") as f:
            for line in f:
                if not i % 100:  # let application process events each 100 steps.
                    QApplication.processEvents()
                i+=1
                #print(line, end='') # строки оканчиваются символом ‘\n’
                line=line.strip()
                
                if not line:
                    continue

                if first_line:
                    if not self.__parse_version(line):
                        raise MyException('На первой строке отстутствует версия файла!')
                    first_line=False
                    continue

                if line.startswith(OPTIONS_START): #start option
                    read_options=True
                    continue

                if line.startswith(OPTIONS_END): #end option
                    read_options=False
                    continue        

                if line.startswith(GAME_DATA_START): #начало истории
                    if not self.__create_history_table(): #создадим таблицу с историей
                        return False
                    read_history=True
                    continue

                if line.startswith(GAME_DATA_END): #end истории
                     read_history=False
                     continue

                if line.startswith('[') and read_options:
                    self.__parse_config(line) #парсим конфигурацию

                elif read_history:
                    if not self.__parse_data(line):  #а тут заносим в таблицу с историей наши тиражи
                        return False

        return True




