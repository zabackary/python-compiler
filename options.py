from dataclasses import dataclass, field
from typing import Literal


@dataclass
class ModuleMergerOptions:
    ignore_imports: list[str] = field(default_factory=lambda: [])
    remove_imports: list[str] = field(default_factory=lambda: [])
    docstring: str | None = """ Generated by python-minifier. """
    prelude: str | None = None
    compile_time_constants: dict[str, str | bool | int | float] = field(
        default_factory=lambda: {})
    export_dictionary_mode: (Literal["dict"]
                             | Literal["munch"]
                             | Literal["class"]
                             | Literal["class_instance"]) = "dict"
    export_names_mode: (Literal["locals"]
                        | Literal["static"]) = "locals"
    short_generated_names: bool = False
    hash_length: int = 8
