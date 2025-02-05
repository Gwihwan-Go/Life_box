from typing import List, Dict, Optional, Any
import requests
import yaml
import os
from datetime import datetime

class NotionClient:
    """A client for interacting with the Notion API."""
    
    API_BASE_URL = "https://api.notion.com/v1"
    API_VERSION = "2022-06-28"
    
    def __init__(self):
        self.config = self._load_config()
        self.headers = {
            "Authorization": f"Bearer {self.config['notion_secret']}",
            "Content-Type": "application/json",
            "Notion-Version": self.API_VERSION,
        }
        self.database_id = self.config['notion_database_id']

    def _load_config(self) -> Dict[str, str]:
        """Load configuration from environment variables or config file."""
        try:
            if os.environ.get('GITHUB_ACTIONS'):
                return dict(os.environ)
            
            with open('config.yaml') as f:
                return yaml.safe_load(f)
        except Exception as e:
            raise RuntimeError(f"Failed to load configuration: {str(e)}")

    def get_block_children(self, block_id: str) -> List[Dict[str, Any]]:
        """Retrieve children blocks of a given block ID."""
        url = f"{self.API_BASE_URL}/blocks/{block_id}/children"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()["results"]

    def query_database_by_date_range(self, start_day: str, end_day: str) -> List[str]:
        """Query database for pages within a date range."""
        url = f"{self.API_BASE_URL}/databases/{self.database_id}/query"
        query = {
            "filter": {
                "and": [
                    {"property": "date", "date": {"on_or_after": start_day}},
                    {"property": "date", "date": {"on_or_before": end_day}}
                ]
            }
        }
        
        response = requests.post(url, headers=self.headers, json=query)
        response.raise_for_status()
        return [page['id'] for page in response.json()["results"]]

    def get_page(self, page_id: str) -> Dict[str, Any]:
        """Retrieve a page by its ID."""
        url = f"{self.API_BASE_URL}/pages/{page_id}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def get_page_date(self, page_id: str) -> str:
        """Get the date property of a page."""
        page = self.get_page(page_id)
        return page['properties']['date']['date']['start']

    def get_pages(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retrieve pages from the database with optional limit."""
        url = f"{self.API_BASE_URL}/databases/{self.database_id}/query"
        page_size = 100 if limit is None else limit
        
        results = []
        has_more = True
        next_cursor = None

        while has_more and (limit is None or len(results) < limit):
            payload = {"page_size": page_size}
            if next_cursor:
                payload["start_cursor"] = next_cursor

            response = requests.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            
            results.extend(data["results"])
            has_more = data["has_more"]
            next_cursor = data.get("next_cursor")

        return results[:limit] if limit else results

    def read_page_tables(self, page_id: str) -> List[List[str]]:
        """Read all tables from a page."""
        blocks = self.get_block_children(page_id)
        date = self.get_page_date(page_id)
        print(f"Processing the page of {date} date...")
        
        tables = []
        for block in blocks:
            if block['type'] == 'table':
                table_rows = self.get_block_children(block['id'])
                for row in table_rows:
                    cells = row['table_row']['cells']
                    cols = [
                        cell[0]['plain_text']
                        for cell in cells
                        if cell
                    ]
                    tables.append(cols)
        return tables

def main(num_pages: Optional[int] = None) -> Dict[str, Any]:
    """Main function to retrieve page data."""
    client = NotionClient()
    pages = client.get_pages(num_pages)
    
    if not pages:
        return {'date': None, 'table': []}
    
    page = pages[0]
    page_id = page["id"].replace('-', '')
    date = client.get_page_date(page_id)
    table = client.read_page_tables(page_id)
    
    return {'date': date, 'table': table}
