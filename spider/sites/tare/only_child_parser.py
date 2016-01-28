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

"""Tare helper functions to parse children pages."""
import random
import re

from bs4 import BeautifulSoup
from twisted.logger import Logger

from data_types import Child, Contact
from utils import (
    create_attachment, get_birthdate, get_pictures_encoded, parse_name
)
from validators import dict_of_validators as validators

log = Logger()

# These are the magic phrases that get the data from a TARE profile page
# They also happen to represent some, if not all of the fields to be updated
CHILD_SELECTORS = {
    "Name": (
        "div##Information > div:nth-of-type(2) > div:nth-of-type(2) > "
        "span:nth-of-type(1)"
    ),
    "Child_s_Birthdate__c": (
        "div##Information > div > div > div:nth-of-type(2) > "
        "span:nth-of-type(1)"
    ),
    "Case_Number__c": (
        "div#pageContent > div > div > div:nth-of-type(2) > span"
    ),
    "District__c": (
        "div##Information > div > div > div:nth-of-type(2) > span"
    ),
    "Child_s_County__c": "",
    "Caseworker_Placement_Notes__c": [
        "div##Information > div:nth-of-type(6) > p",
        "div##Information > div:nth-of-type(8) > p",
    ],
}

CONTACT_SELECTORS = {
    "Name": "Name",
    "Address": "MailingStreet",
    "Email Address": "Email",
    "Phone Number": "Phone"
}

ATTACHMENT_SELECTORS = {
    "profile_picture": "div##Information > div:nth-of-type(1) > a > img",
    "other_pictures": "div#contentGallery > div > div > a > img",
}


def parse_child_info(link, soup):
    """
    Parse Child data from a swirl of soup.

    @type soup: BeautifulSoup data
    @param soup: Chunk of a webpage containing the child info.

    @rtype: Child
    @return: Child object filled in with data from the soup.
    """
    child_info = Child()
    child_fields = list(child_info.get_variable_fields())

    # Handle Special Cases
    child_info.update_fields({
        "Link_to_Child_s_Page__c": link
    })

    try:
        child_fields.remove('Link_to_Child_s_Page__c')
    except ValueError:
        pass

    log.debug("Begin Child Fields")
    fields = iter(soup.find("span", text="Name").parent.parent.select("> div"))
    for field in fields:
        # Grab the name
        if "Name" in field.text:
            child_info.update_field("Name", next(fields).text.strip())
        # For some reason, Age and Gender are grouped together...
        elif "Age" in field.text:
            fs = iter(field.select("div"))
            for f in fs:
                if "Age" in f.text:
                    bday = get_birthdate(next(fs).text.strip())
                    child_info.update_field('Child_s_Birthdate__c', bday)
                    log.debug("bday: %s" % bday)

    return child_info


def parse_contact_info(soup):
    """
    Parse Contact data from a swirl of soup.

    @type soup: BeautifulSoup data
    @param soup: Chunk of a webpage containing the contact info.

    @rtype: Contact
    @return: Contact object filled in with data from the soup.
    """
    contact_info = Contact()
    contact_fields = list(contact_info.get_variable_fields())

    cw_soup = iter(soup.select("fieldset > div"))

    for field in cw_soup:
        info = parse_name(next(cw_soup).text.strip())
        if field.text == "Name":
            contact_info.update_fields(parse_name(info))
        elif field == "Phone":
            contact_info.update_field("Phone", validators["phone"](info))
        elif field == "Address":
            cleaned_re = re.compile("\s+")
            info = cleaned_re.sub(" ", info)
            address = validators["address"](info.strip())
            try:
                str_types = [str, unicode]
                address_fields = {
                    "MailingStreet": (
                        address.street
                        if type(address.street) in str_types
                        else " ".join(address.street)
                    ),
                    "MailingCity": (
                        address.city
                        if type(address.city) in str_types
                        else " ".join(address.city)
                    ),
                    "MailingState": (
                        address.state
                        if type(address.state) in str_types
                        else " ".join(address.state)
                    ),
                    "MailingPostalCode": (
                        address.zip
                        if type(address.zip) in str_types
                        else " ".join(address.zip)
                    ),
                }
                contact_info.update_fields(address_fields)
            except:
                pass
        elif "Email Address" in field.text:
            contact_info.update_field("Email", info)

    return contact_info


def parse_attachments(child, session, souped, base_url):
    """
    Parse Contact data from a swirl of soup.

    @type soup: BeautifulSoup data
    @param soup: Chunk of a webpage containing the contact info.

    @rtype: Contact
    @return: Contact object filled in with data from the soup.
    """
    # Get the profile picture attachment
    profile_image_data = get_pictures_encoded(
        session, souped, CHILD_SELECTORS.get("profile_picture"), base_url, True
    )

    # Get other images
    other_images = get_pictures_encoded(
        session, souped,
        ATTACHMENT_SELECTORS.get("other_pictures"),
        base_url, False
    )

    # Create attachments for the profile and thumbnail of the profile
    for img in profile_image_data:
        for k, v in img.iteritems():
            name = "-%s-%s.jpg" % (
                child_name, str(random.randInt(100, 999))
            )
            child.add_attachment((create_attachment(v, name)))

    # Create attachments of all other images and append a number to the name
    for i, img in enumerate(other_images):
        # For non-Profile pictures, we just want the full image.
        # thumbnail is None anyway
        name = "-%s-%s.jpg" % (
            child.get_field("Name"), str(random.randInt(100, 999))
        )
        child.add_attachment((create_attachment(img.get("full"), name)))


def gather_profile_details_for(link, session, base_url):
    """
    Given a TARE URL, pull the following data about a child.

    Photos, Name, TareId, Age (to be converted to a birthdate), others
    """
    log.info("Only Child:\n%s" % link)
    # Data required to have for a child

    # "Import" the html into BeautifulSoup for easy traversal
    req = session.get(link)
    if "/Application/TARE/Home.aspx/Error" in req.url:
        raise Exception("TARE Server had an error for link: %s" % link)

    # HTML data from the request
    html_data = req.text

    # Parse the html for Child data scraping
    souped = BeautifulSoup(html_data, 'lxml')
    child = parse_child_info(link, souped)

    # Get a smaller soup for the contact data since it's contained in one area
    contact = parse_contact_info(souped)

    # Add the contact to childself.Case_Worker_Contact__c
    child.update_field("Case_Worker_Contact__c", contact)

    log.debug(
        "Child data successfully generated. Returning `%s`" %
        child.get_field("Name")
    )
    return child
