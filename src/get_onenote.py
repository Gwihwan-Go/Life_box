import msal
from requests_oauthlib import OAuth2Session
import yaml
import random
import re
import string
import time
from fnmatch import fnmatch
from html.parser import HTMLParser
from xml.etree import ElementTree
from pathvalidate import sanitize_filename
SCOPES = ["Notes.Read","Notes.Read.All"]
def get_json(graph_client, url, params=None, indent=0):
    values = []
    next_page = url
    while next_page:
        resp = get(graph_client, next_page, params=params, indent=indent).json()
        if 'value' not in resp:
            raise RuntimeError(f'Invalid server response: {resp}')
        values += resp['value']
        next_page = resp.get('@odata.nextLink')
    return values


def get(graph_client, url, params=None, indent=0):
    while True:
        resp = graph_client.get(url, params=params)
        if resp.status_code == 429:
            # We are being throttled due to too many requests.
            # See https://docs.microsoft.com/en-us/graph/throttling
            indent_print(indent, 'Too many requests, waiting 20s and trying again.')
            time.sleep(20)
        elif resp.status_code == 500:
            # In my case, one specific note page consistently gave this status
            # code when trying to get the content. The error was "19999:
            # Something failed, the API cannot share any more information
            # at the time of the request."
            indent_print(indent, 'Error 500, skipping this page.')
            return None
        elif resp.status_code == 504:
            indent_print(indent, 'Request timed out, probably due to a large attachment. Skipping.')
            return None
        else:
            resp.raise_for_status()
            return resp

def get_notebooks(graph_client, select=None, indent=0):
    pass

def sort_by_name(items):
    target_pages = [item for item in items if skip_page(item["title"])==False]
    non_target_pages = [item for item in items if skip_page(item["title"])]
    target_pages = sorted(target_pages, key=lambda k: int(k['title'].split()[0]))
    return non_target_pages + target_pages

def pop_latest_pages(graph_client, sections, select, period_range):

    count = 0
    ndata=0
    result={}
    #Iterate over the reversed sections 
    end_day = period_range[-1]
    start_day = period_range[0]
    while count < end_day and len(sections) > 0:
        section = sections.pop()
        indent_print(1, section["displayName"])
        result[section["displayName"]] = {} # Create a dictionary for the section
        pages = get_json(graph_client, section['pagesUrl'])
        pages, select = filter_items(pages, select, 'pages', 2)

        indent_print(2,f"you got {len(pages)} pages")

        pages = sort_by_name(pages)
        # pages = sorted(pages, key=lambda k: k['lastModifiedDateTime'])
        #pages = sorted(pages, key=lambda k: k['createdDateTime'])

        # Iterate over the reversed pages
        while count < end_day and len(pages) > 0:
            ## sort pages by its name, reversed
            page = pages.pop() 

            if skip_page(page["title"]) : # not the Diary page
                indent_print(3, f"skipping {page['title']}")
                continue
            if count < start_day : # not in the period range
                indent_print(3, f"not in the period range {page['title']}")
                count+=1
                continue

            result[section["displayName"]][page["title"]]  = get_page(graph_client, page, 3)
            count+=1
            ndata+=1

    print(f"Collected over {ndata} pages")
    return result

def get_page(graph_client, page, select=None, indent=0):
    indent_print(indent, f"Collecting {page['title']}")
    response = get(graph_client, page['contentUrl'], indent=indent)
    return response.text

def get_section(graph_client, section, select=None, indent=1):

    result = {}
    indent_print(1, section["displayName"])
    result[section["displayName"]] = {} # Create a dictionary for the section
    pages = get_json(graph_client, section['pagesUrl'])
    pages, select = filter_items(pages, select, 'pages', 2)

    for page in pages[::-1] :
        indent_print(2,f"you got {len(pages)} pages")
        if skip_page(page["title"]) :
            indent_print(3, f"skipping {page['title']}")
        result[section["displayName"]][page["title"]]=get_page(graph_client, page, select, indent=2)
    
    return result



