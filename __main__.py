import argparse
import json
import os
import sys
import time

from .src import plugin
from .src.compiler import Compiler
from .src.graph import TopologicalSortError
from .src.options import CompilerOptions
from .src.transformers import AsteriskImportError, TransformError

DEFAULT_FILE_NAME = "__stdin__.py"
PROG_NAME = "python-compiler"
ERRORS = {
    "circular-deps": "failed to compile due to circular dependencies",
    "recursion": "failed to compile due to excessive amount of nested modules",
    "asterisk-import": "failed to compile because of asterisk import in %s",
    "transform": "%s",
    "assignment-to-constant": "failed to compile due to assignment to constant: %s"
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
        description="Compiles/merges Python files.")
    parser.add_argument("-i", "--input", required=True,
                        type=argparse.FileType('r'),
                        help="the input file, can be - for stdin")
    parser.add_argument("-o", "--output", nargs="?",
                        type=argparse.FileType('w'), default=sys.stdout,
                        help="the output file. Defaults to stdout")
    parser.add_argument("--ignore-imports", nargs="+",
                        default=[],
                        help="modules for which to ignore transforming imports for (i.e., leave them untouched)")
    parser.add_argument("--remove-imports", nargs="+",
                        default=[],
                        help="modules for which to remove imports for")
    parser.add_argument("-p", "--prelude",
                        default=None,
                        help="some Python code to insert at the top of the file. must be well-formed parsable Python code")
    parser.add_argument("-c", "--define-constant", nargs=2,
                        default=[],
                        action="append",
                        help="defines one compile-time constant. use some name that you're sure won't collide with any in your code, i.e. __MY_CONSTANT__")
    parser.add_argument("-d", "--define", nargs=1,
                        default=[],
                        action="append",
                        help="equivalent to defining a constant to be 1 using --define-constant.")
    parser.add_argument("-m", "--minify", action=argparse.BooleanOptionalAction,
                        help="minifies the result")
    parser.add_argument("-j", "--json", action=argparse.BooleanOptionalAction,
                        help="outputs messages as json")
    parser.add_argument("-t", "--time", action=argparse.BooleanOptionalAction,
                        default=True,
                        help="puts the time at the top of the generated code. --no-time for deterministic builds")
    parser.add_argument("--docstring", action=argparse.BooleanOptionalAction,
                        default=True,
                        help="puts a generated docstring at the top of the module. added by default")
    parser.add_argument("--module-hash-length",
                        type=int,
                        default=8,
                        help="the length of the hash used for making modules unique")
    parser.add_argument("--export-dictionary-mode",
                        default="dict",
                        choices=["dict", "munch", "class", "class_instance"],
                        help="the method that export dictionaries are converted to dot-accessible objects")
    parser.add_argument("--export-names-mode",
                        default="locals",
                        choices=["locals", "static"],
                        help="how module exports are determined. use 'locals' for compatibility with existing code. forced to 'static' if --export-dictionary-mode is set to 'class' or 'class_instance'")
    args = parser.parse_args(argv)
    constants: dict[str, bool | str | int | float] = {
        "__COMPILED__": True
    }
    for [constant_name, constant_value] in args.define_constant:
        constants[constant_name] = constant_value
    for [constant_name] in args.define:
        constants[constant_name] = 1
    current_time = (" at %s" % time.strftime(
        "%a, %d %b %Y %H:%M:%S", time.localtime())) if args.time else ""
    with args.input as input:
        try:
            plugins: list[plugin.Plugin] = []
            plugins.append(plugin.ConstantsPlugin(constants=constants))
            if args.prelude is not None:
                plugins.append(plugin.PreludePlugin(prelude=args.prelude))
            if args.minify:
                plugins.append(plugin.MinifyPlugin())
            merged = Compiler(
                source=input.read(),
                path=os.path.join(os.getcwd(),
                                  input.name if input.name != "<stdin>" else DEFAULT_FILE_NAME),
                options=CompilerOptions(
                    ignore_imports=args.ignore_imports,
                    remove_imports=args.remove_imports,
                    docstring=f""" Generated by {PROG_NAME}{current_time} """ if args.docstring else None,
                    export_dictionary_mode=args.export_dictionary_mode,
                    export_names_mode=args.export_names_mode,
                    short_generated_names=args.minify,
                    hash_length=args.module_hash_length,
                    plugins=plugins
                ))()
            if args.json:
                args.output.write(json.dumps({
                    "output": merged
                }))
            else:
                args.output.write(merged)
        except TopologicalSortError:
            print(
                format_error("circular-deps", args.json),
                file=sys.stderr)
            sys.exit(1)
        except RecursionError:
            print(
                format_error("recursion", args.json),
                file=sys.stderr)
            sys.exit(1)
        except AsteriskImportError as e:
            print(
                format_error("asterisk-import", args.json, e.args),
                file=sys.stderr)
            sys.exit(1)
        except TransformError as e:
            print(
                format_error("transform", args.json, e.args),
                file=sys.stderr)
            sys.exit(1)
        except plugin.constants.AssignmentToConstantError as e:
            print(
                format_error("assignment-to-constant", args.json, e.args),
                file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main(sys.argv[1:])
