# `python-compiler`

A command-line tool to compile Python files into one ginormous one.

## Command-line usage

Must be invoked via `python -m python-compiler` from the parent directory due to
how Python's module resolver works.

```
usage: python-compiler [-h] -i INPUT [-o [OUTPUT]]
                       [--ignore-imports IGNORE_IMPORTS [IGNORE_IMPORTS ...]]
                       [-m | --minify | --no-minify] [-j | --json | --no-json]

Compiles/merges Python files.

options:
  -h, --help            show this help message and exit
  -i INPUT, --input INPUT
                        the input file, can be - for stdin
  -o [OUTPUT], --output [OUTPUT]
                        the output file. Defaults to stdout
  --ignore-imports IGNORE_IMPORTS [IGNORE_IMPORTS ...]
                        modules for which to ignore transforming imports for (i.e., leave them
                        untouched)
  -m, --minify, --no-minify
                        minifies the result
  -j, --json, --no-json
                        outputs messages as json
```

To-do list:

- [ ] Add compile-time constants
