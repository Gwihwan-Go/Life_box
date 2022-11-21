import random
import re
import string
import time
from fnmatch import fnmatch
from html.parser import HTMLParser
from xml.etree import ElementTree
from pathvalidate import sanitize_filename

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