import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from src.notionClient import NotionClient, main
import pprint

def test_main():
    mock_page = {
        'id': 'page-id',
        'properties': {'date': {'date': {'start': '2023-01-01'}}}
    }
    mock_tables = [['cell1', 'cell2']]
    
    with patch.object(NotionClient, 'get_pages', return_value=[mock_page]), \
         patch.object(NotionClient, 'get_page_date', return_value='2023-01-01'), \
         patch.object(NotionClient, 'read_page_tables', return_value=mock_tables):
        
        result = main(num_pages=1)
        
        assert result['date'] == '2023-01-01'
        assert result['table'] == mock_tables

def test_actual_notion_client():
    """Test actual Notion API integration"""
    client = NotionClient()
    start_day = '2023-03-01'
    end_day = '2023-03-03'
    
    # Test querying date range
    page_ids = client.query_database_by_date_range(start_day, end_day)
    assert isinstance(page_ids, list), "Expected list of page IDs"
    
    if page_ids:
        # Test getting page date
        page_date = client.get_page_date(page_ids[0])
        assert isinstance(page_date, str), "Expected date string"
        assert datetime.strptime(page_date, '%Y-%m-%d'), "Expected valid date format YYYY-MM-DD"
    
    # Test main function
    result = main()
    pytest.skip(f"Debug output - result:\n{pprint.pformat(result, indent=2, width=150)}")

    assert isinstance(result, dict), "Expected dictionary result"
    assert 'date' in result, "Expected 'date' in result"
    assert 'table' in result, "Expected 'table' in result" 