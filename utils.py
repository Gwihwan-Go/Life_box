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

def interpret_hours(time, prev_info=None) :
    """
    interpret written time information and handle possible errors.
    First, It converts written str-format time to datetime module 
    Second, calculate how much times.
    Finally, return the results.
    input :
        time(str) : written time format, 
                    it could be [1-48] : [0-59].
                    In case of start time, it is allowed to write nothing. 
                    In this case, this function brings up prev_information to fill the start time.
        prev_info(datetime.module) : previous end time, in case of unwritten start time
    output :
        results(datetime.datetime) : correct and unified format of time.               
    """
    if len(time.strip())<1 : ##if no info, ex) "-17:30" not "15:30-17:30",
        return prev_info

    h_m_li = time.split(':') #[hour, min]

    while len(h_m_li) < 2 : ## no hour info, ex) not 8:55- , 55-
        h_m_li.append(h_m_li[0])
        h_m_li[0] = str(prev_info.hour) ## fill the hour info with prev info
    if int(h_m_li[0]) > 23 : 
        ##if user write 24:00 or over, datetime   can't interpret over than 23
        h_m_li[0] = str(int(h_m_li[0])-12) 

    results = datetime.strptime(":".join(h_m_li), "%H:%M")
    
    return results

def cal_hours(raw_data, dic) :
    """
    input 
        raw_data(list) : raw_data of list [['work','12:00-14:00'],['sleep','-17:00']]
        dic(default_dict) : A dictionary file to save data with
    output
        result(dict) : dictionary [activity : the hour of time]

    """
    prev_end=None
    for tm, atv in [i for i in raw_data if len(i)>0] :
        ###############read time##############
        start, end = tm.split('-')
        start_time = interpret_hours(start, prev_end)
        end_time = interpret_hours(end, start_time)
        ###############read time##############

        ###############calculate hours##############
        hour = end_time-start_time
        while hour < timedelta(0) : ##if 11 - 1 2 3 =?
            hour+=timedelta(hours=12) # 23 - 1 2 3 =?
        ###############calculate hours##############
        
        ###############read time - handling exception##############
        prev_end = end_time ##if "-17:30" not "15:30-17:30" in this case, we need to save prev_end time
        ###############read time - handling exception##############
        cate_atv=categorize.categorize(atv)  ##categroize dictionary key to more representative ones
        ####### save data zone ########
        print(f"{cate_atv}({atv}) : {hour}")
        if cate_atv in dic.keys() :
            dic[cate_atv]+=hour ##add hours
        else :
            dic[cate_atv]=hour ##init with hours

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