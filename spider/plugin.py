
#  Copyright 2016 A Family For Every Child
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

"""Plugin loading module."""

from twisted.logger import Logger
from zope.interface.exceptions import BrokenImplementation
from zope.interface.verify import verifyClass, verifyObject

from iplugin import SitePlugin


logger = Logger()


def load_plugin(location, cfg, *args, **kwargs):
    """
    Load a plugin.

    @type location: String
    @param location: import path

    @type cfg: ConfigObj
    @param cfg: Configuration section used by the plugin

    @rtrype: Plugin
    @return: Return either a SitePlugin or DBPlugin
    """
    pth = "%s" % location

    # import sites.SitePlugin and make sites.SitePlugin.plugin available
    imp = __import__(pth, globals(), locals(), ['plugin'])
    try:
        verifyClass(SitePlugin, imp.plugin)
        # Instantiate the plugin
        kwargs.update({
            'config': cfg[imp.plugin.settings_name]
        })
        _tmp = imp.plugin(*args, **kwargs)
        verifyObject(SitePlugin, _tmp)
    except [BrokenImplementation, AttributeError], e:
        logger.failure("%s:\n%s" % (location, str(e)))

    return _tmp


def load_site_plugins(cfg):
    """
    load SitePlugin based plugins listed in the config.

    @type cfg: ConfigObj
    @param cfg: The sites' section of the config

    @rtrype: list
    @returns: list of loaded plugins
    """
    plugins = []
    for splug in cfg['plugins']:
        pth = "sites.%s" % splug
        logger.debug("Loading SitePlugin plugin: %s" % splug)
        plugins.append(load_plugin(pth, cfg))
        logger.debug("%s Loaded!" % splug)

    return plugins


def load_database_plugin(cfg):
    """
    Load a DBPlugin based plugin listed in the config.

    @type cfg: ConfigObj
    @param cfg: The database section of the config

    @rtrype: DBPlugin implenter
    @returns: A DBPlugin implemented plugin
    """
    plugin_name = cfg['plugin']
    pth = "dbs.%s" % plugin_name

    logger.debug("Loading DBPlugin plugin: %s" % plugin_name)
    plugin = load_plugin(pth, cfg)
    logger.debug("%s Loaded!" % plugin_name)

    return plugin
