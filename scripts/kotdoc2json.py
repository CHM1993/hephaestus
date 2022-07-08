import argparse
import json
import os
import re
import sys

from bs4 import BeautifulSoup
from pathlib import Path


REGULAR_CLASS = 0
INTERFACE = 1
ABSTRACT_CLASS = 2
ENUM = 3


def _get_super_classes_interfaces(html_doc):
    regex = re.compile(r'(?:[^,(]|<[^)]*>)+')
    element = html_doc.select(".cover .platform-hinted .symbol")[0]
    # remove these elements
    rem_elems = element.find_all("span", {"class": "top-right-position"}) + \
        element.find_all("div", {"class": "copy-popup-wrapper"})
    for e in rem_elems:
        e.decompose()
    segs = element.text.split(": ")
    if len(segs) == 1:
        # No super classes / interfaces.
        return []
    text = element.text.split(": ")[1].replace(" , ", ",")
    return re.findall(regex, text)


def extract_package_name(html_doc):
    return html_doc.select(".breadcrumbs a")[-2].text


def extract_class_name(html_doc):
    return html_doc.select(".cover a")[0].text


def extract_class_type_parameters(html_doc):
    typ_param = html_doc.select(".cover a")[1].text
    return typ_param


def extract_super_class(html_doc):
    classes = _get_super_classes_interfaces(html_doc)
    if not classes:
        return None
    # In general, we cannot distinguish between interfaces and classes.
    return classes[0]


def extract_class_type(html_doc):
    cl_type = html_doc.select(".cover span")[3].text
    if 'interface' in cl_type:
        return INTERFACE
    if 'abstract class' in cl_type:
        return ABSTRACT_CLASS
    if 'enum' in cl_type:
        return None
    return REGULAR_CLASS


def extract_super_interfaces(html_doc):
    classes = _get_super_classes_interfaces(html_doc)
    return classes


def extract_method_return_type(method_doc, is_constructor):
    if is_constructor:
        return [], None
    elem = method_doc.find("span", {"class": "token function"})
    elem.decompose()
    ret_type = method_doc.select("a")[-1].text
    if not ret_type:
        return [], "Unit"

    return [], ret_type


def extract_method_parameter_types(method_doc, is_constructor):
    types = []
    for param in method_doc.select(".parameter"):
        types.append(param.select("a")[-1].text)
    return types


def extract_method_name(method_doc, is_constructor):
    try:
        return method_doc.find(class_="function").text
    except IndexError:
        # We are probably in a field
        return None


def process_javadoc(html_doc):
    class_name = extract_class_name(html_doc)
    package_name = extract_package_name(html_doc)
    full_class_name = "{pkg}.{cls}".format(pkg=package_name,
                                           cls=class_name)
    super_class = extract_super_class(html_doc)
    super_interfaces = extract_super_interfaces(html_doc)
    class_type = extract_class_type(html_doc)
    api = {
      'name': full_class_name,
      'methods': [],  # We populate this field below
      'type_parameters': extract_class_type_parameters(html_doc),
      'implements': super_interfaces,
      'inherits': super_class,
      "class_type": class_type,
      'fields': False,
    }
    methods = html_doc.select(
        "div[data-togglable=\"Functions\"] .title .symbol")
    for method_doc in methods:
        is_con = False
        method_name = extract_method_name(method_doc, is_con)
        type_params, ret_type = extract_method_return_type(method_doc,
                                                           is_con)
        param_types = extract_method_parameter_types(method_doc, is_con)
        if param_types is None:
            continue
        method_obj = {
            "name": method_name,
            "parameters": param_types,
            "type_parameters": type_params,
            "return_type": ret_type,
            "is_static": False,
            "is_constructor": is_con,
            "access_mod": "public"
        }
        api["methods"].append(method_obj)
    return api


def preprocess_args(args):
    # Some pre-processing to create the output directory.

    if not os.path.isdir(args.output):
        try:
            os.makedirs(args.output, exist_ok=True)
        except IOError as e:
            print(e)
            sys.exit(0)


def file2html(path):
    with open(path, 'r') as f:
        return BeautifulSoup(f, "html.parser")


def dict2json(outdir, data):
    path = os.path.join(outdir, data["name"]) + ".json"
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--language",
        default="java",
        choices=["java"],
        help="Language associated with the given API docs"
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        required=True,
        help="Directory to output JSON files"
    )
    parser.add_argument(
        "-i", "--input",
        type=str,
        required=True,
        help="Input directory of API docs"
    )
    return parser.parse_args()


def main():
    args = get_args()
    preprocess_args(args)
    for path in Path(args.input).rglob('*/index.html'):
        apidoc_path = str(path)
        data = process_javadoc(file2html(apidoc_path))
        dict2json(args.output, data)


if __name__ == '__main__':
    main()
