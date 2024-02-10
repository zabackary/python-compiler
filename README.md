# `python-compiler`

A command-line tool to compile Python files into one ginormous one.

## Command-line usage

Must be invoked via `python -m python-compiler` from the parent directory due to
how Python's module resolver works.

```
usage: python-compiler [-h] -i INPUT [-o [OUTPUT]] [--ignore-imports IGNORE_IMPORTS [IGNORE_IMPORTS ...]] [--remove-imports REMOVE_IMPORTS [REMOVE_IMPORTS ...]] [-p PRELUDE]
                       [-c DEFINE_CONSTANT DEFINE_CONSTANT] [-d DEFINE] [-m | --minify | --no-minify] [-j | --json | --no-json] [-t | --time | --no-time]
                       [--docstring | --no-docstring] [--module-hash-length MODULE_HASH_LENGTH] [--export-dictionary-mode {dict,munch,class}]
                       [--export-names-mode {locals,static}]

Compiles/merges Python files.

options:
  -h, --help            show this help message and exit
  -i INPUT, --input INPUT
                        the input file, can be - for stdin
  -o [OUTPUT], --output [OUTPUT]
                        the output file. Defaults to stdout
  --ignore-imports IGNORE_IMPORTS [IGNORE_IMPORTS ...]
                        modules for which to ignore transforming imports for (i.e., leave them untouched)
  --remove-imports REMOVE_IMPORTS [REMOVE_IMPORTS ...]
                        modules for which to remove imports for
  -p PRELUDE, --prelude PRELUDE
                        some Python code to insert at the top of the file. must be well-formed parsable Python code
  -c DEFINE_CONSTANT DEFINE_CONSTANT, --define-constant DEFINE_CONSTANT DEFINE_CONSTANT
                        defines one compile-time constant. use some name that you're sure won't collide with any in your code, i.e. __MY_CONSTANT__
  -d DEFINE, --define DEFINE
                        equivalent to defining a constant to be 1 using --define-constant.
  -m, --minify, --no-minify
                        minifies the result
  -j, --json, --no-json
                        outputs messages as json
  -t, --time, --no-time
                        puts the time at the top of the generated code. --no-time for deterministic builds (default: True)
  --docstring, --no-docstring
                        puts a generated docstring at the top of the module. added by default (default: True)
  --module-hash-length MODULE_HASH_LENGTH
                        the length of the hash used for making modules unique
  --export-dictionary-mode {dict,munch,class}
                        the method that export dictionaries are converted to dot-accessible objects
  --export-names-mode {locals,static}
                        how module exports are determined. use 'locals' for compatibility with existing code. forced to 'static' if --export-dictionary-mode is set to 'class'
```

To-do list:

- [ ] Add compile-time constants
