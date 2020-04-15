import collections, datetime

class DrawResult:
    """результат одного розыгрыша"""
    def __init__(self):
        self.draw_number =0
        self.draw_date =datetime.date.min
        self.balls1 = []
        self.balls2 = []

    def __str__(self):
        str_list = []
        str_list.append('№ '+str(self.draw_number))
        str_list.append('от '+self.draw_date.strftime("%Y-%m-%d"))
        for num in self.balls1:
            str_list.append(str(num))
        if len(self.balls2)>0:
            str_list.append('|') 
            for num in self.balls2:
                str_list.append(str(num))   
        return ' '.join(str_list)