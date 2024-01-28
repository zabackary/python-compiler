import argparse
import json
import os
import sys

from .graph import TopologicalSortError
from .minify import minify
from .module_import_finder import AsteriskImportError, TransformError
from .modulemerger import ModuleMerger
from .options import ModuleMergerOptions

DEFAULT_FILE_NAME = "__stdin__.py"
PROG_NAME = "python-module-merger"
ERRORS = {
    "circular-deps": "failed to compile due to circular dependencies",
    "recursion": "failed to compile due to excessive amount of nested modules",
    "asterisk-import": "failed to compile because of asterisk import in %s",
    "transform": "failed to transform module: %s"
}


def format_error(name: str, output_json: bool = False, args: tuple[str, ...] = ()):
    msg = ERRORS[name] % args
    if output_json:
        return json.dumps({
            "error": True,
            "name": name,
            "msg": msg
        })
    else:
        return f"{PROG_NAME}: error: {msg}"


def main(argv: list[str]):
    parser = argparse.ArgumentParser(
        prog=PROG_NAME,
        description="Merges Python modules together and outputs to stdout.")
    parser.add_argument("-i", "--input", required=True,
                        type=argparse.FileType('r'),
                        help="the input file, can be - for stdin")
    parser.add_argument("-o", "--output", nargs="?",
                        type=argparse.FileType('w'), default=sys.stdout,
                        help="the output file. Defaults to stdout")
    parser.add_argument("--ignore-imports", nargs="+",
                        default=[],
                        help="modules for which to ignore transforming imports for (i.e., leave them untouched)")
    parser.add_argument("-m", "--minify", action=argparse.BooleanOptionalAction,
                        help="minifies the result")
    parser.add_argument("-j", "--json", action=argparse.BooleanOptionalAction,
                        help="outputs messages as json")
    args = parser.parse_args(argv)
    with args.input as input:
        try:
            mm = ModuleMerger(
                source=input.read(),
                path=os.path.join(os.getcwd(),
                                  input.name if input.name != "<stdin>" else DEFAULT_FILE_NAME),
                options=ModuleMergerOptions(
                    ignore_imports=args.ignore_imports
                ))
            merged = mm.merge()
            if args.minify:
                merged = minify(merged)
            if args.json:
                args.output.write(json.dumps({
                    "output": merged
                }))
            else:
                args.output.write(merged)
        except TopologicalSortError:
            print(
                format_error("circular-deps", args.json))
            sys.exit(1)
        except RecursionError:
            print(
                format_error("recursion", args.json))
            sys.exit(1)
        except AsteriskImportError as e:
            print(
                format_error("asterisk-import", args.json, e.args))
            sys.exit(1)
        except TransformError as e:
            print(
                format_error("transform", args.json, e.args))
            sys.exit(1)


if __name__ == "__main__":
    main(sys.argv[1:])