def download_attachments(graph_client, content, out_dir, indent=0):
    image_dir = out_dir / 'images'
    attachment_dir = out_dir / 'attachments'

    class MyHTMLParser(HTMLParser):
        def handle_starttag(self, tag, attrs):
            self.attrs = {k: v for k, v in attrs}

    def generate_html(tag, props):
        element = ElementTree.Element(tag, attrib=props)
        return ElementTree.tostring(element, encoding='unicode')

    def download_image(tag_match):
        # <img width="843" height="218.5" src="..." data-src-type="image/png" data-fullres-src="..."
        # data-fullres-src-type="image/png" />
        parser = MyHTMLParser()
        parser.feed(tag_match[0])
        props = parser.attrs
        image_url = props.get('data-fullres-src', props['src'])
        image_type = props.get('data-fullres-src-type', props['data-src-type']).split("/")[-1]
        file_name = ''.join(random.choice(string.ascii_lowercase) for _ in range(10)) + '.' + image_type
        req = get(graph_client, image_url, indent=indent)
        if req is None:
            return tag_match[0]
        img = req.content
        indent_print(indent, f'Downloaded image of {len(img)} bytes.')
        image_dir.mkdir(exist_ok=True)
        with open(image_dir / file_name, "wb") as f:
            f.write(img)
        props['src'] = "images/" + file_name
        props = {k: v for k, v in props.items() if 'data-fullres-src' not in k}
        return generate_html('img', props)

    def download_attachment(tag_match):
        # <object data-attachment="Trig_Cheat_Sheet.pdf" type="application/pdf" data="..."
        # style="position:absolute;left:528px;top:139px" />
        parser = MyHTMLParser()
        parser.feed(tag_match[0])
        props = parser.attrs
        data_url = props['data']
        file_name = props['data-attachment']
        if (attachment_dir / file_name).exists():
            indent_print(indent, f'Attachment {file_name} already downloaded; skipping.')
        else:
            req = get(graph_client, data_url, indent=indent)
            if req is None:
                return tag_match[0]
            data = req.content
            indent_print(indent, f'Downloaded attachment {file_name} of {len(data)} bytes.')
            attachment_dir.mkdir(exist_ok=True)
            with open(attachment_dir / file_name, "wb") as f:
                f.write(data)
        props['data'] = "attachments/" + file_name
        return generate_html('object', props)

    content = re.sub(r"<img .*?\/>", download_image, content, flags=re.DOTALL)
    content = re.sub(r"<object .*?\/>", download_attachment, content, flags=re.DOTALL)
    return content


def indent_print(depth, text):
    print('  ' * depth + text)


def filter_items(items, select, name='items', indent=0):
    if not select:
        return items, select
    items = [item for item in items
             if fnmatch(item.get('displayName', item.get('title')).lower(), select[0].lower())]
    if not items:
        indent_print(indent, f'No {name} found matching {select[0]}')
    return items, select[1:]


def download_notebooks(graph_client, path, select=None, indent=0):
    notebooks = get_json(graph_client, f'{graph_url}/me/onenote/notebooks')
    indent_print(0, f'Got {len(notebooks)} notebooks.')
    notebooks, select = filter_items(notebooks, select, 'notebooks', indent)
    for notebook in notebooks:
        notebook_name = notebook["displayName"]
        indent_print(indent, f'Opening notebook {notebook_name}')
        sections = get_json(graph_client, notebook['sectionsUrl'])
        section_groups = get_json(graph_client, notebook['sectionGroupsUrl'])
        indent_print(indent + 1, f'Got {len(sections)} sections and {len(section_groups)} section groups.')
        download_sections(graph_client, sections, path / notebook_name, select, indent=indent + 1)
        download_section_groups(graph_client, section_groups, path / notebook_name, select, indent=indent + 1)


def download_section_groups(graph_client, section_groups, path, select=None, indent=0):
    section_groups, select = filter_items(section_groups, select, 'section groups', indent)
    for sg in section_groups:
        sg_name = sg["displayName"]
        indent_print(indent, f'Opening section group {sg_name}')
        sections = get_json(graph_client, sg['sectionsUrl'])
        indent_print(indent + 1, f'Got {len(sections)} sections.')
        download_sections(graph_client, sections, path / sg_name, select, indent=indent + 1)


def download_sections(graph_client, sections, path, select=None, indent=0):
    sections, select = filter_items(sections, select, 'sections', indent)
    for sec in sections:
        sec_name = sec["displayName"]
        indent_print(indent, f'Opening section {sec_name}')
        pages = get_json(graph_client, sec['pagesUrl'] + '?pagelevel=true')
        indent_print(indent + 1, f'Got {len(pages)} pages.')
        download_pages(graph_client, pages, path / sec_name, select, indent=indent + 1)


def download_pages(graph_client, pages, path, select=None, indent=0):
    pages, select = filter_items(pages, select, 'pages', indent)
    pages = sorted([(page['order'], page) for page in pages])
    level_dirs = [None] * 4
    for order, page in pages:
        level = page['level']
        page_title = sanitize_filename(f'{page["title"]}', platform='auto') #deleted {order}
        indent_print(indent, f'Opening page {page_title}')
        if level == 0:
            page_dir = path / page_title
        else:
            page_dir = level_dirs[level - 1] / page_title
        level_dirs[level] = page_dir
        download_page(graph_client, page['contentUrl'], page_dir, indent=indent + 1)


def download_page(graph_client, page_url, path, indent=0):
    out_html = path / 'main.html'
    if out_html.exists():
        indent_print(indent, 'HTML file already exists; skipping this page')
        return
    path.mkdir(parents=True, exist_ok=True)
    response = get(graph_client, page_url, indent=indent)
    if response is not None:
        content = response.text
        indent_print(indent, f'Got content of length {len(content)}')
        content = download_attachments(graph_client, content, path, indent=indent)
        with open(out_html, "w", encoding='utf-8') as f:
            f.write(content)

def skip_page(page_name) :
    import re
    if re.match(r'^\d', page_name) :
        return False 
    else :
        return True

