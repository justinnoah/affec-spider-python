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
from helpers import return_type
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
}

CONTACT_SELECTORS = {
    "Name": "Name",
    "Address": "MailingStreet",
    "Email Address": "Email",
    "Phone Number": "Phone"
}

ATTACHMENT_SELECTORS = {
    "profile_picture": "div##Information > div:nth-of-type(1) > a > img",
    "other_pictures": "div#contentGallery",
}


@return_type(Child)
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
    try:
        child_info.update_fields({
            "Link_to_Child_s_Page__c": link,
            'Case_Number__c': soup.select(
                CHILD_SELECTORS['Case_Number__c']
            )[0].text.strip(),
        })
        child_fields.remove('Link_to_Child_s_Page__c')
    except ValueError:
        pass

    tare_provided_fields = {
        "Name": "Name",
        "Age": "Child_s_Birthdate__c",
        "Race": "Child_s_Nationality__c",
        "Gender": "Child_s_Sex__c",
        "Ethnicity": "Child_s_Nationality__c",
        "Region": "District__c",
        "Primary Language": "Child_s_Primary_Language__c",
    }

    def grab_child_data(current, itr):
        field = current.text.strip()

        # Handle special parsing requirements
        if field == "Age":
            value = get_birthdate(next(itr).text.strip())
        elif field in ["Ethnicity", "Race"]:
            value = child_info.get_field(tare_provided_fields[field])
            value.append(next(itr).text.strip())
        elif field == "Region":
            value = "Region: %s" % next(itr).text.strip()
        elif field in tare_provided_fields.keys():
            value = next(itr).text.strip()
        # Short circuit if nothing relavent found
        else:
            return None

        # Update child_info field
        child_info.update_field(tare_provided_fields[field], value)

    log.debug("Begin Child Fields")
    fields = iter(soup.find("span", text="Name").parent.parent.select("> div"))
    for field in fields:
        # Only one div should be proccessed,
        # if multiple exist, let's break it down
        rabbit_hole = field.select("div")
        fs = iter(rabbit_hole)
        # Given sub-fields, lets check them
        if len(rabbit_hole):
            for rabbit_itr in fs:
                grab_child_data(rabbit_itr, fs)
        else:
            grab_child_data(field, fields)

    # Grab the Bio
    bio = ""
    info = soup.select_one("div##Information")
    headers = info.find_all("div", class_="groupHeader")
    bodies = info.find_all("div", class_="groupBody")

    # Add all the headers and bodies to the bio
    for header, body in zip(headers, bodies):
        bio += "%s\n%s\n\n" % (header.text.strip(), body.text.strip())

    # Update siblings' bio
    child_info.update_field("Child_s_Bio__c", bio.strip())

    # Return Data
    return child_info


@return_type(Contact)
def parse_contact_info(soup):
    """
    Parse Contact data from a swirl of soup.

    @type soup: BeautifulSoup data
    @param soup: Chunk of a webpage containing the contact info.

    @rtype: Contact
    @return: Contact object filled in with data from the soup.
    """
    contact_info = Contact()

    tare_provided_fields = {
        "Name": "",
        "Address": "",
        "Phone Number": "Phone",
        "Email Address": "Email",
    }

    def grab_contact_data(current, itr):
        field = current.text.strip()

        # Handle special parsing requirements
        if field == "Name":
            contact_info.update_fields(
                parse_name(next(itr).text.strip())
            )
        elif field == "Phone":
            contact_info.update_field(
                tare_provided_fields[field],
                validators["phone"](next(iter).text.strip())
            )
        elif field == "Address":
            cleaned_re = re.compile("\s+")
            info = cleaned_re.sub(" ", next(itr).text.strip())
            try:
                address = validators["address"](info.strip())
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
        elif field in tare_provided_fields.keys():
            value = next(itr).text.strip()
            contact_info.update_field(tare_provided_fields[field], value)
        # End of grab_contact_data

    cw_soup = iter(soup.select("fieldset > div"))

    for field in cw_soup:
        # Only one div should be proccessed,
        # if multiple exist, let's break it down
        rabbit_hole = field.select("div")
        fs = iter(rabbit_hole)
        # Given sub-fields, lets check them
        if len(rabbit_hole):
            for rabbit_itr in fs:
                grab_contact_data(rabbit_itr, fs)
        else:
            grab_contact_data(field, cw_soup)

    return contact_info


