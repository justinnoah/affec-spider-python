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

"""Object Relational Mapping for Child, Sibling, and Contact objects."""

from datetime import date, datetime

from twisted.logger import Logger


log = Logger()


class AllChildren(object):
    """
    AllChildren object.

    Non-database object containing the returned results of a search
    for both children and sibling groups.
    """

    # List of Child database objects
    children = []

    # List of SiblingGroup objects
    siblings = []

    def __init__(self, children=[], siblings=[]):
        """Let's do some type checking upfront to make life a bit easier."""
        if not ((type(children) == list) and (type(siblings) == list)):
            raise TypeError("children and siblings must be a list")

        for item in children:
            if type(item) != Child:
                raise TypeError("%s is not a Child object." % item)

        for item in siblings:
            if type(item) != SiblingGroup:
                raise TypeError("%s is not a SiblingGroup object." % item)

        # If types are all good, create an AllChildren object
        self.children = children
        self.siblings = siblings

    def merge(self, second):
        """
        Merge this with s second AllChildren object.

        @type second: AllChildren
        @param second: A second AllChildren to merge with this one.
        """

        log.debug("Begin merge")
        if type(second) != AllChildren:
            raise TypeError(
                "AllChildren can only merge with another AllChildren"
            )
        else:
            log.debug("Merge: 2nd type checks out, begin")

        log.debug("Merging children into AllChildren")
        log.debug("Second.children: %s" % second.children)
        for child in second.get_children():
            if child not in self.children:
                log.debug("Adding Child: %s" % child)
                self.children.append(child)

        log.debug("Merging SiblingGroups into AllChildren")
        for group in second.get_siblings():
            if group not in self.siblings:
                log.debug("Adding Group: %s" % group)
                self.siblings.append(group)

        log.debug(
            "Merge: Finished.\nMerge: %s\nMerge: %s" %
            (self.children, self.siblings)
        )

    def add_child(self, child):
        """
        Add a child object to list of children.

        @type child: Child
        @param child: Child object to be added.
        """

        if type(child) != Child:
            raise TypeError(
                "Only child objects can be added to the list of children."
            )

        self.children.append(child)

    def get_children(self):
        return list(self.children)

    def add_sibling_group(self, group):
        """
        Add a SiblingGroup object to list of sibling groups.

        @type group: SiblingGroup
        @param group: SiblingGroup object to be added.
        """

        if type(group) != SiblingGroup:
            raise TypeError(
                "Only child objects can be added to the list of children."
            )

        self.siblings.append(group)

    def get_siblings(self):
        return list(self.siblings)


class _DBObject(object):
    """Database object."""

    # A list of Attachment type objects
    _attachments = []

    def __init__(self, name, constants, variables):
        self.table_name = name
        self._constant_fields = constants
        self._variable_fields = variables

    def get_attachments(self):
        """
        @rtype: list(Attachment)
        @return: A clone of the list of Attachment type objects.
        """
        return list(self._attachments)

    def get_variable_fields(self):
        """
        @rtype: list(String)
        @return: A list of keys that can be updated
        """
        return list(self._variable_fields.keys())

    def update_field(self, key, value):
        """
        Update a single field.

        @type key: String
        @param key: Key of the _variable_fields

        @type value: object
        @param value: Data assigned to a field
        """
        self._variable_fields[key] = value

    def update_fields(self, d):
        """
        Update variable_fields with new data.

        @type d: dict
        @param d: new key<->value pairs to update variable_fields with.
        """
        self._variable_fields.update(d)

    def get_field(self, key):
        """
        Retrieve a single field.

        @type key: String
        @param key: Key of the _variable_fields

        @type value: object
        @param value: Data assigned to a field
        """
        return self._constant_fields.get(key) or self._variable_fields.get(key)

    def as_dict(self):
        """
        Return both constant and variable fields together in one dict.

        Siblings of this parent object may want to override this to include
        type checks on fields.

        @rtrype: dict
        @returns: a complete Child object as a dict.
        """
        return dict(self._constant_fields.update(self._variable_fields))

    def add_attachment(self, attachment):
        """
        Add an Attachment type object to the list of attachments.

        This feels a little janky to have this method attached to the
        _DBObject, though writing it twice (once for children and siblinggroup)
        seemed more annoying.

        @type attachment: Attachment
        @param attachment: Attachment for child/sibling object
        """
        if type(attachment) != Attachment:
            raise TypeError(
                "Only Attachment objects can be"
                "added to the list of Attachments."
            )

        self._attachments.append(attachment)

    def __str__(self):
        return "%s: %s" % (type(self), self.get_field('Name'))


