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

"""Plugin interface for sites."""

from zope.interface import Attribute, Interface


InvalidPluginType = TypeError


class SitePlugin(Interface):
    """
    A site.

    Sites are plugins for parsing data out of specific websites.
    For example, TARE.
    """

    base_url = Attribute("""
        @type base_url: String
        @ivar base_url: The base url of the Site. Sometimes necessary for links
        Added as an ivar for logging purposes
    """)

    config = Attribute("""
        @type config: dict
        @ivar config: configuration options
    """)

    settings_name = Attribute("""
        @type name: String
        @ivar name: config section under [Sites]. Typically this will be the
        same name as the plugin.
    """)

    def __init__(config):
        """
        Instantiate a SitePlugin and require config options to be passed.

        @type config: dict
        @param config: dictionary of key/value options needed by the plugin.
        """

    def get_all():
        """
        Return an AllChildren with all sibling groups and children found.

        @rtrype: AllChildren
        @return: All children and sibling groups discovered on the site
        """

    def get_child_by_id(cid):
        """
        Find a child by it's given external id.

        @type cid: String
        @param cid: External ID

        @rtype: list
        @return: list of Child objects found by external id. Typically this
        will contain one element.
        """

    def get_sibling_group_by_id(sgid):
        """
        Find a child by it's given external id.

        @type sgid: String
        @param sgid: External ID

        @rtype: list
        @return: list of Sibling Group objects found by external id. Typically
        this will contain one element.
        """


class DBPlugin(Interface):
    """
    A database.

    Database backend, whether it be MySQL, etc.
    """

    config = Attribute("""
        @type config: dict
        @ivar config: configuration options
    """)

    settings_name = Attribute("""
        @type name: String
        @ivar name: config section under [Sites]. Typically this will be the
        same name as the plugin.
    """)

    def add_or_update_child(child):
        """
        Add or update a child object to/in the database.

        @type child: Child
        @param child: Child object to add to the database

        @rtrype: Integer
        @returns: id of added child
        """

    def add_or_update_sibling_group(sgroup):
        """
        Add a sibling group object to the database.

        @type sgroup: SiblingGroup
        @param sgroup: Sibling group to add to the database

        @rtrype: Integer
        @returns: id of added sibling group
        """

    def get_children_count():
        """
        Return the number of children in the database.

        @rtrype: C(int)
        @returns: Number of Children__c objects
        """

    def get_sibling_group_count():
        """
        Return the number of sibling groups in the database.

        @rtrype: C(int)
        @returns: Number of Sibling_Group__c objects
        """

    def add_contact(contact):
        """
        Add a contact.

        @type contact: Contact
        @param contact: Contact to add

        @rtrype: OrderedDict
        @returns: Contact ID
        """

    def add_attachment(attachment, childid, name):
        """
        Add an attachment object to the Salesforce Database.

        @type attachment: Attachment
        @param attachment: The attachment to Insert

        @type childid: String
        @param childid: Id to associate with the attachment

        @rtype: OrderedDict
        @return: Attachment ID
        """

    def get_contact(contact, create=False):
        """
        Lookup a contact with similar data to the contact parameter.

        @type contact: Contact
        @param contact: Contact which to find similarities of.

        @type create: Bool
        @param create: Whether or not to create the contact
        if the 'contact' is not found in the database

        @rtype: list(Contact)
        @returns: A list of similar Contacts or an empty list if none
        """
