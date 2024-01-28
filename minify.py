from .python_minifier import minify as py_minify  # type:ignore


def minify(source: str) -> str:
    return py_minify(
        source=source,
        remove_annotations=True,
        combine_imports=True,
        hoist_literals=True,
        rename_locals=True,
        rename_globals=True,
        remove_pass=True,
        remove_object_base=True,
        remove_literal_statements=True,
        constant_folding=True,
        convert_posargs_to_args=True,
        remove_explicit_return_none=True,
    )
