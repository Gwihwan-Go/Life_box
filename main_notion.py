import argparse
from datetime import timedelta,  date
from utils.html_parser import *
from utils.utils import *
from utils.get_onenote import get_onenote
import yaml
import nltk
from utils.get_notion import *
from pprint import pprint

nltk.download('all')

if __name__ == "__main__" :

    try :
        if os.environ['GITHUB_ACTIONS'] :
            config = os.environ
    except :
        with open('config.yaml') as f:
            config = yaml.safe_load(f)
            
    whether_update = get_env()
    parser = argparse.ArgumentParser()

    parser.add_argument("-e", "--end_day", type=str, 
        help="It will get the data until a day before the day, 7/27 for 7/20-7/26",
        action="store", 
        default=(date.today() - timedelta(days=1)).isoformat() #default is yesterday 
    )
    parser.add_argument("-s", "--start_day", type=str, 
        help="It will get the data until a day before the day, 7/27 for 7/20-7/26",
        action="store", 
        default=(date.today() - timedelta(days=7)).isoformat() #default is one week before of yesterday
    )       
    parser.add_argument("-o", "--out", 
        type=str,help="output directory to store the result", 
        default="overview")      
    args = parser.parse_args()

    output_path = args.out
    page_ids = query_database_by_range(args.start_day, args.end_day)
    days_between = (date.fromisoformat(args.end_day) - date.fromisoformat(args.start_day)).days + 1
    print(f'Processing {days_between} days...')
    print(f'Processing {len(page_ids)} pages...')
    all_data = {}
    for page_id in page_ids:
        #get properties from page_id
        # date = get_date_from_page_id(page_id)
        # print(f'Processing {date}...')
        page_id = page_id.replace('-', '')
        table = read_table_of_my_page(page_id)
        new_data = interpret_table_contents(table)
        all_data = add_dictionary(all_data, new_data)

    all_data = dict(sorted(list(all_data.items()), key=lambda x : x[1], reverse=True))
    # print(all_data)
    all_data['🤔no_record']=cal_unknown(all_data, timedelta(days=days_between))
    averaged = {key:(value/days_between) for key,value in all_data.items()}
    # data to text format and save
    processed_content = [preprocess_data(key, averaged, timedelta(days=1)) for key in averaged.keys()]
    file_content = '\n'.join((generate_file_content_line(_)
                            for _ in processed_content))

    write_text_file(file_content, args.start_day, args.end_day, output_path)

    if whether_update: # only update when running in GitHub Actions
        update_gist(output_path, config['gist_id'], config['auth_token'])