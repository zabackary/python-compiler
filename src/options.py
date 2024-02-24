from dataclasses import dataclass, field
from typing import Literal

from .plugin import Plugin


@dataclass
class CompilerOptions:
    ignore_imports: list[str] = field(default_factory=lambda: [])
    remove_imports: list[str] = field(default_factory=lambda: [])
    docstring: str | None = """ Generated by python-minifier. """
    export_dictionary_mode: (Literal["dict"]
                             | Literal["munch"]
                             | Literal["class"]
                             | Literal["class_instance"]) = "dict"
    export_names_mode: (Literal["locals"]
                        | Literal["static"]) = "locals"
    short_generated_names: bool = False
    hash_length: int = 8

    plugins: list[Plugin] = field(default_factory=lambda: [])
