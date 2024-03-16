from .constants import ConstantsPlugin
from .minify import MinifyPlugin
from .plugin import Plugin
from .prelude import PreludePlugin
from .simplify_if import SimplifyIfPlugin

builtin_plugins = [ConstantsPlugin, MinifyPlugin,
                   PreludePlugin, SimplifyIfPlugin]

__all__ = ["Plugin", "builtin_plugins",
           "ConstantsPlugin", "MinifyPlugin", "PreludePlugin", "SimplifyIfPlugin"]
