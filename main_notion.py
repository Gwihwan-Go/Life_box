import argparse
from datetime import timedelta, date
from src.interpretNotionPage import interpret_table_contents
from src.utils import (
    add_dictionary, get_env, cal_unknown, preprocess_data, 
    generate_file_content_line, write_text_file, update_gist
)
from src.notionClient import NotionClient
from src.report import report_study_and_revise_db
import yaml
import os

def load_config():
    """Load configuration from environment variables or config file."""
    try:
        if os.environ.get('GITHUB_ACTIONS'):
            return dict(os.environ)
        
        with open('config.yaml') as f:
            return yaml.safe_load(f)
    except Exception as e:
        raise RuntimeError(f"Failed to load configuration: {str(e)}")

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("-e", "--end_day", type=str, 
        help="End date in ISO format (e.g., 2024-07-27)",
        default=(date.today() - timedelta(days=1)).isoformat()
    )
    parser.add_argument("-s", "--start_day", type=str, 
        help="Start date in ISO format (e.g., 2024-07-20)",
        default=(date.today() - timedelta(days=7)).isoformat()
    )       
    parser.add_argument("-o", "--out", 
        type=str,
        help="Output directory to store the result", 
        default="overview"
    )      
    parser.add_argument("--report_study_and_revise_db",
        action="store_true",
        help="Generate study time summary and revise the database",
        default=False
    )
    return parser.parse_args()

def validate_dates(start_day: str, end_day: str) -> int:
    """Validate date formats and return days between."""
    try:
        start_date = date.fromisoformat(start_day)
        end_date = date.fromisoformat(end_day)
        return (end_date - start_date).days + 1
    except ValueError as e:
        raise ValueError(f"Error parsing dates: {e}")

def process_pages(client: NotionClient, page_ids: list) -> tuple[dict, int]:
    """Process pages and return aggregated data."""
    all_data = {}
    empty_count = 0
    
    for page_id in page_ids:
        page_id = page_id.replace('-', '')
        table = client.read_page_tables(page_id)
        # print(f'Table content for {page_id}:', table)  # Debug table content
        
        new_data = interpret_table_contents(table)
        # print(f'Interpreted data for {page_id}:', new_data)  # Debug interpreted data
        
        if not new_data or len(new_data.keys()) == 0:  # Check if defaultdict has no keys
            empty_count += 1
            print(f'Empty page: {page_id} (table length: {len(table) if table else 0})')
            continue
            
        all_data = add_dictionary(all_data, new_data)
        
    return dict(sorted(list(all_data.items()), key=lambda x: x[1], reverse=True)), empty_count

def generate_report(all_data: dict, days_between: int) -> str:
    #TODO: add notion template and invite guest to deploy the workflow
    """Generate report content from data."""
    time_unknown = cal_unknown(all_data, timedelta(days=days_between))
    all_data['🤔no_record'] = time_unknown
    averaged = {key: (value/days_between) for key, value in all_data.items()}
    processed_content = [preprocess_data(key, averaged, timedelta(days=1)) 
                        for key in averaged.keys()]
    return '\n'.join(generate_file_content_line(_) for _ in processed_content)

def main():
    try:
        args = parse_arguments()
        config = load_config()
        whether_update = get_env()
        client = NotionClient()
        
        if args.report_study_and_revise_db:
            report_study_and_revise_db(client)
            # return
            
        days_between = validate_dates(args.start_day, args.end_day)
        page_ids = client.query_database_by_date_range(args.start_day, args.end_day)
        
        print(f'Processing {days_between} days...')
        print(f'Processing {len(page_ids)} pages...')
        
        all_data, empty_count = process_pages(client, page_ids)
        days_between -= empty_count
        file_content = generate_report(all_data, days_between)
        try:
            write_text_file(file_content, args.start_day, args.end_day, args.out)
            if whether_update:
                if 'gist_id' not in config or 'auth_token' not in config:
                    raise KeyError("Missing required config values for gist update")
                update_gist(args.out, config['gist_id'], config['auth_token'])
        except Exception as e:
            print(f"Error writing output or updating gist: {e}")
            raise
            
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        exit(1)

if __name__ == "__main__":
    main()
