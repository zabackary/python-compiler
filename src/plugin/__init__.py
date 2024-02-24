from .constants import ConstantsPlugin
from .minify import MinifyPlugin
from .plugin import Plugin
from .prelude import PreludePlugin

builtin_plugins = [ConstantsPlugin, MinifyPlugin, PreludePlugin]

__all__ = ["Plugin", "builtin_plugins",
           "ConstantsPlugin", "MinifyPlugin", "PreludePlugin"]