class Child(_DBObject):
    """Child object."""

    def __init__(self):
        """Init."""
        # Table name constant
        name = "Children__c"

        # Constants
        constants = {
            # Recruitment Status
            "Recruitment_Status__c": "Pre-Recruitment",
            # Recruitment Region
            "Recruitment_Region__c": "National",
            # Recruitment update
            "Recruitment_Update__c": (
                "%s - Copied in by web spider from TARE" %
                datetime.now().strftime("%m/%d/%Y %H:%M")
            ),
            # Web Bio Approval - NULL
            "Web_Approval__c": False,
            # Child is Listed On Public Website - True
            "Adoption_Recruitment__c": True,
            # Public Web Adoption Recruitment Date
            "Web_Adoption_Recruitment_Date__c": "%s" % date.today(),
            # Data Base Listing-Private
            "Northwest_HG_Private_Listing_Date__c": "%s" % date.today(),
            # Data Base Listing-Private
            "Northwest_HG__c": True,
            # AFFEC Web Site
            "Web__c": True,
            # AFFEC Web (Posted To)
            "Web_Date__c": "%s" % date.today(),
            # AFFEC Web (Removed From)
            "Web_End_Date__c": None,
            # Action Needed Date
            "Action_Needed_Date__c": "%s" % date.today(),
        }

        # Variable
        variables = {
            # Child's First Name
            "Name": "",
            # Child Bulletin Date
            "Child_Bulletin_Date__c": "",
            # Child's State
            "Child_s_State__c": "TX",
            # Legal Status - If Possible
            "Legal_Status__c": '',
            # District/Region - District Number
            "District__c": 0,
            # Child's County - If Possible
            "Child_s_County__c": None,
            # State Case Number - tareID
            "Case_Number__c": '',
            # Caseworker Placement Notes - Bio
            "Caseworker_Placement_Notes__c": '',
            # Link to Child's Page - Tare Link
            "Link_to_Child_s_Page__c": "",
            # CW Update to Families
            "CW_Update_to_Families__c": (
                "%s - %s is looking for a home"
            ),
            "Case_Worker_Contact__c": ""
        }

        super(Child, self).__init__(name, constants, variables)

    def __str__(self):
        return "Child: %s" % self._variable_fields["Name"]


class SiblingGroup(_DBObject):
    """SiblingGroup object."""

    def __init__(self):
        """Init."""
        # List of Child objects in the SiblingGroup
        self.children = []

        # Table name constant
        name = "Sibling_Group__c"

        # Constants
        constants = {
            # Same as only child
            "Recruitment_Status__c": 'Pre-Recruitment',
            # Data Base Listing - Private (date)
            "Northwest_HG_Private_Listing_Date__c": '%s' % date.today(),
            # Data Base Listing - Private (checkmark)
            "Northwest_HG__c": True,
            # Last update
            "Date_of_Last_Update__c": '%s' % date.today(),
            # Recruitment Update
            "Recruitment_Update__c": (
                "%s - Copied in by web spider from TARE" %
                datetime.now().strftime("%m/%d/%Y %H:%M")
            ),
        }

        # Variables
        variables = {
            # TARE id
            "Case_Number__c": '',
            # All Children comma separated with an and before the last
            "Name": '',
            # Legal status if possible
            "Legal_Status2__c": '',
            # generated with positional B-H suffix - generated
            "Bulletin_Number__c": '',
            # Children's names
            "Child_1_First_Name__c": '',
            "Child_2_First_Name__c": '',
            "Child_3_First_Name__c": '',
            "Child_4_First_Name__c": '',
            "Child_5_First_Name__c": '',
            "Child_6_First_Name__c": '',
            "Child_7_First_Name__c": '',
            "Child_8_First_Name__c": '',
            # County - if available
            "Child_s_County__c": '',
            # Siblings' State
            "State__c": 'TX',
            # Primary Contact
            "Caseworker__c": '',
            "Children_s_Bio__c": '',
            "Caseworker_Placement_Notes__c": '',
        }

        super(SiblingGroup, self).__init__(name, constants, variables)

    def add_child(self, child):
        if type(child) == Child:
            self.children.append(child)
        else:
            raise TypeError(
                "Only Child objects can be added to children lists"
            )

    def get_children(self):
        return list(self.children)


class Contact(_DBObject):
    """Database object."""

    def __init__(self):
        """
        Init.

        FIXME:
        Much of the following data is hardcoded for TARE. Eventually this Needs
        to be added to the config or stripped out in some way to make room
        for any site to import data.
        """
        name = "Contact__c"

        constants = {
            "AccountId": "0014B0000048cGK",
            "Business_Name__c": "Texas DFPS",
            "Last_Action__c":
                "%s entered by TARE spider." % datetime.now().isoformat(' ')
        }

        variables = {
            'FirstName': '',
            'LastName': '',
            'Email': '',
            'HomePhone': '',
            'MobilePhone': '',
            'OtherPhone': '',
            'Phone': '',
            'MailingStreet': '',
            'MailingCity': '',
            'MailingState': '',
            'MailingPostalCode': '',
        }

        super(Contact, self).__init__(name, constants, variables)

    def name(self):
        return "%s %s" % (
            self._variable_fields['FirstName'],
            self._variable_fields['LastName']
        )


class Attachment(_DBObject):
    """Attachment object."""

    def __init__(self):
        """Init."""
        name = "Attachment__c"

        constants = {
            "ContentType": "image/jpeg",
        }

        variables = {
            "ParentId": "",
            "Name": "",
            "Body": "",
        }

        super(Attachment, self).__init__(name, constants, variables)


__all__ = [Child, SiblingGroup, Attachment, Contact]
