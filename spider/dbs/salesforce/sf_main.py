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

from datetime import datetime
from dateutil.relativedelta import relativedelta
from dateutil.parser import parse as bday_parse
import re

from bs4 import BeautifulSoup
from simple_salesforce import Salesforce as sfdb
from twisted.logger import Logger
from zope.interface import implements
from zope.interface.exceptions import DoesNotImplement

from data_types import AllChildren, Child, Contact, SiblingGroup
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

        keys = ['username', 'password', 'token', 'sandbox', 'contact_account']
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
        # Report with a datetime string appended
        n = datetime.now().isoformat().replace(":", "-")
        self.report = open("Report_%s.txt" % n, 'w')

        self.nationalities = []

        # Grab all metadata
        all_field_metadata = self.sf.Children__c.describe()['fields']
        for field in all_field_metadata:
            if field.get("name") == "Child_s_Nationality__c":
                # Grab the Nationality picklist labels
                if "picklistValues" in field.keys():
                    for value_dict in field["picklistValues"]:
                        # Must get the label. We don't want to add "None" to
                        # the list.
                        label = value_dict.get('label')
                        if label:
                            self.nationalities.append(label)

    def _query(self, query):
        """
        Raw salesforce query.

        INTERNAL USE ONLY - HERE BE DRAGONS!
        """
        return self.sf.query(query)

    def _results_to_childs(self, results):
        """
        Convert salesforce Child results into a list of Child objects.

        @type res: [OrderedDict]
        @param res: salesforce returned list of Children__c OrderedDicts

        @rtype: [Child]
        @return: salesforce [Children__c] as a [Child]
        """
        children = []

        for res in results:
            child = Child()
            child.update_fields(res)
            children.append(child)

        return children

    def _results_to_sibling_groups(self, results):
        """
        Convert salesforce Sibling results into a list of SiblingGroup objects.

        @type res: [OrderedDict]
        @param res: salesforce returned list of Sibling_Group__c OrderedDicts

        @rtype: SiblingGroup
        @return: salesforce [Sibling_Group__c] as a [SiblingGroup]
        """
        sgroups = []

        for res in results:
            sgroup = SiblingGroup()
            sgroup.update_fields(res)
            sgroups.append(sgroup)

        return sgroups

    def _results_to_contacts(self, results):
        """
        Convert salesforce Sibling results into a list of SiblingGroup objects.

        @type res: [OrderedDict]
        @param res: salesforce returned list of Sibling_Group__c OrderedDicts

        @rtype: SiblingGroup
        @return: salesforce [Sibling_Group__c] as a [SiblingGroup]
        """
        contacts = []

        for res in results:
            self.log.debug("SF CONTACT: %s" % unicode(res))
            contact = Contact()
            contact.update_fields(res)
            contacts.append(contact)

        return contacts

    def add_all(self, all_of_them):
        """Import an AllChildren object into the database."""
        if type(all_of_them) is not AllChildren:
            raise TypeError(
                "%s != AllCheldren: db.add_all can only add "
                "AllChildren objects to the database." % type(all_of_them)
            )

        # Start with Children
        children = all_of_them.get_children()
        for child in children:
            # We do not save the return value as it
            # is not needed for anything here.
            self.add_or_update_child(child)

        # Finish with SiblingGroups
        sgroups = all_of_them.get_siblings()
        for sgroup in sgroups:
            # We do not save the return value as it
            # is not needed for anything here.
            self.add_or_update_sibling_group(sgroup)

    def find_by_case_number(self, case_number, t=None, return_fields=[]):
        """
        Find either Children or SiblingGroups with `case_number`.

        @type case_number: String
        @param case_number: Case Number to search by

        @type t: _DBObject
        @param t: Either Child or SiblingGroup object. None can be used for
        uncertain cases and may return both

        @rtype: AllChildren
        @return: Object containing results from the case number query
        """
        self.log.debug(
            "Querying case_number: %s" % case_number
        )

        # The search criteria is only a case number
        criteria = {
            'Case_Number__c': case_number
        }

        # We are returning an AllChildren type since this method can
        # be used for either Children__c or Sibling_Group__c
        existing_results = AllChildren([], [])

        # Type not specified, return both
        if not t:
            children = self.get_children_by(criteria, return_fields)
            siblings = self.get_sibling_group_by(criteria, return_fields)
            for child in self._results_to_childs(children):
                existing_results.add_child(child)
            for sibling in self._results_to_sibling_groups(siblings):
                existing_results.add_or_update_sibling_group(sibling)
        # Return results from Children__c
        elif t == Child:
            children = self.get_children_by(criteria, return_fields)
            for child in self._results_to_childs(children):
                existing_results.add_child(child)
        # Return results from Sibling_Group__c
        elif t == SiblingGroup:
            siblings = self.get_sibling_group_by(criteria, return_fields)
            for sibling in self._results_to_sibling_groups(siblings):
                existing_results.add_sibling_group(sibling)
        # Uh-oh, not good.
        else:
            raise TypeError(
                "find_by_case_number requires "
                "a type of None, Child, or SiblingGroup.\nReceived: %s"
                % t
            )

        # Returning an AllChildren object with Childs SiblingGroups or both
        return existing_results

    def add_or_update_child(self, child):
        """
        Add a Child object to the database.

        Doing so may also require adding a Contact object as well.
        """
        if type(child) is not Child:
            raise TypeError(
                "%s != Child: Can only add Child "
                "objects to the database as Child objects" % type(child)
            )

        self.log.info("%s - %s" % (
            child.get_field("Case_Number__c"), child.get_field("Name")
        ))

        self.log.debug("Importing Child: %s/%s - %s" % (
            child.get_field("Name"),
            child.get_field("Case_Number__c"),
            child.get_field("Link_to_Child_s_Page__c")
        ))

        save_fields = child.get_variable_fields()

        # Check for existing with TareId
        existing_tare_id_results = self.find_by_case_number(
            child.get_field("Case_Number__c"),
            Child,
            return_fields=save_fields
        )

        # If a Children__c object exists with the given tare id
        if not existing_tare_id_results.is_empty():
            self.log.debug("TARE Id exists in the database already, updating.")
            existing_child = existing_tare_id_results.get_children()[0]
            self.log.debug(
                "Updating child with Id: %s" % existing_child.get_field("Id")
            )
            child.update_field("Id", existing_child.get_field("Id"))

        # Check for a contact and add it first
        contact = child.get_field("Case_Worker_Contact__c")
        if type(contact) == Contact:
            self.log.debug("Contact: %s" % contact)
            returned = self.get_contact(contact, create=True)[0]
            if type(returned) == list:
                returned = returned[0]
            self.log.debug("Returned Contact: %s" % returned)
            child.update_field(
                'Case_Worker_Contact__c',
                returned.get_field("Id"),
            )
        else:
            child.update_field('Case_Worker_Contact__c', '')

        # Do our best to turn the Nationality into picklist options
        nationalities = child.get_field("Child_s_Nationality__c")
        if nationalities:
            picklist = []
            word = re.compile("\w+")
            for nationality in nationalities:
                word_match = word.match(nationality)
                first_word = (
                    "Unknown" if not word_match
                    else word_match.group()
                )
                for pick in self.nationalities:
                    if first_word in pick:
                        picklist.append(pick)
            if not picklist:
                picklist.append("Unknown")

            child.update_field('Child_s_Nationality__c', ";".join(picklist))

        child_id = child.get_field("Id")
        if child_id:
            in_db_child = existing_child.as_dict()
            scraped_dict = child.as_dict()
            if "Child_Bulletin_Date__c" in scraped_dict:
                del scraped_dict["Child_Bulletin_Date__c"]
            if "Child_Bulletin_Date__c" in in_db_child:
                del in_db_child["Child_Bulletin_Date__c"]
            null_to_value = {}
            update_dict = {}

            for k, v in scraped_dict.items():
                if in_db_child[k] != v:
                    # Birthday check
                    if k == "Child_s_Birthdate__c":
                        # Bday from site
                        scraped_bday = bday_parse(v)
                        # Bday currently in the DB
                        db_bday = bday_parse(in_db_child[k])
                        # Six months
                        three_months = relativedelta(months=3)
                        # Acceptable bounds for a birthdate
                        lower_bound = db_bday - three_months
                        upper_bound = db_bday + three_months
                        # If within range, skip
                        if lower_bound <= scraped_bday <= upper_bound:
                            continue

                    update_dict[k] = {
                        "old": in_db_child[k],
                        "new": v
                    }
                    if in_db_child[k] is None:
                        null_to_value[k] = v

            keys = update_dict.keys()
            non_update = (
                True
                if "Recruitment_Update__c" in keys and len(keys) == 1
                else False
            )
            self.log.debug("Non-Update? %s" % non_update)
            if keys and not non_update:
                self.log.debug("Keys: %s" % keys)
                self.report.write(
                    "============\n"
                    "UPDATE CHILD\n"
                    "============\n"
                )
                self.report.write(
                     "%s\n" % child.get_field("Link_to_Child_s_Page__c")
                )
                self.report.write("%s - %s\n" % (
                    child.get_field("Case_Number__c"), child.get_field("Name"))
                )
                for k, v in update_dict.items():
                    if k == "Child_s_Bio__c":
                        report_str = "%s: Bio has change." % k
                    else:
                        report_str = ("%s: %s, %s" % (k, v["old"], v["new"]))
                    self.report.write("%s\n" % report_str)

                self.report.write("\n")

            if null_to_value.keys():
                self.sf.Children__c.update(
                    child.get_field("Id"), null_to_value
                )
        else:
            self.report.write(
                "=========\n"
                "ADD CHILD\n"
                "=========\n")
            self.report.write(
                "%s\n" % child.get_field("Link_to_Child_s_Page__c")
            )
            self.report.write("%s - %s\n" % (
                child.get_field("Case_Number__c"), child.get_field("Name"))
            )
            x = self.sf.Children__c.create(child.as_dict())
            self.report.write("\n")
            child.update_field("Id", x.get("id"))

        # Add attachments and give the attachment's the Child object's ID
        attachments = list(child.get_attachments())
        in_db_attachments = self._query(
            "SELECT Id,BodyLength FROM Attachment WHERE ParentId='%s'" %
            child.get_field("Id")
        )
        current_body_sizes = [
            a["BodyLength"] for a in in_db_attachments["records"]
        ]

        # self.log.info("New:\n%s" % sorted(new_body_sizes))
        for attachment in attachments:
            # Is the attachment going into the db?
            adding = True
            bs = None
            for bs in current_body_sizes:
                if attachment.get_field("BodyLength") == bs:
                    # In this instance, more than likely, the attachment
                    # is already in the database, so we skip it
                    adding = False
                    break

            # Remove already added items
            if bs and adding:
                current_body_sizes.remove(bs)

            if adding:
                a = self.add_attachment(
                    attachment,
                    child.get_field("Id"),
                    child.get_field("Name"),
                    Child,
                )
                self.log.debug("Adding attachment: %s" % a)

        return child

    def add_attachment(self, attachment, sid, name, t):
        """
        Fullfill the add_attachment requirement.

        @type attachment: Attachment
        @param attachment: The attachment to Insert

        @type sid: String
        @param sid: The object ID to associate with the attachment

        @type name: String
        @param name: Name field of the Child or SiblingGroup

        @type t: type
        @param t: Child or SiblingGroup

        @rtype: OrderedDict
        @return: Attachment ID
        """
        self.log.info("Adding attachment")
        # Add the ParentId to the attachment
        attachment.update_field("ParentId", sid)
        # Create said attachment
        attach_dict = attachment.as_dict()
        del attach_dict["BodyLength"]
        attached = self.sf.Attachment.create(attach_dict)

        # If this is the profile pic on the page, let's add it to the db object
        if attachment.is_profile:
            b64_data = attachment.get_field("Body")
            img = BeautifulSoup('', 'lxml')
            img_tag = img.new_tag(
                "img",
                alt=name,
                src="data:image/jpeg;base64,%s" % b64_data,
            )
            img.append(img_tag)
            if t is Child:
                self.sf.Children__c.update(
                    sid,
                    {'Child_s_Photo__c': img.prettify()}
                )
            elif t is SiblingGroup:
                self.sf.Sibling_Group__c.update(
                    sid,
                    {'Sibling_Photo__c': img.prettify()}
                )

        # Return the sf results
        return attached

    def get_children_by(self, search_criteria, return_fields=[]):
        """
        Simple query result of a Child objects.

        @type search_criteria: dict
        @param search_criteria: A dictionary of keys and values
        to search children by.

        @type return_fields: list(String)
        @param return_fields: The fields the query should return,
        if none are passed, only Id is returned

        @rtype: list
        @return: Return results from salesforce of children Ids only.
        """
        # Query string
        query_string = (
            "SELECT %(select_fields)s FROM Children__c WHERE %(where_fields)s"
        )

        # select fiesds, we always return at least Id
        s_fields = set(["Id"])
        for field in return_fields:
            s_fields.add(field)

        # Join the list of s_fields into a string separated by ", "
        select_fields = ", ".join(s_fields)

        # Parse the dict indo a where clause
        w_fields = []
        for k, v in search_criteria.items():
            w_fields.append("%s = '%s'" % (k, v))

        # Join the list of w_filds into a string separated by AND
        where_fields = " AND ".join(w_fields)

        # Use the internal query method to query
        final_query = query_string % {
            'select_fields': select_fields,
            'where_fields': where_fields
        }

        results = self._query(final_query)["records"]

        self.log.debug("\nQuery: %s\n\nResults: %s" % (
            unicode(final_query),
            unicode(results)
        ))

        return results

    def get_children_count(self):
        """Return the number of Child objects in the database."""
        raise DoesNotImplement("Skeleton only.")

    def add_or_update_sibling_group(self, sgroup):
        """
        Add a SiblingGroup object to the database.

        Doing so may also require adding a Contact object as well.
        """
        if type(sgroup) is not SiblingGroup:
            raise TypeError(
                "%s != SiblingGroup: Can only add SiblingGroup "
                "objects to the database as SiblingGroups" % type(sgroup)
            )

        self.log.info("%s - %s" % (
            sgroup.get_field("Case_Number__c"), sgroup.get_field("Name")
        ))

        # Check for existing with TareId
        save_fields = sgroup.get_variable_fields()
        existing_tare_id_results = self.find_by_case_number(
            sgroup.get_field("Case_Number__c"),
            SiblingGroup,
            return_fields=save_fields
        )
        scraped_dict = sgroup.as_dict()

        # Child reference Id string
        reference_str = "Child_%d_First_Name__c"

        # Given a sibling group, the children should be added first
        children = sgroup.get_children()
        c_names = [x.get_field("Name") for x in children]
        children_references = {}
        for num, child in enumerate(children):
            names = list(c_names)
            names.remove(child.get_field("Name"))
            child.update_field("Child_s_Siblings__c", ", ".join(names))
            added_child = self.add_or_update_child(child)
            cid = added_child.get_field("Id")
            children_references[reference_str % int(int(num) + 1)] = cid

        scraped_dict.update(children_references)

        contact = sgroup.get_field("Caseworker__c")
        added_contact = self.get_contact(contact, create=True)[0]
        cid = added_contact.get_field("Id")
        scraped_dict.update({'Caseworker__c': cid})

        self.log.debug("EXISTING SGROUPS: %s" % existing_tare_id_results)

        # Are we updating or creating?
        if not existing_tare_id_results.is_empty():
            self.log.debug("TARE Id exists in the database already, updating.")
            existing_group = existing_tare_id_results.get_siblings()[0]
            gr_id = existing_group.get_field("Id")
            self.log.debug("Updating sibling group with Id: %s" % gr_id)
            scraped_dict.update({"Id": gr_id})

        if scraped_dict.get("Id"):
            in_db_group = existing_group.as_dict()
            if "Child_Bulletin_Date__c" in scraped_dict:
                del scraped_dict["Child_Bulletin_Date__c"]
            if "Child_Bulletin_Date__c" in in_db_group:
                del in_db_group["Child_Bulletin_Date__c"]
            null_to_value = {}
            update_dict = {}

            for k, v in scraped_dict.items():
                if in_db_group[k] != v:
                    update_dict[k] = {
                        "old": in_db_group[k],
                        "new": v
                    }
                    if in_db_group[k] is None:
                        null_to_value[k] = v

            keys = update_dict.keys()
            non_update = (
                True
                if "Recruitment_Update__c" in keys and len(keys) == 1
                else False
            )
            self.log.debug("Non-Update? %s" % non_update)
            if keys and not non_update:
                self.log.debug("Keys: %s" % keys)
                self.report.write(
                    "====================\n"
                    "UPDATE SIBLING GROUP\n"
                    "====================\n"
                )
                self.report.write(
                     "%s\n" % scraped_dict.get("Children_s_Webpage__c")
                )
                self.report.write("%s - %s\n" % (
                    scraped_dict.get("Case_Number__c"),
                    scraped_dict.get("Name")
                ))
                for k, v in update_dict.items():
                    if k == "Children_s_Bio__c":
                        report_str = "%s: Bio has change." % k
                    else:
                        report_str = ("%s: %s, %s" % (k, v["old"], v["new"]))
                    self.report.write("%s\n" % report_str)

                self.report.write("\n")

            if null_to_value.keys():
                self.sf.Sibling_Group__c.update(
                    scraped_dict.get("Id"), null_to_value
                )
        else:
            self.report.write(
                "=================\n"
                "ADD SIBLING GROUP\n"
                "=================\n"
            )
            self.report.write(
                "%s\n" % scraped_dict.get("Children_s_Webpage__c")
            )
            self.report.write("%s - %s\n" % (
                scraped_dict.get("Case_Number__c"), scraped_dict.get("Name"))
            )
            x = self.sf.Sibling_Group__c.create(scraped_dict)
            scraped_dict.update({"Id": x.get("id")})

        # Add attachments and give the attachment's the Child object's ID
        attachments = list(sgroup.get_attachments())
        in_db_attachments = self._query(
            "SELECT Id,BodyLength FROM Attachment WHERE ParentId='%s'" %
            scraped_dict["Id"]
        )
        current_body_sizes = [
            a["BodyLength"] for a in in_db_attachments["records"]
        ]

        # self.log.info("New:\n%s" % sorted(new_body_sizes))
        for attachment in attachments:
            # Is the attachment going into the db?
            adding = True
            bs = None
            for bs in current_body_sizes:
                if attachment.get_field("BodyLength") == bs:
                    # In this instance, more than likely, the attachment
                    # is already in the database, so we skip it
                    adding = False
                    break

            # Remove already added items
            if bs and adding:
                current_body_sizes.remove(bs)

            if adding:
                a = self.add_attachment(
                    attachment,
                    scraped_dict.get("Id"),
                    scraped_dict.get("Name"),
                    SiblingGroup,
                )
                self.log.debug("Adding attachment: %s" % a)

        return sgroup

    def get_sibling_group_by(self, search_criteria, return_fields=[]):
        """
        Simple query result of a Child objects.

        @type search_criteria: dict
        @param search_criteria: A dictionary of keys and values
        to search children by.

        @type return_fields: list(String)
        @param return_fields: The fields the query should return,
        if none are passed, only Id is returned

        @rtype: list
        @return: Return results from salesforce of children Ids only.
        """
        # Query string
        query_string = (
            "SELECT %(select_fields)s "
            "FROM Sibling_Group__c "
            "WHERE %(where_fields)s"
        )

        # select fiesds, we always return at least Id
        s_fields = set(["Id"])
        for field in return_fields:
            s_fields.add(field)

        # Join the list of s_fields into a string separated by ", "
        select_fields = ", ".join(s_fields)

        # Parse the dict indo a where clause
        w_fields = []
        for k, v in search_criteria.items():
            w_fields.append("%s = '%s'" % (k, v))

        # Join the list of w_filds into a string separated by AND
        where_fields = " AND ".join(w_fields)

        # Use the internal query method to query
        final_query = query_string % {
            'select_fields': select_fields,
            'where_fields': where_fields
        }

        results = self._query(final_query)["records"]

        self.log.debug("\nQuery: %s\n\nResults: %s" % (
            unicode(final_query),
            unicode(results)
        ))

        return results

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
        contact.update_field("AccountId", self.config['contact_account'])
        returned = self.sf.Contact.create(contact.as_dict()).get("id")
        contact.update_field("Id", returned)
        return contact

    def get_contact(self, contact, create=False):
        """Find and return a list of similar contacts, create if missing."""
        query = """
            SELECT Id,%(fields)s FROM Contact
            WHERE (%(name)s) AND (%(mailing)s)
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
            # 'Email': '',
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
            self.log.debug("Field Data: %s" % data)
            # Handle first names
            if field == 'FirstName':
                # First Name to search
                fname = data.strip()
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

        mailing_list = []
        for k, v in where_fields.iteritems():
            if "Mailing" in k:
                mailing_list.append(v)

        final_query = query % {
            'fields': select_fields,
            'name': fname,
            'mailing': " AND ".join(mailing_list)
        }

        self.log.debug("CONTACT QUERY:\n%s\n" % final_query)
        r = self._query(final_query).get("records")
        self.log.debug("QUERY RESULTS:\n%s\n" % unicode(r))
        results = self._results_to_contacts(r)

        if (not results) and create:
            self.log.debug("Creating contact")
            results = self.add_contact(contact)

        # FIXME: Only handling the one most likely. This may need to change.
        if results:
            return [results] if not type(results) == list else results
        else:
            return []
