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
import re

from bs4 import BeautifulSoup
from twisted.logger import Logger

from data_types import Child, Contact
from utils import create_attachment, get_birthdate, get_pictures_encoded
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
    "profile_picture": "div##Information > div:nth-of-type(1) > a > img",
    "other_pictures": "div#contentGallery > div > div > a > img",
}

CONTACT_BASE = "div##Information > div > div > fieldset"
CONTACT_SELECTORS = {
    "Name": (
        "> div:nth-of-type(1) > div:nth-of-type(2)"
    ),
    "MailingStreet": (
        "> div:nth-of-type(2) > div:nth-of-type(2) > span"
    ),
    "Email": (
        "> div:nth-of-type(3) > div:nth-of-type(2) > span"
    ),
    "Phone": (
        "> div:nth-of-type(4) > div:nth-of-type(2) > span"
    ),
}


def gather_profile_details_for(link, session, base_url):
    """
    Given a TARE URL, pull the following data about a child.

    Photos, Name, TareId, Age (to be converted to a birthdate), others
    """
    log.debug("Cloning child, contact, and fields objects")
    log.info("Only Child:\n%s" % link)
    # Data required to have for a child
    child_info = Child()
    contact_info = Contact()
    child_fields = list(child_info.get_variable_fields())
    contact_filds = list(contact_info.get_variable_fields())

    # "Import" the html into BeautifulSoup for easy traversal
    req = session.get(link)
    if "/Application/TARE/Home.aspx/Error" in req.url:
        raise Exception("TARE Server had an error for link: %s" % link)

    html_data = req.text

    souped = BeautifulSoup(html_data, 'lxml')
    with open("test.html", "wb") as t:
        t.write(souped.prettify().encode('utf8'))

    # Handle Special Cases
    selector = CHILD_SELECTORS.get("Child_s_Birthdate__c")
    child_info.update_fields({
        "Child_s_Birthdate__c": get_birthdate(souped, selector),
        "Link_to_Child_s_Page__c": link
    })

    try:
        child_fields.remove('Link_to_Child_s_Page__c')
        child_fields.remove('Child_s_Birthdate__c')
    except ValueError:
        pass

    log.debug("Begin Child Fields")
    for field in child_fields:
        selector = CHILD_SELECTORS.get(field)
        if not selector:
            log.info("%s not yet supported" % field)
            continue
        elif type(selector) is list:
            info = ""
            for s in selector:
                x = souped.select_one(s)
                if x:
                    info += u"%s" % x.text
        else:
            selected = souped.select_one(selector)
            if selected:
                info = unicode(
                    selected.text.strip()
                )
        log.debug("Field: %s, Info: %s" % (field, info))
        child_info.update_field(field, info)

    log.debug("Begin Contact Fields")
    small_soup = souped.select(CONTACT_BASE)[0]
    for field in contact_filds:
        selector = CONTACT_SELECTORS.get(field)
        if not selector:
            log.info("%s not yet supported" % field)
            continue
        else:
            selected = small_soup.select_one(selector)
            if selected:
                info = unicode(
                    selected.string.strip()
                )

        if field == "Name":
            name_split = info.split(' ')
            contact_info.update_fields({
                "FirstName": name_split[0],
                "LastName": name_split[-1]
            })
        elif field == "Phone":
            contact_info.update_field("Phone", validators["phone"](info))
        elif field == "MailingStreet":
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
        else:
            contact_info.update_field(field, info)

    attachments = []

    # Get the profile picture attachment
    profile_image_data = get_pictures_encoded(
        session, souped, CHILD_SELECTORS.get("profile_picture"), base_url, True
    )

    # Create attachments for the profile and thumbnail pictures
    for img in profile_image_data:
        for k, v in img.iteritems():
            suffix = "_%s.jpg" % k
            name = "%s%s" % (child_info.get_field("Name"), suffix)
            attachments.append(create_attachment(v, name))

    # Get other images
    other_images = get_pictures_encoded(
        session, souped, CHILD_SELECTORS.get("other_pictures"), base_url, False
    )

    # Create attachments of the other images and append a number to the name
    for i, img in enumerate(other_images):
        suffix = "_%d.jpg" % i
        name = "%s%s" % (child_info.get_field("Name"), suffix)
        # For non-Profile pictures, we just want the full image.
        # thumbnail is None anyway
        attachments.append(create_attachment(img.get("full"), name))

    child = {
        "child_info": child_info,
        "attachments": attachments,
        'contact_info': contact_info,
    }

    log.debug(
        "Child data successfully generated. Returning `%s`" %
        child["child_info"].get_field("Name")
    )
    return child
