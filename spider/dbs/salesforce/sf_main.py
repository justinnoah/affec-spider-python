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

from simple_salesforce import Salesforce as sfdb
from twisted.logger import Logger
from zope.interface import implements
from zope.interface.exceptions import DoesNotImplement

from data_types import Contact
from iplugin import DBPlugin


class Salesforce(object):
    """Salesforce plugin for AFFEC Spider."""

    # Let the plugin loader know this is a Database Plugin
    # and thus guarantee an interface
    implements(DBPlugin)

    log = Logger()

    settings_name = "Salesforce"

    def _check_config(self, config):
        """Verify the necessary inputs for salesforce are provided."""
        self.log.debug("Verifying configuration")

        keys = ['username', 'password', 'token', 'sandbox']
        for key in keys:
            if key not in config.keys():
                raise Exception(
                    "%s is missing '%s' in the configuration." % (
                        self.settings_name, key
                    )
                )
            elif not config[key]:
                raise Exception(
                    "%s is missing a configuration value for '%s'" % (
                        self.settings_name, key
                    )
                )

        return config

    def __init__(self, config):
        """Salesforce plugin __init__."""
        # Config
        self.config = self._check_config(config)
        # Create a salesforce instance
        self.log.debug("Create sf instance")
        self.sf = sfdb(
            username=self.config['username'],
            password=self.config['password'],
            security_token=self.config['token'],
            sandbox=bool(self.config['sandbox']),
        )

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
        if type(contact) is not Contact:
            raise TypeError(
                "add_contact requires a Contact object as an argument"
            )
        self.log.debug("add_contact: %s" % contact.name())
        self.sf.Contact.create(contact.as_dict())

    def find_similar_contact(self, contact):
        """Find and return a list of similar contacts."""
        query = """
            SELECT Id,%(fields)s FROM Contact
            WHERE (%(name)s) OR (%(mailing)s)
        """

        # Fields to return from the query along with the Id
        fields = {
            'MailingStreet': '',
            'MailingCity': '',
            'MailingState': '',
            'MailingPostalCode': '',
            'FirstName': [],
            'LastName': '',
            'Phone': '',
            'Email': '',
        }

        # Fields for comparison
        where_fields = {
            "FirstName": '',
            "LastName": '',
            "MailingPostalCode": '',
            "MailingStreet": '',
            "MailingCity": '',
        }

        for field in fields:
            data = contact.get_field(field)
            # Handle first names
            if field == 'FirstName':
                # First Name to search
                fname = data
                if fname.startswith("bob"):
                    fields["FirstName"].append('bob')
                    fields["FirstName"].append('r')
                elif fname.startswith('rob'):
                    fields["FirstName"].append('rob')
                    fields["FirstName"].append('b')
                elif fname.startswith('will'):
                    fields["FirstName"].append('will')
                    fields["FirstName"].append('b')
                elif fname.startswith('bill'):
                    fields["FirstName"].append('bill')
                    fields["FirstName"].append('w')
                else:
                    fields["FirstName"].append(fname[0])

                where = ["FirstName LIKE '%s%%'" % x for x in fields[field]]
                where_fields["FirstName"] = " OR ".join(where)
            elif field == "LastName":
                # Store the data in the fields (probably not necessary)
                fields[field] = data
                # Only use the first 4 letters of the last name
                where = "%s = '%s'" % (field, fields[field][0:4])
                where_fields["LastName"] = where
            else:
                fields[field] = data
                where = "%s = '%s'" % (field, fields[field])
                where_fields[field] = where

        select_fields = ",".join(fields.keys())
        fname = where_fields["FirstName"]
        del where_fields["FirstName"]
        mailing_list = []
        for k, v in where_fields:
            if v:
                mailing_list.append("%s = '%s'" % (k, v))

        final_query = query % {
            'fields': select_fields,
            'name': fname,
            'mailing': " AND ".join(mailing_list)
        }

        self.log.debug("QUERY:\n%s\n" % final_query)
        results = self.sf.query(final_query)

        if not results.get('totalSize'):
            results = self.add_contact(contact)

        # FIXME: Only handling the one most likely. This Needs to change.
        return [results] if not type(results) == list else results[0]

    def get_contact(self, contact, create=False):
        """Search for `contact` in the database. Create if `create`."""
        raise DoesNotImplement("Skeleton only.")
