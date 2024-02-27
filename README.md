# `python-compiler`

> A command-line tool to compile Python files into one ginormous one, with
> plugin support and more.

## Command-line usage

Must be invoked via `python -m python-compiler` from the parent directory due to
how Python's module resolver works. If you know a better way, please tell me!

```text
usage: python-compiler [-h] -i INPUT [-o [OUTPUT]] [--ignore-imports IGNORE_IMPORTS [IGNORE_IMPORTS ...]] [--remove-imports REMOVE_IMPORTS [REMOVE_IMPORTS ...]] [-p PRELUDE]
                       [-c DEFINE_CONSTANT DEFINE_CONSTANT] [-d DEFINE] [-m | --minify | --no-minify] [-j | --json | --no-json] [-t | --time | --no-time]
                       [--docstring | --no-docstring] [--module-hash-length MODULE_HASH_LENGTH] [--export-dictionary-mode {dict,munch,class,class_instance}]
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
                        defines one compile-time constant as a string. use some name that you're sure won't collide with any in your code, i.e. __MY_CONSTANT__
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
  --export-dictionary-mode {dict,munch,class,class_instance}
                        the method that export dictionaries are converted to dot-accessible objects
  --export-names-mode {locals,static}
                        how module exports are determined. use 'locals' for compatibility with existing code. forced to 'static' if --export-dictionary-mode is set to 'class' or
                        'class_instance'
```

## Library usage

I'm not sure how pip packages are supposed to be structured, so I'm probably not
going to publish this library. If you find it useful, I may look into it.

```python
import python_compiler

python_compiler.Compiler(
    source=input(),
    path="/path/to/source/file",
    options=python_compiler.CompilerOptions(
        # ...
        plugins=[
            # Plugins
            python_compiler.plugins.MinifyPlugin()
        ]
    )
)
```

For more examples, see the [CLI source code](./__main__.py). Note that `path`
does not need to be a real path, but it's used for import resolution.

## Plugins

### Built-in plugins

Built-in plugins can be imported from the `python-compiler.plugins` module. See
the docstrings for usage information.

#### MinifyPlugin

Uses `python-minifier` to minify the resulting code after bundling is performed.
This can reduce the size of the resulting code by a factor of 3 or more,
depending on the input.

#### ConstantsPlugin

Dynamically replaces variable names with content at compile-time. Similar to
`#IFDEF`s if you're using the C preprocessor.

#### PreludePlugin

An easy way to add a snippet of code at the beginning of the output.

### Plugin authoring

Plugins must inherit from [the base `Plugin` class](./src/plugin/plugin.py). An
example plugin might go something like this:

```python
class MyPlugin(python_compiler.plugin.Plugin):
    def hook_module(self, path, module):
        module = my_transformation(module)
        return module
```

There are a couple available hooks as of this writing:

- `hook_module`  
  A hook run before name translation is performed and modules are bundled
- `hook_module_post_transform`  
  A hook run after name translation is performed but before modules are bundled
- `hook_import`  
  A hook run on all imports a module imports
- `hook_import_resolution`  
  A hook run during the module resolution step. It can be used to define
  "virtual modules".
- `hook_output`  
  A hook called just prior to the end of code generation.
