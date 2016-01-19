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

"""Salesforce plugin for AFFEC Spider."""

from zope.interface import implements
from zope.interface.exceptions import DoesNotImplement

from iplugin import DBPlugin


class Salesforce(object):
    """Salesforce plugin for AFFEC Spider."""

    # Let the plugin loader know this is a Database Plugin
    # and thus guarantee an interface
    implements(DBPlugin)

    settings_name = "Salesforce"

    def __init__(self, config):
        """Salesforce plugin __init__."""
        self.config = None

    def add_child(self, child):
        """
        Add a Child object to the database.

        Doing so may also require adding a Contact object as well.
        """
        raise DoesNotImplement("Skeleton only.")

    def get_children_count(self):
        """Return the number of Child objects in the database."""
        raise DoesNotImplement("Skeleton only.")

    def add_sibling_group(self, sgroup):
        """
        Add a SiblingGroup object to the database.

        Doing so may also require adding a Contact object as well.
        """
        raise DoesNotImplement("Skeleton only.")

    def get_sibling_group_count(self):
        """Return the number of SiblingGroup objects in the database."""
        raise DoesNotImplement("Skeleton only.")

    def add_contact(self, contact):
        """Add a Contact object to the database."""
        raise DoesNotImplement("Skeleton only.")

    def get_contact(self, contact, create=False):
        """Search for `contact` in the database. Create if `create`."""
        raise DoesNotImplement("Skeleton only.")
