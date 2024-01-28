import argparse
import os
import sys

from .modulemerger import ModuleMerger

DEFAULT_FILE_NAME = "__stdin__.py"


def main(argv: list[str]):
    parser = argparse.ArgumentParser(
        prog="python-module-merger",
        description="Merges Python modules together and outputs to stdout.")
    parser.add_argument("-i", "--input", required=True,
                        type=argparse.FileType('r'),
                        help="The input file, can be - for stdin")
    parser.add_argument("-o", "--output", nargs="?",
                        type=argparse.FileType('w'), default=sys.stdout,
                        help="The output file. Defaults to stdout")
    parser.add_argument("--ignore-imports", nargs="+",
                        default=[],
                        help="modules for which to ignore transforming imports for (i.e., leave them untouched)")
    args = parser.parse_args(argv)
    print(args)
    with args.input as input:
        mm = ModuleMerger(input.read(), os.path.join(
            os.getcwd(),
            input.name if input.name != "<stdin>" else DEFAULT_FILE_NAME))
        args.output.write(mm.merge())


if __name__ == "__main__":
    main(sys.argv[1:])
