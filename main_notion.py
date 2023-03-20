import argparse
from datetime import timedelta, datetime
from utils.html_parser import *
from utils.utils import *
from utils.get_onenote import get_onenote
import yaml
import nltk
from utils.get_notion import *
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
    parser.add_argument("-d", "--end_day", type=str, 
        help="It will get the data until a day before the day, 7/27 for 7/20-7/26",
        action="store", 
        default=f"{(datetime.now() - timedelta(days = 1)).year}/{(datetime.now() - timedelta(days = 1)).month}/{(datetime.now() - timedelta(days = 1)).day}") #default is yesterday 
    parser.add_argument("-p", "--period", 
        type=int,help="how long do you want to know?", 
        default=7)        
    parser.add_argument("-o", "--out", 
        type=str,help="output directory to store the result", 
        default="overview")      
    args = parser.parse_args()

    output_path = args.out
    pages = get_pages(args.period)
    period = calculate_start_end_day(args.end_day, args.period)
    all_data = {}
    for page in pages[2:]:
        date = return_date_of_my_page(page)
        page_id = page["id"].replace('-', '')
        table = read_table_of_my_page(page_id)
        # interpret_table(table)
        all_data = add_dictionary(all_data, interpret_table_contents(table))
        # print_and_clear_unlist_words()
    all_data = dict(sorted(list(all_data.items()), key=lambda x : x[1], reverse=True))
    all_data['🤔no_record']=cal_unknown(all_data, timedelta(days=args.period))
    averaged = {key:(value/args.period) for key,value in all_data.items()}
    # data to text format and save
    processed_content = [preprocess_data(key, averaged, timedelta(days=1)) for key in averaged.keys()]
    file_content = '\n'.join((generate_file_content_line(_)
                            for _ in processed_content))

    write_text_file(file_content, period, output_path)

    if whether_update: # only update when running in GitHub Actions
        update_gist(output_path, config['gist_id'], config['auth_token'])