def parse_attachments(cname, session, souped, base_url):
    """
    Parse attachments and add them to the child object.

    @type cname: String
    @param cname: Child's name.

    @type session: requests session
    @param session: The "browser" session that has us logged into TARE.

    @type souped: BeautifulSoup data
    @param soup: Chunk of a webpage containing the contact info.

    @type base_url: String
    @param base_url: The beginning of all TARE urls.
    """
    # Get the profile picture attachment
    try:
        profile_img_tag = souped.select(
            ATTACHMENT_SELECTORS["profile_picture"]
        )[0]
        if profile_img_tag.get("src"):
            profile_image_data = get_pictures_encoded(
                session, base_url, [profile_img_tag.get("src")], True
            )
    except IndexError:
        profile_image_data = {'full': None, 'thumbnail': None}

    gallery = souped.select_one(ATTACHMENT_SELECTORS.get("other_pictures"))
    urls = []
    if gallery:
        other_img_tags = gallery.find_all("img", class_="galleryImage")
        for tag in other_img_tags:
            if tag.get("src"):
                urls.append(tag.get("src"))

    # Get other images
    other_images = get_pictures_encoded(
        session, base_url, urls, False
    )

    log.debug(
        "GRABBED ALL ATTACHMENTS! %s and %s" % (
            len(profile_image_data), len(other_images)
        )
    )

    attachments_returned = []

    # Create attachments for the profile and thumbnail of the profile
    for img in profile_image_data:
        for k, v in img.items():
            name = "%s-%s.jpg" % (cname, str(random.randint(100, 999)))
            attch = create_attachment(v["data"], name)
            attch.update_field("BodyLength", v["length"])
            if k == "full":
                attch.is_profile = True
            attachments_returned.append(attch)

    # Create attachments of all other images and append a number to the name
    for i, img in enumerate(other_images):
        # For non-Profile pictures, we just want the full image.
        # thumbnail is None anyway
        name = "%s-%s.jpg" % (cname, str(random.randint(100, 999)))
        full = img.get("full")
        attch = create_attachment(full.get("data"), name)
        attch.update_field("BodyLength", full.get("length"))
        attachments_returned.append(attch)

    log.debug("Returning %s attachments for %s" % (
        len(attachments_returned), cname)
    )
    return list(attachments_returned)


@return_type(Child)
def gather_profile_details_for(link, session, base_url):
    """
    Given a TARE URL, pull the following data about a child.

    Photos, Name, TareId, Age (to be converted to a birthdate), others
    """
    log.info("Child:\n%s" % link)
    # Data required to have for a child

    # "Import" the html into BeautifulSoup for easy traversal
    req = session.get(link)
    if "/Application/TARE/Home.aspx/Error" in req.url:
        raise ValueError("TARE Server had an error for link: %s" % link)
    elif "/Application/TARE/Home.aspx/Default" in req.url:
        raise ValueError("TARE redirected away from the url %s" % link)

    # HTML data from the request
    html_data = req.text

    # Parse the html for Child data scraping
    souped = BeautifulSoup(html_data, 'lxml')
    child = parse_child_info(link, souped)

    # Get a smaller soup for the contact data since it's contained in one area
    contact = parse_contact_info(souped)

    # Get pictures/attachments
    attachments = parse_attachments(
        child.get_field("Name"), session, souped, base_url
    )
    log.debug("Adding %s images to %s from\n\t%s" % (
        len(attachments), child.get_field("Name"), link
    ))
    for attachment in attachments:
        child.add_attachment(attachment)

    # Add the contact to childself.Case_Worker_Contact__c
    child.update_field("Case_Worker_Contact__c", contact)

    log.debug(
        "Child data successfully generated. Returning `%s`" %
        child.get_field("Name")
    )
    return child
