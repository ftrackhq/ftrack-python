import os
import re
from bs4 import BeautifulSoup
from pathlib import Path


ROOT_DIR = "./build/html/api_reference"
OUT_DIR = "./build/md_output/"

for dirpath, dirnames, filenames in os.walk(ROOT_DIR): 
    for dirname in dirnames:
        dir_path = os.path.join(dirpath, dirname)
        new = dir_path.replace(ROOT_DIR, OUT_DIR)
        Path(new).mkdir(parents=True, exist_ok=True)

    
def postprocess(text):
    """
    Fixes double-escaped curly braces by converting '\\{' to '\{' and '\\}' to '\}'.

    :param text: The input string where double-escaped curly braces should be fixed.
    :return: A new string with double-escaped curly braces corrected.
    """
    # Escape '{' if it is not preceded by a backslash
    text = re.sub(r'(?<!\\){', r'\{', text)
    # Escape '}' if it is not preceded by a backslash
    text = re.sub(r'(?<!\\)}', r'\}', text)
    # Pattern to match double-escaped '{' (i.e., '\\{') and convert to single-escaped '\{'
    text = re.sub(r'\\{2}(\{)', r'\\\1', text)
    # Pattern to match double-escaped '}' (i.e., '\\}') and convert to single-escaped '\}'
    text = re.sub(r'\\{2}(\})', r'\\\1', text)

    return text

def add_docusaurus_metadata(content: str, id: str, title: str, hide_title) -> str:
    """
    Add docusaurus metadata into content.
    """
    return f"---\nid: {id}\ntitle: {title}\nhide_title: {hide_title}\n---\n\n" + content

def format_tag(tag):
    # Format block-level elements
    if tag.string and not tag.is_self_closing:
        # Wrap the text in the tag with newlines and indentation
        tag.insert(0, '\n  ')
        tag.append('\n')
    for child in tag.children:
        if isinstance(child, str):
            continue
        format_tag(child)

def get_content(soup, id):
    soup = soup.find("body").find("section", id=id)
    # format_tag(soup)

    return soup.prettify()

def process_files(dir):
    print(dir)
    for dirpath, _, filenames in os.walk(dir):
        
        for filename in filenames:
            
            file_path = os.path.join(dirpath, filename)
            if os.path.isdir(file_path):
                continue
             
            relative_path = re.sub(f'^{re.escape(ROOT_DIR)}/?', '', file_path)
            name = relative_path.split('.')[0]
            with open(file_path, 'r') as f:
                soup = BeautifulSoup(f.read(), "html.parser")
                id_ref = "module-ftrack_api." + name.replace('/index', '').replace("/", ".").replace('index', '')
                if id_ref[-1] == '.':
                    id_ref = id_ref[:-1]
                print(id_ref)
                body = get_content(soup, id_ref)
            
            output_file_path = OUT_DIR + name + ".md"
            
            with open(output_file_path, 'w+') as f:
                content = add_docusaurus_metadata(postprocess(str(body)), name.split("/")[-1], name.split("/")[-1], False)
                f.write(content)

process_files(ROOT_DIR)
