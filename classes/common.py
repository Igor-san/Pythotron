import traceback, sys, os, string

ORGANIZATION_NAME = 'HomeSoft'
ORGANIZATION_DOMAIN = 'homesoft.ru'
APPLICATION_NAME = 'Pythotron'
FILES_TYPES ="Sqlite (*.sqlite *.db);;Lottoball (*.ntr);;All files (*.*)"

DATABASES_FOLDER='databases' #где базы
DATAIMPORT_FOLDER='dataimport' #где плагины обновления

DRAWNUMBER_COLUMN_INDEX=1
UNIXTIME_COLUMN_INDEX=2 #индекс столбца с датой в history

EUROJACKPOT_PLAY_URL='https://bit.ly/3a29Nxt'
EUROMILLIONS_PLAY_URL='https://bit.ly/2V2UvEu'
LOTTERY_PLAY_URL='https://bit.ly/2yUPK7p'

HELP_URL='https://upad.ru/viewtopic.php?f=20&t=5132'#сслыка на тему в форуме

OPTIONS_START='[Options Start]'
OPTIONS_END='[Options End]'
GAME_DATA_START='[Game Data Start]'
GAME_DATA_END  = '[Game Data End]'

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

def compare_balls_detail(balls1,balls2):
    """ сравним два массива c шарами на количество совпадений и отображение самих совпадений
    balls1 и balls1 одномерные массивы шаров тиража,например [3,15,36,44] и [2,33,12,11]!
    """
    coins=0
    detail=''
    for ball1 in balls1:
        for ball2 in balls2:
            if ball1==ball2:
                coins+= 1
                detail+=str(ball1)+' '

    return (str(coins)+':'+detail)
       
    pass #compare_balls_detail

def compare_draws(balls_array1,balls_array2):
    """ сравним два массива c шарами на количество совпадений
    balls_array1 и balls_array2 двумерные массивы шаров тиража, а не отдельный тираж!
    """
    coins=[]
    for balls1 in balls_array1:
        for balls2 in balls_array2:
            one_coin=0
            for ball1 in balls1:
                for ball2 in balls2:
                    if ball1==ball2:one_coin+= 1
                        
            coins.append(one_coin)
    return coins

       
    pass #compare_draws
