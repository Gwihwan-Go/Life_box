from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from collections import defaultdict
from src.utils import add_dictionary
from src.classifyContents import categorize, print_and_clear_unlist_words

def extract_table_content(html_content: str) -> List[List[str]]:
    """Extract table content from HTML using simple string parsing.
    
    Args:
        html_content: HTML content of the page
        
    Returns:
        List of rows where each row is [activity, time_range]
    """
    result = []
    
    # Extract title
    title_start = html_content.find('<title>')
    title_end = html_content.find('</title>')
    if title_start != -1 and title_end != -1:
        title = html_content[title_start + 7:title_end].strip().split()[-1]
        result.append([title, 'sleep'])

    # Extract table data
    table_start = html_content.find('<table')
    table_end = html_content.find('</table>')
    
    if table_start != -1 and table_end != -1:
        table_content = html_content[table_start:table_end]
        rows = table_content.split('<tr')
        
        for row in rows[1:]:  # Skip first split result
            if '<td' in row:
                cols = []
                td_parts = row.split('<td')
                
                for td in td_parts[1:]:  # Skip first split result
                    end_td = td.find('</td>')
                    if end_td != -1:
                        text = td[:end_td]
                        # Remove any remaining HTML tags
                        while '<' in text and '>' in text:
                            tag_start = text.find('<')
                            tag_end = text.find('>')
                            text = text[:tag_start] + text[tag_end + 1:]
                        cols.append(text.strip())
                
                if cols:
                    result.append([col for col in cols if col])

    return [row for row in result if len(row) > 0]

def parse_time_range(time_str: str) -> Tuple[str, str]:
    """Split time range into start and end times.
    
    Args:
        time_str: Time range string (e.g. "12:00-14:00" or "-17:00")
        
    Returns:
        Tuple of (start_time, end_time)
    """
    if '-' not in time_str:
        return ('', time_str)
    start, end = time_str.split('-')
    return (start, end)

def get_time_info_without_errors(time: str, prev_info: Optional[datetime] = None) -> Optional[datetime]:
    """Parse time string into datetime, handling edge cases.
    
    Args:
        time: Time string in HH:MM format
        prev_info: Previous end time for context
        
    Returns:
        Parsed datetime or None if invalid
    """
    if not time.strip():
        return prev_info

    h_m_li = time.split(':')
    
    if len(h_m_li) < 2:
        if not prev_info:
            return None
        h_m_li.append(h_m_li[0])
        h_m_li[0] = str(prev_info.hour)
        
    hour = int(h_m_li[0])
    if hour > 23:
        hour -= 12
        h_m_li[0] = str(hour)

    try:
        return datetime.strptime(":".join(h_m_li), "%H:%M")
    except ValueError:
        return None

def calculate_duration(start: datetime, end: datetime) -> timedelta:
    """Calculate duration between two times, handling overnight periods.
    
    Args:
        start: Start datetime
        end: End datetime
        
    Returns:
        Duration as timedelta
    """
    duration = end - start
    while duration < timedelta(0):
        duration += timedelta(hours=12)
    return duration

def interpret_table_contents(raw_data: List[List[str]]) -> Dict[str, timedelta]:
    """Convert raw table data into categorized duration totals.
    
    Args:
        raw_data: List of [time_range, activity] rows
        
    Returns:
        Dictionary mapping activity categories to total durations
    """
    dic = defaultdict(timedelta)
    prev_end = None
    
    for row in [r for r in raw_data if len(r) > 1]:
        time_str, activity = row[0], row[1]
        
        start_str, end_str = parse_time_range(time_str)
        ##TODO If this is the first row, we need to get the time from the previous day  
        start = get_time_info_without_errors(start_str, prev_end)
        end = get_time_info_without_errors(end_str, start)
        
        if not all([start, end]):
            continue
            
        duration = calculate_duration(start, end)
        prev_end = end
        
        activities = activity.split('/')
        duration_per_activity = duration / len(activities)
        
        for activity in activities:
            category = categorize(activity)
            dic[category] += duration_per_activity
            
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
            raw_time_data = extract_table_content(inner_dict[month][day])
            ## add dictionary files
            time_data = add_dictionary(time_data, interpret_table_contents(raw_time_data))
            
    print_and_clear_unlist_words()
    time_data = dict(sorted(list(time_data.items()), key=lambda x : x[1], reverse=True))
    return time_data

if __name__ == "__main__" :

    from utils import *
    from src.classifyContents import *
    atv = 'road - hello hi god'
    for part_atv in atv.split('/') :
        print(part_atv)
        cate_atv=categorize(part_atv)
        print(cate_atv)