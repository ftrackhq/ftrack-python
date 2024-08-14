#!/usr/bin/env python3

"""
Takes the output from Sphinx, clean it and send it to Docusaurus.

1. Get four main modules from _build/html/
    - Extract only the 'body' html and store it as a md file under 
            ./doc/api-{module_name}.md

2. Get all files under _build/html/api_reference/
    - Extract 'body' html and store it as a md file under
            ./website/docs/api/{filenames}.md

3. Update 'api_reference.json' with the new markdown files
    - Update the 'api_reference' section.
    - Add each module under a sub-directory.
"""


"""
Takes all relevant html files from the html output sphinx folder, parse it with Beautifulsoup, remove unnecessary html data (such as <head>) and
save a markdown file.
"""

from bs4 import BeautifulSoup
import glob
from pathlib import Path
from typing import List
import re
import json

"""
PARAMETERS
"""

MODULES = ["api_reference"]
ROOT_HTML_DIRECTORY = "./build/html/api_reference"
ROOT_MD_DIRECTORY = "./doc/api_reference/_new"
API_REFERENCE_FILEPATH = "./doc/api_reference.json"
"""
Helper functions
"""


def get_content(soup):
    return soup.find("main").find("div")


def add_docusaurus_metadata(content: str, id: str, title: str, hide_title) -> str:
    """
    Add docusaurus metadata into content.
    """
    return f"---\nid: {id}\ntitle: {title}\nhide_title: {hide_title}\n---\n\n" + content


def fix_href(soup, module: str):
    """
    Fix internal href to be compatible with docusaurus.
    """

    for a in soup.find_all("a", {"class": "reference internal"}, href=True):
        a["href"] = re.sub("^texthero\.", f"/docs/{module}/", a["href"])
        a["href"] = a["href"].lower()
    return soup


def to_md(
    in_html_filepath: str, out_md_filepath: str, id: str, title: str, hide_title: str
) -> None:
    """
    Convert Sphinx-generated html to md.

    Parameters
    ----------
    in_html_filepath : str
        input html file. Example: ./build/html/api_reference/attribute.html
    out_md_filepath : str
        output html file. Example: ./doc/api_reference/_new/attribute.md
    id : str
        Docusaurus document id
    title : str
        Docusaurus title id
    hide_title : str ("true" or "false")
        Whether to hide title in Docusaurus.
        
    """

    with open(in_html_filepath, "r") as f:
        soup = BeautifulSoup(f.read(), "html.parser")
        body = get_content(soup)

    with open(out_md_filepath, "w") as f:
        content = add_docusaurus_metadata(str(body), id, title, hide_title)
        f.write(content)


def get_prettified_module_name(module_name: str):
    """
    Return a prettified version of the module name. 
    
    Examples
    --------
    >>> get_title("preprocessing")
    Preprocessing
    >>> get_title("nlp")
    NLP
    """
    module_name = module_name.lower().strip()
    if module_name == "nlp":
        return "NLP"
    else:
        return module_name.capitalize()


"""
Update sidebars and markdown files
"""

api_reference = {}


for m in MODULES:
    in_html_filename = f"{ROOT_HTML_DIRECTORY}/{m}.html"
    out_md_filename = f"{ROOT_MD_DIRECTORY}/{m}.md"
    id = "api_reference-" + m.lower().strip()
    title = get_prettified_module_name(m)

    hide_title = "false"

    # initialize api_sidebars
    api_reference[title] = [id]

    to_md(in_html_filename, out_md_filename, id, title, hide_title)

for a in glob.glob("./build/html/api_reference/*.html"):
    object_name = a.split("/")[-1].replace(".html", "")
    print
    id = object_name
    (_, module_name, fun_name) = object_name.split(".")

    title = f"{module_name}.{fun_name}"

    module_name = get_prettified_module_name(module_name)

    hide_title = "true"

    api_reference[module_name].sort()

    api_reference[module_name] = api_reference[module_name] + ["/api_reference" + id]

    in_html_filename = f"{ROOT_HTML_DIRECTORY}/api_reference/{object_name}.html"
    out_md_filename = f"{ROOT_MD_DIRECTORY}/api_reference/{object_name}.md"

    to_md(in_html_filename, out_md_filename, id, title, hide_title)


# Load, update and save again sidebars.json
with open(API_REFERENCE_FILEPATH) as js:
    root = json.load(js)

root["api"] = api_reference

with open(API_REFERENCE_FILEPATH, "w") as f:
    json.dump(root, f, indent=2)