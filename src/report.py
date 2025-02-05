from enum import Enum
from datetime import date, timedelta
from src.interpretNotionPage import interpret_table_contents
from src.utils import add_dictionary

class NotionProperties(Enum):
    STUDY_TIME = "有价值时间"
    # Add other property names here as needed
    
def report_study_and_revise_db(client, date=date.today() - timedelta(days=1)):
    """
    Report the study time from the data.
    """
    date_str = date.isoformat()
    page_ids = client.query_database_by_date_range(date_str, date_str)
    print(f'Processing {date_str}...')
    all_data = {}
    for page_id in page_ids:
        page_id = page_id.replace('-', '')
        table = client.read_page_tables(page_id)
        print(f'Processing {page_id}...')
        new_data = interpret_table_contents(table)
        study_time = extract_study_time(new_data)
        print(f'Study time: {study_time}')
        print(f'Pretty time: {pretty_time(study_time)}')
        add_study_time_todb(client, page_id, pretty_time(study_time))
        
    # print(all_data)
    # study_time = extract_study_time(all_data)
    # print(f'Study time: {study_time}')
    return all_data

def pretty_time(time):
    """
    Convert the time to a pretty string.
    Args:
        time (timedelta): The time to convert
    Returns:
        str: A formatted string in the format "Xh Ym" or "Ym" if hours is 0
    """
    total_minutes = int(time.total_seconds() / 60)
    hours = total_minutes // 60
    minutes = total_minutes % 60
    
    if hours > 0:
        return f"{hours}hrs {minutes}mins"
    return f"{minutes}mins"

def is_study_key(key):
    """
    Check if the key is a study key.
    """
    return key == '📖Academic' or key == '💰Work' or key == '🧹Chores'

def extract_study_time(data):
    """
    Extract the study time from the data.
    Returns the total time spent on study-related activities.
    """
    total_time = timedelta()
    for key, value in data.items():
        if is_study_key(key):
            total_time += value
            print(f'{key}: {value}')
    return total_time

def add_study_time_todb(client, page_id, time):
    """
    Revise the database with the study time.
    """
    try:
        print(f'Adding {time} to {page_id}')
        client.update_page_property(page_id, NotionProperties.STUDY_TIME.value, time)
        print(f'Added {time} to {page_id}')
    except Exception as e:
        print(f'Failed to add study time to {page_id}: {str(e)}')
