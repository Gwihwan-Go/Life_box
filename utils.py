import os
from bs4 import BeautifulSoup
import codecs
from datetime import datetime, timedelta
import math
import categorize
from pytz import timezone
def search_by_date(year,month,date,dir) :
    """
    choose notebook which matched month/day varaibles.
    year(int) : 2022
    month(int) : 01,02,03, ... , 10,11,12   <-- User should follow this rule.
    day(int) : 1, 2, 3, 4, 5, 6,... or 01,02,03, ...
    dir(str) : the directory of Diary, it should have subdirectory like 2022.06 , 2022.07 ...
    """

    str_year = str(year)
    if month<10 :
        str_month='0'+str(month)
    else :
        str_month=str(month)
    str_day = str(date)

    for y_m in os.listdir(dir) :
        if (y_m.startswith(str_year)) and y_m.endswith(str_month) :
            for day in os.listdir(dir+'/'+y_m) :
                if day.startswith(str_day) or day.startswith('0'+str_day) :
                    return dir+'/'+y_m+'/'+day
    
    print(f'cannot found {year}/{month}/{day} file')
    return None

def get_schedule(docs_path) :
    """
    input 
        docs_path(str) : file path of html
    output
        result(list) : raw_data of list [['work','12:00-14:00'],['sleep','-17:00']]
        
    """
    result = []
    f = codecs.open(docs_path, 'r', 'utf-8')
    document= BeautifulSoup(f.read(),"html.parser")
    table = document.find('table')
    
    if table is not None : #If there is no table in a notebook.
        rows = table.find_all('tr')
        for row in rows:
            cols = row.find_all('td')
            cols = [ele.text.strip() for ele in cols]
            result.append([ele for ele in cols if ele]) # Get rid of empty values
    title = document.find('title').get_text()
    title = title.split(' ')[-1]
    result.insert(0, [title,'sleep'])
    
    return result

def cal_hours(raw_data, dic) :
    """
    input 
        raw_data(list) : raw_data of list [['work','12:00-14:00'],['sleep','-17:00']]
        dic(default_dict) : A dictionary file to save data with
    output
        result(dict) : dictionary [activity : the hour of time]

    """
    
    for tm, atv in [i for i in raw_data if len(i)>0] :
        ###############read time##############
        start, end = tm.split('-')
        
        if len(start.strip())<1 : ##if "-17:30" not "15:30-17:30"
            start = prev_end

        if int(start.split(':')[0]) > 23 : ##if user write 24:00 or over
            h,m=start.split(':')
            start_time = datetime.strptime(":".join([str(int(h)-12),m]), "%H:%M")
        else :
            start_time = datetime.strptime(start, "%H:%M")
        if int(end.split(':')[0]) > 23 :
            h,m=end.split(':')
            end_time = datetime.strptime(":".join([str(int(h)-12),m]), "%H:%M")
        else :
            end_time = datetime.strptime(end, "%H:%M")
        ###############read time##############

        ###############calculate hours##############
        hour = end_time-start_time
        if hour < timedelta(0) : ##if 2-12 =? 
            hour+=timedelta(hours=12)
        ###############calculate hours##############
        
        ###############read time - handling exception##############
        prev_end = end ##if "-17:30" not "15:30-17:30" in this case, we need to save prev_end time
        ###############read time - handling exception##############

        ####### save data zone ########
        key_save_path = "resources/key_list.json"
        key_list=categorize.load(key_save_path)
        atv=categorize.search(atv, key_list) ##categroize dictionary key to more representative ones

        if atv in dic.keys() :
            dic[atv]+=hour ##add hours
        else :
            dic[atv]=hour ##init with hours

    return dic
def generate_file_content_line(raw_data: dict) -> str:
    """    
    from
    https://github.com/shinanxu/waka-box-py/blob/master/main.py
    Python      2 hrs 36 mins  ██████▍░░░░░░░░  41.9%
    Arguments:
        raw_data {dict} -- name, text, percent (python, 2 hrs 36 mins, 41.9%)
    Returns:
        str -- Python      2 hrs 36 mins  ██████▍░░░░░░░░  41.9%
    """
    return ' '.join([
        # name が言語名。
        raw_data['name'].ljust(11),
        # text が期間。
        raw_data['text'].ljust(14),
        # バーチャート。
        _generate_bar_chart(raw_data['percent'], 15),
        # パーセンテージ。
        str(round(raw_data['percent'], 1)).rjust(5) + '%',
    ])

def _generate_bar_chart(percent: float, size: int) -> str:
    """
    from
    https://github.com/shinanxu/waka-box-py/blob/master/main.py
    """
    full = '█'
    semifull = '█▏▎▍▌▋▊▉'
    empty = '░'
    frac = math.ceil(size * 8 * percent / 100)
    barsFull = math.ceil(frac / 8)
    semi = int(frac % 8)
    barsEmpty = size - barsFull
    return ''.join([
        full * (barsFull - 1),
        semifull[semi],
        empty * barsEmpty,
    ])

def _days_hours_minutes(td):
    hours = f"{(td.seconds)//3600+td.days*24} hrs"
    secs = f"{(td.seconds//60)%60} mins"
    return " ".join([hours, secs])

def _percent_time(time, whole) :

    return round(time / whole,3)*100

def cal_unknown(items, whole) :
    known=timedelta(seconds=0)
    for i in items.items() :
        if i[0]=='unknown' :
            continue
        known+=i[1]

    return whole-known

def preprocess_data(key, dic, whole) :
    '''sleep : time ===> 'sleep', 'time', 'percentage'''
    return {'name' : key, 'text' : _days_hours_minutes(dic[key]), 'percent' : _percent_time(dic[key], whole)}

def time_info(location='Asia/Seoul') :
    """
    input :
        location(default = 'america')
    output :
        time info
        ex) Wednesday, 03 Aug, 01:41 KST
    
    """
    now = datetime.now(timezone(location))
    
    return now.strftime("%A, %d %b, %H:%M %Z")