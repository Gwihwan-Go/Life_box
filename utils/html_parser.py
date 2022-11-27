from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from utils.utils import *
from utils.nlp_utils import *
from collections import defaultdict

def collect_table_content(content) :
    """
    input 
        content(str) : content of the page
    output
        result(list) : raw_data of list [['work','12:00-14:00'],['sleep','-17:00']]
        
    """
    result = []
    document= BeautifulSoup(content,"html.parser")
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

def get_time_info_without_errors(time, prev_info=None) :
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

def interpret_table_contents(raw_data) :
    """
    watch : 0:40:00
    dog : 0:30:00
    Restroom : 1:00:00
    watch : 0:50:00
    ==> '😌recharging': datetime.timedelta(seconds=10800)
    table 
    activity1 | time ==> categorized_activity | summed_time in period
    activity2 | time ==> categorized_activity2 | summed_time in period
    input 
        raw_data(list) : raw_data of list [['work','12:00-14:00'],['sleep','-17:00']]
        dic(default_dict) : A dictionary file to save data with
    output
        result(dict) : dictionary [activity : the hour of time]

    """

    prev_end=None
    dic = defaultdict(timedelta)
    
    for tm, atv in [i for i in raw_data if len(i)>0] :
        ###############read time##############
        start, end = tm.split('-')
        start_time = get_time_info_without_errors(start, prev_end)
        end_time = get_time_info_without_errors(end, start_time)
        ###############read time##############

        ###############calculate hours##############
        hour = end_time-start_time
        while hour < timedelta(0) : ##if 11 - 1 2 3 =?
            hour+=timedelta(hours=12) # 23 - 1 2 3 =?
        ###############calculate hours##############
        
        ###############read time - handling exception##############
        prev_end = end_time ##if "-17:30" not "15:30-17:30" in this case, we need to save prev_end time
        ###############read time - handling exception##############

        for part_atv in atv.split('/') :
            cate_atv=categorize(part_atv)  ##categroize dictionary key to more representative ones
            divider = len(atv.split('/'))
            divided_hour = hour/divider
        ####### save data zone ########
            print(f" : {divided_hour}") # print activity at categorize func
            dic[cate_atv]+=divided_hour

    return dic
    

def contents_to_organized_dict(contents, target_notebook_names):
    """
    parse table contents from html contents
    Convert table contents to organized dict

    <html> ....</html>
    ->->->
    {'🌙sleep': datetime.timedelta(seconds=34200),
    '📖academic': datetime.timedelta(seconds=26100),
    '🍔food': datetime.timedelta(seconds=3900),
    '💰work': datetime.timedelta(seconds=5700),
    '🚎road': datetime.timedelta(seconds=2700),
    '😌recharging': datetime.timedelta(seconds=10800)}

    input: contents(html) : contents from onenote
           target_notebook_names(str) : target notebook names
    output: organized_dict(dict) : 
    """

    time_data = dict()
    inner_dict = {k:v for k,v in contents[target_notebook_names[0]].items() if v}
    months = inner_dict.keys()
    for month in months:
        days = inner_dict[month].keys()
        for day in days:
            #collect table from html -> list
            raw_time_data = collect_table_content(inner_dict[month][day])
            ## add dictionary files
            time_data = add_dictionary(time_data, interpret_table_contents(raw_time_data))
            
    print_and_clear_unlist_words()
    time_data = dict(sorted(list(time_data.items()), key=lambda x : x[1], reverse=True))
    return time_data

if __name__ == "__main__" :

    from utils import *
    from nlp_utils import *
    atv = 'road - hello hi god'
    for part_atv in atv.split('/') :
        print(part_atv)
        cate_atv=categorize(part_atv)
        print(cate_atv)