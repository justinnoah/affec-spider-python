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
from twisted.logger import Logger


logger = Logger()


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

    if 'database' not in config.sections:
        raise ConfigObjError("Section [database] is missing!")

    if 'plugins' not in config['sites']:
        raise ConfigObjError("Section [sites] is missing plugins!")

    if 'plugin' not in config['database']:
        raise ConfigObjError("Section [database] is missing a plugin!")

    return config


def main(logger, config_path=None):
    """
    main.

    @type logger: Logger
    @param logger:  Twisted logger for output

    @type config_path: String
    @param config_path: optional alternative path to a config file
    """
    logger.debug("Welcome to the jungle!")

    try:
        cfg = load_config(config_path) if config_path else load_config()
    except [Exception, ConfigObjError], e:
        logger.failure(str(e))


if __name__ == '__main__':
    sys.exit(main(Logger()))
