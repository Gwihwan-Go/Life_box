import argparse
from datetime import timedelta, datetime
from utils.html_parser import *
from utils.utils import *
from utils.get_onenote import get_onenote
import yaml

if __name__ == "__main__" :

    try :
        if os.environ['GITHUB_ACTIONS'] :
            config = os.environ
            print( "Running in GitHub Actions" )
            whether_update = True
    except :
        with open('config.yaml') as f:
            config = yaml.safe_load(f)
            print( "Running in local" )
            whether_update = False

    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--end_day", type=str, 
        help="It will get the data until a day before the day, 7/27 for 7/20-7/26",
        action="store", 
        default=f"{(datetime.now() - timedelta(days = 1)).month}/{(datetime.now() - timedelta(days = 1)).day}") #default is yesterday 
    parser.add_argument("-p", "--period", 
        type=int,help="how long do you want to know?", 
        default=7)        
    parser.add_argument("-o", "--out", 
        type=str,help="output directory to store the result", 
        default="overview")      
    args = parser.parse_args()

    output_path = args.out
    target_notebook_names = ['Diary']
    
    # collect onenote data based on args
    period = calculate_start_end_day(args.end_day, args.period)
    onenote_result = get_onenote(config, period, target_notebook_names=target_notebook_names)
    # parse data from onenote script
    time_data = contents_to_organized_dict(onenote_result, target_notebook_names)
    time_data['🤔no_record']=cal_unknown(time_data, timedelta(days=args.period))
    averaged = {key:(value/args.period) for key,value in time_data.items()}
    # data to text format and save
    processed_content = [preprocess_data(key, averaged, timedelta(days=1)) for key in averaged.keys()]
    file_content = '\n'.join((generate_file_content_line(_)
                            for _ in processed_content))

    write_text_file(file_content, period, output_path)

    if whether_update: # only update when running in GitHub Actions
        update_gist(output_path, config['gist_id'], config['auth_token'])