def check_access_result(access_result, print_token=False) :
    """
    show acess_result 
    input :
        access_result(acquire_token_object)
        print_token(bool) : whether to print token
    output :
        None
    
    """
    if "access_token" in access_result:
        print("successfully got access token ::: ", end='')
        if print_token :
            print(access_result["access_token"])
    else:
        print(access_result.get("error"))
        print(access_result.get("error_description"))
        print(access_result.get("correlation_id")) 

def generate_access_token_by_refresh_token(refresh_token, client_id, scopes) :
    """
    acquire token
    input :
        infos in config file
    output :
        access_result(acquire_token_object)
    """
    pass
    # import requests
    # acquire_token_by_refresh_token_url = f'{authority_url}/oauth2/v2.0/token'
    # data = {
    #     'client_id': client_id,
    #     'scope': ' '.join(scopes),
    #     'refresh_token': refresh_token,
    #     'grant_type': 'refresh_token'
    # }
    # response = requests.post(acquire_token_by_refresh_token_url, data=data)
    # return response.json()

def generate_access_token_with_username_pwd(config):
    """
    For complete automization, this is not recommended
    The grant type is not supported over the /common or 
    /consumers endpoints. Please use the /organizations or tenant-specific endpoint.
    acquire token
    input :
        config(dict) : dictionary of config.yaml
        it could be replaced with os.environ in github actions
        
    output :
        access_result(acquire_token_object)
    
    """
    client = msal.ConfidentialClientApplication(client_id=config['client_id'], 
                                                authority=f'https://login.microsoftonline.com/{config["tenant_id"]}',
                                                client_credential=config['secret'])
    access_result = client.acquire_token_by_username_password(username=config['username'], password=config['password'], scopes=SCOPES)
    check_access_result(access_result)
    return access_result

def generate_access_token_by_flow_code(config):

    """
    Recommended
    input :
        config(dict) : dictionary of config.yaml
        it could be replaced with os.environ in github actions
        
    output :
        access_result(acquire_token_object)
    """
    access_token_cache = msal.SerializableTokenCache()
    #if config.yaml file has 'api_token'
    try :
        access_token_cache.deserialize(config['tempToken'])
    except :
        pass

    client = msal.PublicClientApplication(client_id=config['client_id'], 
                                            token_cache=access_token_cache)
    accounts = client.get_accounts()

    if accounts:
        access_result = client.acquire_token_silent(SCOPES, 
                                                    account=accounts[0])
        print("successfully got access token from saved ::: ",)

    else:
        flow = client.initiate_device_flow(scopes=SCOPES) # Initiate the device flow`
        print(flow['message']) # Print the message from the response`

        access_result = client.acquire_token_by_device_flow(flow) # Acquire the token by device flow
        
        ## SAVE TOKEN ::: edit tempToken of config.yaml file 
        config['tempToken'] = access_token_cache.serialize()
        with open('config.yaml', 'w') as f:
            yaml.dump(config, f)
        
        check_access_result(access_result)


    return access_result

def get_onenote(config, period_range, target_notebook_names=['Diary']) :
    """
    This is the main function that will be called when the script is run.
    Collect oneNote Diaries 
        input :
            config(dict) : dictionary of config.yaml
                            it could be replaced with 'os.environ' in github actions
            target_days(int) : how much diary pages to pull
            target_notebook_names(arr) : notebook_names in list
        output :
            onenote_result(dict) : collected data
            structure : 
                onenote_result[notebook_name][section_name][page_title] = page_content
                ex) onenote_result['Diary']['2022.10'][11 2:00-7:00] = 'blahblah'
    """

    onenote_result = {}
    base_url = 'https://graph.microsoft.com/v1.0/' # Microsoft Graph API endpoint
    endpoint = base_url + 'me/onenote/notebooks' #/sections/pages 
    
    #generate_access_token_by_flow_code
    access_result = generate_access_token_with_username_pwd(config) 
    # access_result = generate_access_token_by_flow_code(config)

    # if there is no target_days ? then all the pages in selected notebook will be looked at
    graph_client = OAuth2Session(token=access_result)

    notebooks = get_json(graph_client, endpoint)
    notebooks, select = filter_items(notebooks, target_notebook_names, 'notebooks', 0)

    for nb in notebooks :
        indent_print(0, nb["displayName"]) # Print the name of the notebook
        onenote_result[nb["displayName"]] = {} # Create a dictionary for the notebook
        sections = get_json(graph_client, nb['sectionsUrl']) # Get the sections of the notebook
        sections, select = filter_items(sections, select, 'sections', 1) # Filter the sections

        # Pop the latest pages from the sections
        onenote_result[nb["displayName"]] = pop_latest_pages(graph_client, sections, select, period_range) 
    
    return onenote_result


if __name__ == "__main__":

    start_day = 1 # 1day ago
    end_day = 7 # 7days ago
    period_range = [i for i in range(start_day,end_day+1)] # a 며칠 전부터 며칠 전까지, 1:7 -> 1일 전부터 7일 전까지

    target_notebook_names = ['Diary']
    with open('config.yaml') as f:
        config = yaml.safe_load(f)
    
    get_onenote(config, period_range, target_notebook_names=target_notebook_names)