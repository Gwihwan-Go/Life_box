# python onenote_export.py --select 'Diary' --outdir ./inputs

python access_to_server.py

python main.py -p 30 -o main_month
python main.py 
python main.py -p 1 -o overview_today

python update_gist.py 