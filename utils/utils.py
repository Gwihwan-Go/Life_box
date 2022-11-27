import os
from datetime import datetime, timedelta
import math
from pytz import timezone

def get_env() :
    #print current kst time
    print('The code is running at :',time_info())
    try : 
        if os.environ['GITHUB_ACTIONS'] :
            print( "Running in GitHub Actions" )
            return True
    except :
        print( "Running in Local Device" )
        return False
    


def add_dictionary(dic1, dic2) :
    """
    add two dictionaries
    """
    for key, value in dic2.items() :
        if key in dic1 :
            dic1[key] += value
        else :
            dic1[key] = value
    return dic1

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

def write_text_file(file_content, period, output_path) :
    """
    write text file which would be the git file at last.
    input :
        file_content(str) : string to be written
        start_day, end_day(datetime) : start day and end day
        output_path(str) : save path
    
    """
    #get datetime object from n day before today
    start_day = datetime.now() - timedelta(days=period[-1] - 1) + timedelta(hours=9)
    end_day = datetime.now() - timedelta(days=period[0]) + timedelta(hours=9)
    footer = f"Last refresh: {time_info('Asia/Seoul')}"
    with open(output_path, 'w') as f :
        f.write(f"My life Overview in period of {start_day.month}/{start_day.day} ~ {end_day.month}/{end_day.day} [averaged]\n")
        f.writelines(file_content)
        f.write('\n')
        f.write(footer)
    f.close()
    print(f"{start_day.month}/{start_day.day} ~ {end_day.month}/{end_day.day} records has successfully saved at {output_path}")

def calculate_start_end_day(start_day,period) :
    """
    calculate start day and end day
    input :
        start_day(datetime) : start day
        period(int) : number of days to calculate
    output :
        day_range(list) : [how_many_days_before_today-period, how_many_days_before_today]
                        [1,7] : 1 week ago ~ yesterday(6 days)
                        [2,10] : 10 days ago ~ 2 days ago(8 days)
    """
    ## convert start_day to datetime object
    if '/' in start_day :
        start_day = datetime.strptime(start_day, '%m/%d')
    elif '-' in start_day :
        start_day = datetime.strptime(start_day, '%m-%d')
    
    now = datetime.now()+timedelta(hours=9)
    start_day = start_day.replace(year=datetime.now().year)
    end_day = now - start_day + timedelta(days=period)
    start_day = now - start_day.replace(year=datetime.now().year)

    return [start_day.days, end_day.days]

def update_gist(file_path, gist_id, auth_token):
    import gistyc
    # Initiate the GISTyc class with the auth token
    gist_api = gistyc.GISTyc(auth_token=auth_token)

    # Update the GIST based on the GISTs ID
    response_update_data = gist_api.update_gist(file_name=file_path,
                                                gist_id=gist_id)
    print(f"gist has successfully updated to {response_update_data['url']}")

if __name__ == "__main__" :
    ##For github actions##
    try :
        if os.environ['GITHUB_ACTIONS'] :
            auth_token = os.environ['auth_token']
            gist_id = os.environ['gist_id']
    ##For github actions##
    except :
        import yaml
        with open('config.yaml') as f:
            config = yaml.safe_load(f)
        f.close()
    file_path='./result.txt'
    update_gist(file_path, config['gist_id'], config['auth_token'])
    startdays = "7/27"
    period = 7
    print(calculate_start_end_day(startdays,period))
