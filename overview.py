from utils import *
from collections import defaultdict
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-d", "--day", type=str, 
    help="It will get the data until a day before the day, 7/27 for 7/20-7/26",
    action="store", 
    default=f"{datetime.now().month}/{datetime.now().day}")       
parser.add_argument("-p", "--period", 
    type=int,help="how long do you want to know?", 
    default=7)           
args = parser.parse_args()

output_path = "./results/Overview my life"
file_path = "./inputs/Diary"
data = defaultdict(None)

end_day = datetime.strptime(args.day,"%m/%d") - timedelta(days=1)
std_time = timedelta(days=args.period)
start_day = end_day - std_time + timedelta(days=1)
_start_day=start_day
while start_day <= end_day :
    notebook_path = search_by_date(2022,start_day.month,start_day.day,file_path)
    if notebook_path is not None :
        notebook_path += '/main.html'
        data = cal_hours(get_schedule(notebook_path), data) #add new data to data
    
    print("#######################")
    print(f"suceessfully recieved {start_day.month}/{start_day.day} data")
    processed_content = [preprocess_data(key, data, std_time) for key in data.keys()]
    file_content = '\n'.join((generate_file_content_line(_)
                        for _ in processed_content))
    print(file_content)
    print("#######################")

    start_day+=timedelta(days=1)

data['🤔no_record']=cal_unknown(data, std_time)
sorted_data = dict(sorted(list(data.items()), key=lambda x : x[1], reverse=True))
averaged = {key:(value/args.period) for key,value in sorted_data.items()}
processed_content = [preprocess_data(key, averaged, std_time/args.period) for key in averaged.keys()]
file_content = '\n'.join((generate_file_content_line(_)
                        for _ in processed_content))

with open(output_path, 'w') as f :
    f.write(f"My life Overview in period of {_start_day.month}/{_start_day.day} ~ {end_day.month}/{end_day.day} [averaged]\n")
    f.writelines(file_content)
f.close()
print(f"{_start_day.month}/{_start_day.day} ~ {end_day.month}/{end_day.day} records has successfully saved at {output_path}")