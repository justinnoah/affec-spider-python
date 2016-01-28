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

"""Main module to get things fired up and running."""

import os
import sys

from configobj import ConfigObj, ConfigObjError
from twisted.logger import Logger, globalLogPublisher, textFileLogObserver

from data_types import AllChildren
from plugin import load_database_plugin, load_site_plugins


log = Logger()


def load_config(path="./config.ini"):
    """
    Load a config as a dict.

    @type path: String
    @param path: Path to config, default is in the same directory as this file

    @rtrype: ConfigObj
    @returns: the config
    """
    # OS agnostic path
    cfg_path = os.path.abspath(path)

    if not os.path.exists(cfg_path):
        raise Exception("%s does not exist!" % cfg_path)

    config = ConfigObj(cfg_path)

    # Verify the config has at least [sites], [databases], and at
    # least one plugin for each
    if 'sites' not in config.sections:
        raise ConfigObjError("Section [sites] is missing!")
    elif 'plugins' not in config['sites']:
        raise ConfigObjError("Section [sites] is missing plugins!")
    elif type(config['sites']['plugins']) is not list:
        config['sites']['plugins'] = [config['sites']['plugins']]

    if 'database' not in config.sections:
        raise ConfigObjError("Section [database] is missing!")
    elif 'plugin' not in config['database']:
        raise ConfigObjError("Section [database] is missing a plugin!")

    return config


def import_data(plugins):
    """
    Using the site plugin(s) import data into the given database.

    @type plugins: dict
    @param pluigns: {
        'sites': [SitePluigin,],
        'database': DBPlugin
    }
    """
    # All the children and siblings groups to be imported
    all_children = AllChildren()

    log.info("Begin parsing / importing data from sites.")
    # For each site listed in the config
    for site in plugins['sites']:
        # grab all chilrden and sibling groups
        all_children.merge(site.get_all())

    log.info("db plugin: add_allchildren.")
    # and import the data
    plugins['database'].add_all(all_children)


def main(config_path=None):
    """
    main.

    @type config_path: String
    @param config_path: optional alternative path to a config file
    """
    log.debug("Welcome to the jungle!")

    try:
        cfg = load_config(config_path) if config_path else load_config()
    except [Exception, ConfigObjError], e:
        log.failure(str(e))

    site_plugins = load_site_plugins(cfg['sites'])
    db_plugin = load_database_plugin(cfg['database'])
    plugins = {
        'sites': site_plugins,
        'database': db_plugin
    }
    import_data(plugins)


if __name__ == '__main__':
    globalLogPublisher.addObserver(
        textFileLogObserver(open("spider.log", 'w'))
    )
    globalLogPublisher.addObserver(textFileLogObserver(sys.stdout))
    sys.exit(main())
