""" jinjarecurse (CLI)

Usage:
    jinjarecurse --vars=VARS_FILE --input=INPUT_PATH --output=OUTPUT_PATH

Options:
    -v <file>, --vars   <file>
    -i <file>, --input  <file>
    -o <file>, --output <file>
"""
import jinja2
import yaml
import sys
import shutil

from binaryornot.check import is_binary
from pathlib import Path
from docopt import docopt


def main():
    arguments = docopt(__doc__, version='jinjarecurse 0.0.2')
    paths = {
        'variables': Path(arguments['--vars']),
        'input': Path(arguments['--input']),
        'output': Path(arguments['--output']),
    }
    check_paths(**paths)
    variables = read_vars(paths['variables'])
    template(paths, variables)


def template(paths, variables):
    ''' Handles figuring out src/dest file pathing and invoking template writer '''
    if paths['input'].is_dir():
        for search in paths['input'].rglob('*'):
            if search.is_file():
                output = str(search).replace(str(paths['input']), str(paths['output']))
                write_template(search, Path(output), variables)
    elif paths['input'].is_file():
        write_template(paths['input'], paths['output'], variables)


def write_template(ipath, opath, variables):
    opath_template = jinja2.from_string(str(opath.absolute()))
    opath_result = opath_template.render(**variables)
    opath_result.parent.mkdir(parents=True, exist_ok=True)
    print("Writing from {} to {}".format(ipath, opath_result))

    if is_binary(str(ipath.absolute())):
        copying_without_templating(ipath, opath_result, "{} is binary.".format(ipath))
    elif check_file_is_empty(str(ipath.absolute()), opath_result):
        copying_without_templating(ipath, opath_result, "{} is empty.".format(ipath))
    else:
        try:
            template = jinja2.get_template(str(ipath.absolute()))
            file_content = template.render(**variables)

            if file_content and not file_content.isspace():
                opath_result.write_text(file_content)
                opath_result.chmod(ipath.stat().st_mode)
            else:
                print("WARNING: {} is empty after templating. Ignoring file".format(ipath))
        except:
            copying_without_templating(ipath, opath_result, "Failed to generate template for {}.".format(ipath))


def copying_without_templating(ipath, opath, reason):
    print("WARNING: {}. Copying without templating.".format(reason))
    shutil.copyfile(str(ipath), str(opath))


def check_file_is_empty(ipath, opath):
    try:
        with open(ipath, 'r') as f:
            file_content = f.read()
            return not file_content or file_content.isspace()
    except:
        copying_without_templating(ipath, opath, "Failed to read {}.".format(ipath))


def check_paths(**kwargs):
    bail = False
    for k, path in kwargs.items():
        if k == 'variables' and not path.is_file():
            print("ERROR: {} ({}) is not a file".format(path, k), file=sys.stderr)
            bail = True
        if k == 'input' and not path.exists():
            print("ERROR: {} ({}) does not exist".format(path, k), file=sys.stderr)
            bail = True
        if k == 'output' and path.exists():
            print("WARNING: {} ({}) exists and any conflicting files will be overwritten".format(path, k),
                  file=sys.stderr)
    if bail:
        sys.exit(1)


def read_vars(var_file):
    var_obj = Path(var_file)
    return yaml.safe_load(var_obj.read_text())


if __name__ == "__main__":
    main()
