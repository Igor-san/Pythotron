import traceback
import sys
import os
import string
import datetime
import locale
from dateutil import rrule

_locale_radix = locale.localeconv()['decimal_point']

class MyException(Exception):
    def __init__(self, message):
        self.message = message
    def __str__(self):
        return self.message

def dbg_except():
    """Функция для отладки операторов try-except"""
    print(sys.exc_info())
    print(" ".join(traceback.format_exception(*sys.exc_info())))


def printf(*args):
    """ аналог print но возвращает строку"""
    return ''.join(map(str, args)) 


def string_to_float(value):
    '''
    Универсальное преобразование, меняем и . и , в системный десятичный разделитель. Но разделителей разряда быть не должно

    '''

    value = value.replace(".", _locale_radix)
    value = value.replace(",", _locale_radix)
    return float(value)

def string_to_float_old(value):
    '''
    Преобразуем флоат из строки NTR в float так как у меня , а в англоинтерфейсе используется.

    '''

    if _locale_radix != ',':
        value = value.replace(",", _locale_radix)
    return float(value)

def weeks_between(start_date, end_date):
    """ количестве недель между датами"""
    weeks = rrule.rrule(rrule.WEEKLY, dtstart=start_date, until=end_date)
    return weeks.count()

def compare_balls(balls1,balls2):
    """ сравним два массива c шарами на количество совпадений
    balls1 и balls1 одномерные массивы шаров тиража,например [3,15,36,44] и [2,33,12,11]!
    """
    coins=0
    for ball1 in balls1:
        for ball2 in balls2:
            if ball1==ball2:coins+= 1

    return coins
       
    pass #compare_balls

def openurl(url):
    try:
        if sys.platform=='win32':
            os.startfile(url)
        elif sys.platform=='darwin':
            subprocess.Popen(['open', url])
        else:
            subprocess.Popen(['xdg-open', url])
    except OSError:
            print ('Пожалуйста, откройте адрес в браузере: '+url)

def compare_balls_detail(balls1,balls2, by_position=False):
    """ сравним два массива c шарами на количество совпадений и отображение самих совпадений
    balls1 и balls1 одномерные массивы шаров тиража,например [3,15,36,44] и [2,33,12,11]!
    Если задано by_position - то по позициям
    Возвращаем кортеж {число совпадений,какие номера совпали}
    """
    if by_position:
        return __compare_balls_detail_pos(balls1,balls2)

    coins=0
    detail=''
    for ball1 in balls1:
        for ball2 in balls2:
            if ball1==ball2:
                coins+= 1
                detail+=str(ball1)+' '

    return (coins,detail)
       
    pass #compare_balls_detail

def __compare_balls_detail_pos(balls1,balls2):
    """ сравним два массива c шарами на количество совпадений и отображение самих совпадений ПО ПОЗИЦИЯМ
    balls1 и balls1 одномерные массивы шаров тиража,например [0,1,1,2] и [0,0,1,1]!
    Возвращаем кортеж {число совпадений,какие номера совпали}
    """
    coins=0
    detail=''
    min_len=min(len(balls1), len(balls2))
    for i in range(min_len):
        if balls1[i]==balls2[i]:
            coins+= 1
            detail+=str(balls1[i])+' '

    return (coins,detail)
       
    pass #compare_balls_detail_pos

def compare_draws(balls_array1,balls_array2, by_position=False):
    """ сравним два массива c шарами на количество совпадений
    balls_array1 и balls_array2 двумерные массивы шаров тиража, а не отдельный тираж!
    """
    coins=[]
    if by_position:
        for balls1 in balls_array1:
            len1=len(balls1)
            for balls2 in balls_array2:
                len2=len(balls2)
                min_len=min(len1, len2)
                one_coin=0
                for i in range(min_len):
                    if balls1[i]==balls2[i]:one_coin+= 1
                
                coins.append(one_coin)
    else:
        for balls1 in balls_array1:
            for balls2 in balls_array2:
                one_coin=0
                for ball1 in balls1:
                    for ball2 in balls2:
                        if ball1==ball2:one_coin+= 1
                        
                coins.append(one_coin)
    return coins
       
    pass #compare_draws
