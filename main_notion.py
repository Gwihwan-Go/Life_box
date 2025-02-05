import argparse
from datetime import timedelta,  date
from src.html_parser import *
from src.utils import *
import yaml
import nltk
from src.notionClient import *
from pprint import pprint
import os

nltk.download('all')

def load_config():
    """Load configuration from environment variables or config file."""
    try:
        if os.environ.get('GITHUB_ACTIONS'):
            return dict(os.environ)
        
        with open('config.yaml') as f:
            return yaml.safe_load(f)
    except Exception as e:
        raise RuntimeError(f"Failed to load configuration: {str(e)}")

if __name__ == "__main__" :
    try:
        config = load_config()  # Load config at the start
        whether_update = get_env()
        unlist_words_path = 'resources/unlisted_words.txt'
        parser = argparse.ArgumentParser()

        parser.add_argument("-e", "--end_day", type=str, 
            help="It will get the data until a day before the day, 2024-07-27 for 7/20-7/26",
            action="store", 
            default=(date.today() - timedelta(days=1)).isoformat() #default is yesterday 
        )
        parser.add_argument("-s", "--start_day", type=str, 
            help="It will get the data until a day before the day, 2024-07-27 for 7/20-7/26",
            action="store", 
            default=(date.today() - timedelta(days=7)).isoformat() #default is one week before of yesterday
        )       
        parser.add_argument("-o", "--out", 
            type=str,help="output directory to store the result", 
            default="overview")      
        args = parser.parse_args()

        output_path = args.out
        
        client = NotionClient()
        page_ids = client.query_database_by_date_range(args.start_day, args.end_day)
        
        # Validate date formats
        try:
            start_date = date.fromisoformat(args.start_day)
            end_date = date.fromisoformat(args.end_day)
            days_between = (end_date - start_date).days + 1
        except ValueError as e:
            print(f"Error parsing dates: {e}")
            exit(1)
            
        print(f'Processing {days_between} days...')
        print(f'Processing {len(page_ids)} pages...')
        all_data = {}
        for page_id in page_ids:
            #get properties from page_id
            # date = get_date_from_page_id(page_id)
            # print(f'Processing {date}...')
            page_id = page_id.replace('-', '')
            table = client.read_page_tables(page_id)
            new_data = interpret_table_contents(table)
            all_data = add_dictionary(all_data, new_data)

        all_data = dict(sorted(list(all_data.items()), key=lambda x : x[1], reverse=True))
        # print(all_data)
        time_unknown = cal_unknown(all_data, timedelta(days=days_between))
        all_data['🤔no_record'] = time_unknown
        averaged = {key:(value/days_between) for key,value in all_data.items()}
        # data to text format and save
        processed_content = [preprocess_data(key, averaged, timedelta(days=1)) for key in averaged.keys()]
        file_content = '\n'.join((generate_file_content_line(_)
                                for _ in processed_content))
        print_and_clear_unlist_words()
        
        # Add error handling for file operations
        
        try:
            write_text_file(file_content, args.start_day, args.end_day, output_path)
            if whether_update:
                if 'gist_id' not in config or 'auth_token' not in config:
                    raise KeyError("Missing required config values for gist update")
                update_gist(output_path, config['gist_id'], config['auth_token'])
        except Exception as e:
            print(f"Error writing output or updating gist: {e}")
            exit(1)
            
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        exit(1)
