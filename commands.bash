# python onenote_export.py --select 'Diary' --outdir ./inputs
# python overview.py -p 30 -o Overview_month
python access_to_server.py
python overview.py 
# python overview.py -p 1 -o Overview_today

python update_gist.py 