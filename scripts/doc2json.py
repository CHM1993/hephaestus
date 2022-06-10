import argparse
import json
import os
import re
import sys

from bs4 import BeautifulSoup


def extract_package_name(html_doc):
    return html_doc.find_all(class_="subTitle")[1].find_all(text=True)[2]


def extract_class_name(html_doc):
    return html_doc.find(class_="typeNameLabel").text


def extract_super_class(html_doc):
    regex = re.compile(".*extends ([^ ]+).*")
    text = html_doc.select(".description .blockList pre")[0].text
    text = text.replace("\n", " ")
    match = re.match(regex, text)
    if match:
        return match.group(1)
    return None


def extract_method_return_type(method_doc):
    regex = re.compile("(static )?(<([A-Z,]+)> )?([a-zA-Z<>]+)")
    text = method_doc.find(class_="colFirst").text
    match = re.match(regex, text)
    if not match:
        raise Exception("Cannot match method's signature {!r}".format(text))
    type_parameters = match.group(3)
    return_type = match.group(4)
    assert return_type is not None
    if type_parameters:
        type_parameters = type_parameters.split(",")
    return type_parameters, return_type


def extract_method_parameter_types(method_doc):
    regex = re.compile("\\(?([^, ]+)[ ][a-zA-Z0-9_]+,? *\\)?")
    text = method_doc.select(".colSecond code")[0].text.replace(
        "\n", " ").replace("\xa0", " ").split("(", 1)[1]
    return re.findall(regex, text)


def extract_method_name(method_doc):
    return method_doc.select(".colSecond a")[0].text


def extract_isstatic(method_doc):
    return 'static' in method_doc.find(class_="colFirst").text


def process_javadoc(html_doc):
    class_name = extract_class_name(html_doc)
    package_name = extract_package_name(html_doc)
    full_class_name = "{pkg}.{cls}".format(pkg=package_name,
                                           cls=class_name)
    super_class = extract_super_class(html_doc)
    api = {
      'name': full_class_name,
      'methods': [],
      'type_parameters': [],
      'implements': [],
      'inherits': super_class,
      'fields': [],
    }
    for method_doc in html_doc.find_all(class_="rowColor"):
        method_name = extract_method_name(method_doc)
        isstatic = extract_isstatic(method_doc)
        type_params, ret_type = extract_method_return_type(method_doc)
        param_types = extract_method_parameter_types(method_doc)
        method_obj = {
            "name": method_name,
            "parameters": param_types,
            "type_parameters": type_params,
            "return_type": ret_type,
            "is_static": isstatic,
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
    path = os.path.join(outdir, data["name"])
    with open(path, 'w') as f:
        json.dump(data, f)


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
        if not apidoc_path.endswith(".html"):
            continue
        data = process_javadoc(file2html(apidoc_path))
        dict2json(args.output, data)


if __name__ == '__main__':
    main()
