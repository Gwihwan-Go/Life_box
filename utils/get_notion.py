import requests
import yaml

with open('config.yaml') as f:
    config = yaml.safe_load(f)
# Replace with your API key

NOTION_TOKEN = config['notion_secret']
DATABASE_ID = config['notion_database_id']

headers = {
    "Authorization": "Bearer " + NOTION_TOKEN,
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}

def get_block_children(block_id):
    # Set the URL for the retrieve block children endpoint
    url = f"https://api.notion.com/v1/blocks/{block_id}/children"
    
    # Make a GET request and get the response as JSON
    response = requests.get(url, headers=headers).json()
    
    # Return the list of block children
    return response["results"]

def get_pages(num_pages=1):
    """
    If num_pages is None, get all_data pages, otherwise just the defined number.
    """
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"

    get_all_data = num_pages is None
    page_size = 100 if get_all_data else num_pages

    payload = {"page_size": page_size}
    response = requests.post(url, json=payload, headers=headers)

    data = response.json()

    # Comment this out to dump all_data data to a file
    # import json
    # with open('db.json', 'w', encoding='utf8') as f:
    #    json.dump(data, f, ensure_ascii=False, indent=4)

    results = data["results"]
    # print(data)
    while data["has_more"] and get_all_data:
        payload = {"page_size": page_size, "start_cursor": data["next_cursor"]}
        url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
        response = requests.post(url, json=payload, headers=headers)
        data = response.json()
        results.extend(data["results"])

    return results

def return_date_of_my_page(page_content) :
    """
    page_content : page_content_json
    output : string(date)
    """
    return page_content['properties']['날짜']['date']['start']

def read_table_of_my_page(page_id) :
    tb_list = []
    blocks = get_block_children(page_id)
    for block in blocks:
        if block['type'] == 'table' :
            table_id = block['id']
            table = get_block_children(table_id)
            
            
            for row in range(len(table)) :
                
                cols = [table[row]['table_row']['cells'][i][0]['plain_text'] 
                        for i in range(len(table[row]['table_row']['cells']))
                        if table[row]['table_row']['cells'][i] != []]
                tb_list.append(cols)
    return tb_list

def main(num_of_pages) :

    pages = get_pages(num_of_pages)

    for page in pages:
        date = return_date_of_my_page(page)
        page_id = page["id"].replace('-', '')
        table = read_table_of_my_page(page_id)
    
    return {'date' : date, 'table' : table}

if __name__ == "__main__" : 
  print(main(3))