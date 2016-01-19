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

"""SitePlugin module for Tare."""

from twisted.logger import Logger
from zope.interface import implements
from zope.interface.exceptions import DoesNotImplement

from iplugin import SitePlugin


class TareSite(object):
    """
    Site plugin for Tare.

    Plugin using interface SitePlugin (found in iplugin.py).
    """

    implements(SitePlugin)

    base_url = "https://www.dfps.state.tx.us"
    settings_name = "Tare"
    log = Logger()

    def __init__(self, config):
        """Fire it up."""
        self.log.debug("TARE plugin starting up.")
        self.config = config

    def get_all(self):
        """Tare definition of SitePlugin method."""
        raise DoesNotImplement("Skeleton only.")

    def get_child_by_id(self, cid):
        """Tare definition of SitePlugin method."""
        raise DoesNotImplement("Skeleton only.")

    def get_sibling_group_by_id(self, sgid):
        """Tare definition of SitePlugin method."""
        raise DoesNotImplement("Skeleton only.")
