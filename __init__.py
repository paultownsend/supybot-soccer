from importlib import reload

from . import config, plugin

__version__ = "1.0.0"
__author__ = "Paul Townsend <pault@pault.org>"
__url__ = "https://github.com/paultownsend/supybot-soccer"

# In case we're being reloaded.
reload(config)
reload(plugin)

Class = plugin.Class
configure = config.configure
