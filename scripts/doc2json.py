import argparse
import json
import os
import re
import sys

from bs4 import BeautifulSoup


REGULAR_CLASS = 0
INTERFACE = 1
ABSTRACT_CLASS = 2
ENUM = 3


def extract_package_name(html_doc):
    return html_doc.find_all(class_="subTitle")[1].find_all(text=True)[2]


def extract_class_name(html_doc):
    regex = re.compile("([A-Za-z0-9]+).*")
    text = html_doc.find(class_="typeNameLabel").text
    match = re.match(regex, text)
    if not match:
        raise Exception("Cannot extract class name: {!r}".format(text))
    return match.group(1)


def extract_class_type_parameters(html_doc):
    regex = re.compile(r'(?:[^,(]|<[^)]*>)+')
    text = html_doc.find(class_="typeNameLabel").text.split("<", 1)
    if len(text) == 1:
        return []
    text = text[1][:-1].encode("ascii", "ignore").decode()
    return [p[0] for p in re.findall(regex, text)]


def extract_super_class(html_doc):
    regex = re.compile(".*extends ([^ ]+).*")
    text = html_doc.select(".description .blockList pre")[0].text.encode(
        "ascii", "ignore").decode()
    text = text.replace("\n", " ")
    match = re.match(regex, text)
    if match:
        return match.group(1)
    return None


def extract_class_type(html_doc):
    text = html_doc.select(".description pre")[0].text
    if 'interface' in text:
        return INTERFACE
    if 'abstract class' in text:
        return ABSTRACT_CLASS
    if 'enum' in text:
        return None
    return REGULAR_CLASS


def extract_super_interfaces(html_doc):
    for doc in html_doc.select(".description .blockList dl"):
        if doc.find("dt").text != "All Superinterfaces:":
            continue
        return list(doc.find("dd").text.encode(
            "ascii", "ignore").decode().split(", "))
    return []


def extract_method_return_type(method_doc, is_constructor):
    if is_constructor:
        return [], None

    regex = re.compile(
        r"(static )?(default )?(<(.*)>)?(.+)")
    text = method_doc.find(class_="colFirst").text.encode(
        "ascii", "ignore").decode()
    match = re.match(regex, text)
    if not match:
        raise Exception("Cannot match method's signature {!r}".format(text))
    type_parameters = match.group(4)
    return_type = match.group(5)
    assert return_type is not None
    if type_parameters:
        regex = re.compile(r"(?:[^,(]|<[^)]*>)+")
        type_parameters = re.findall(regex, type_parameters)
    return type_parameters or [], return_type


def extract_method_parameter_types(method_doc, is_constructor):
    key = ".colConstructorName code" if is_constructor else ".colSecond code"
    regex = re.compile("\\(?([^ ,<>]+(<.*>)?)[ ]+[a-z0-9_]+,? *\\)?")
    try:
        text = method_doc.select(key)[0].text.replace(
            "\n", " ").replace("\xa0", " ").replace("\u200b", "").split(
                "(", 1)[1]
    except IndexError:
        # We probably encounter a field
        return None
    return [p[0] for p in re.findall(regex, text)]


def extract_method_name(method_doc, is_constructor):
    try:
        key = ".colConstructorName a" if is_constructor else ".colSecond a"
        return method_doc.select(key)[0].text
    except IndexError:
        # We are probably in a field
        return None


def extract_isstatic(method_doc, is_constructor):
    if is_constructor:
        return False
    return 'static' in method_doc.find(class_="colFirst").text


def is_constructor(method_doc):
    return method_doc.find(class_="colConstructorName") is not None


def is_field(method_doc):
    try:
        text = method_doc.select(".colFirst a")[0].text
        return all(c.isupper() for c in text.replace("_", ""))
    except IndexError:
        # Probably, we are in a constructor
        return False


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
      'fields': [],
    }
    methods = html_doc.find_all(class_="rowColor") + html_doc.find_all(
        class_="altColor")
    for method_doc in methods:
        is_con = is_constructor(method_doc)
        method_name = extract_method_name(method_doc, is_con)
        isstatic = extract_isstatic(method_doc, is_con)
        type_params, ret_type = extract_method_return_type(method_doc,
                                                           is_con)
        param_types = extract_method_parameter_types(method_doc,
                                                     is_con)

        if param_types is None:
            continue
        method_obj = {
            "name": method_name,
            "parameters": param_types,
            "type_parameters": type_params,
            "return_type": ret_type,
            "is_static": isstatic,
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
    for base in os.listdir(args.input):
        apidoc_path = os.path.join(args.input, base)
        if not apidoc_path.endswith(".html") and 'Set.html' not in apidoc_path:
            continue
        data = process_javadoc(file2html(apidoc_path))
        dict2json(args.output, data)


if __name__ == '__main__':
    main()
