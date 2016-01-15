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


class _DBObject(object):
    """Database object."""

    def __init__(self, name, constants, variables):
        self.table_name = name
        self._constant_fields = constants
        self._variable_fields = variables

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
        }

        super(Child, self).__init__(name, constants, variables)


class SiblingGroup(_DBObject):
    """SiblingGroup object."""

    def __init__(self):
        """Init."""
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


class Contact(_DBObject):
    """Database object."""

    def __init__(self):
        """Init."""
        name = "Contact__c"

        constants = {

        }

        variables = {
            'FirstName': '',
            'LastName': '',
            'Email': '',
            'HomePhone': '',
            'MobilePhone': '',
            'OtherPhone': '',
            'Phone': '',
            'Address': '',
        }

        super(Contact, self).__init__(name, constants, variables)


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
