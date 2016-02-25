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

"""Parse sibling group pages on TARE."""

import random

from bs4 import BeautifulSoup
from twisted.logger import Logger

from data_types import Contact, SiblingGroup
from helpers import return_type
from only_child_parser import gather_profile_details_for as gather_child
from utils import create_attachment, get_pictures_encoded, parse_name
from validators import valid_email, valid_phone

log = Logger()

ALL_CHILDREN_SELECTOR = "div#pageContent > div > div.galleryImage"
CASE_WORKER_SELECTOR = "div#pageContent > div > div:nth-of-type(6)"

# These are the magic phrases that get the data from a TARE profile page
# They also happen to represent some, if not all of the fields to be updated
SGROUP_SELECTORS = {
    "Name": (
        "div > div:nth-of-type(2) > a"
    ),
    # TARE Id
    "Case_Number__c": (
        "div#pageContent > div > div:nth-of-type(6) > div:nth-of-type(2)"
    ),
    "Children_s_Bio__c": [
        "div#pageContent > div > div:nth-of-type(8)",
        "div#pageContent > div > div:nth-of-type(9)",
        "div#pageContent > div > div:nth-of-type(10)",
        "div#pageContent > div > div:nth-of-type(11)",
        "div#pageContent > div > div:nth-of-type(12)",
        "div#pageContent > div > div:nth-of-type(13)",
    ],
}

CONTACT_SELECTORS = {
    "FirstName": "div:nth-of-type(4)",
    "LastName": "div:nth-of-type(4)",
    "Phone": "div:nth-of-type(5)",
    "Email": "div:nth-of-type(6)",
}

ATTACHMENT_SELECTORS = {
    "profile_picture": "div#pageContent > div > div > a > img",
    "other_pictures": "div.galleryImage > a > img"

}


@return_type(list)
def parse_children_in_group(soup, session, base_url):
    """Parse each child's name out of the sibling group."""
    children = []
    children_to_parse = soup.select_one(
        ALL_CHILDREN_SELECTOR
    ).find_next_sibling()
    links = children_to_parse.select("a")
    for link in links:
        sub_url = link.get("href")
        if "TARE/Child" in sub_url:
            full_link = "%s%s" % (base_url, sub_url)
            child = gather_child(full_link, session, base_url)
            children.append(child)

    log.debug("RETURNING %s child(ren)" % len(children))
    return children


def parse_attachments(sgname, session, souped, base_url):
    """
    Parse attachments and add them to the child object.

    @type sgname: String
    @param child: SiblingGroup name.

    @type session: requests session
    @param session: The "browser" session that has us logged into TARE.

    @type souped: BeautifulSoup data
    @param soup: Chunk of a webpage containing the contact info.

    @type base_url: String
    @param base_url: The beginning of all TARE urls.
    """
    sgname = sgname.replace(", ", "")

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
                urls.append(tag.src)

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
        for k, v in img.iteritems():
            name = "%s-%s.jpg" % (
                sgname, str(random.randint(100, 999))
            )
            attachments_returned.append((create_attachment(v, name)))

    # Create attachments of all other images and append a number to the name
    for i, img in enumerate(other_images):
        # For non-Profile pictures, we just want the full image.
        # thumbnail is None anyway
        name = "%s-%s.jpg" % (
            sgname, str(random.randint(100, 999))
        )
        attachments_returned.append((create_attachment(img.get("full"), name)))

    return list(attachments_returned)


@return_type(dict)
def parse_case_worker_details(souped):
        """
        Using the CASE_WORKER_SELECTOR grab essential data.

        This includes:
        TareId, Name, Email, Address, Region, County
        """
        cw_data = {}

        divs = iter(souped.select("> div"))
        for div in divs:
            if "TARE Coord" in div.text:
                cw_data.update(
                    parse_name(
                        div.select_one("div:nth-of-type(2)").text.strip()
                    )
                )
            elif "Phone" in div.text:
                phone = valid_phone(
                    div.select_one("div:nth-of-type(2)").text.strip()
                )
                if phone:
                    cw_data["Phone"] = phone
            elif "Email" in div.text:
                email = valid_email(
                    div.select_one("div:nth-of-type(2)").text.strip()
                )
                if email:
                    cw_data["Email"] = email

        return cw_data


@return_type(SiblingGroup)
def gather_profile_details_for(link, session, base_url):
    """
    Given a TARE URL, pull the following data about a child.

    Photos, Name, TareId, Age (to be converted to a birthdate), others
    """
    log.debug("Sibling Group:\n%s" % link)
    # Data required to have for a sibling group
    sibling_group = SiblingGroup()
    contact_info = Contact()
    fields = list(sibling_group.get_variable_fields())

    # "Import" the html into BeautifulSoup for easy traversal
    req = session.get(link)
    if "/Application/TARE/Home.aspx/Error" in req.url:
        raise ValueError("TARE Server had an error for link: %s" % link)
    elif "/Application/TARE/Home.aspx/Default" in req.url:
        raise ValueError("TARE redirected away from the url %s" % link)

    html_data = req.text
    souped = BeautifulSoup(html_data, 'lxml')

    log.debug("Parsing Caseworker data for Sibling Group")
    cw_soup = souped.find(
        "span", string="TARE Coordinator"
    ).parent.parent.parent
    # Parse Case Worker data for the group
    cw_data = parse_case_worker_details(cw_soup)
    contact_info.update_fields(cw_data)
    sibling_group.update_field('Caseworker__c', contact_info)

    log.info("Begin parsing child links from:\n%s" % link)
    # Parse children
    children_in_group = parse_children_in_group(souped, session, base_url)
    names = [
        child.get_field("Name") for child in children_in_group
    ]
    log.debug("Children: %s" % names)
    sibling_group.update_field("Name", ", ".join(names))
    log.debug("SGroup Name: %s" % sibling_group.get_field("Name"))
    fields.remove("Name")

    # Add children to the SiblingGroup object
    for child in children_in_group:
        sibling_group.add_child(child)

    log.debug("Added children to the SiblingGroup object")

    try:
        divs = cw_soup.select("> div")
        tare_id = divs[1].text.strip()
        region = divs[3].text.strip()
        sibling_group.update_fields({
            "Case_Number__c": tare_id,
            "Children_s_Webpage__c": link,
            "District__c": "Region: %s" % region,
        })
        fields.remove("Case_Number__c")
        fields.remove("Children_s_Webpage__c")
        fields.remove("District__c")
    except Exception, e:
        log.debug("%s" % e)

    log.debug("Begin SGroup Field parsing")
    for field in fields:
        selector = SGROUP_SELECTORS.get(field)
        if field == "Children_s_Bio__c":
            # Start with a blank bio
            bio = ""

            headers = souped.find_all("div.groupHeader")
            bodies = souped.find_all("div.groupBody")

            # Add all the headers and bodies to the bio
            for header, body in zip(headers, bodies):
                bio += "%s\n%s\n\n" % (header.text.strip(), body.text.strip())

            # Update siblings' bio
            sibling_group.update_field(field, bio.strip())
        elif selector:
            log.debug("selector: %s" % selector)
            _selected = souped.select_one(selector)
            sibling_group.update_field(
                field,
                _selected.text.strip() if _selected else ""
            )

    log.debug("SiblingGroup ATTACHMENTS")
    # Add attachments / images
    attachments = parse_attachments(
        sibling_group.get_field("Name"), session, souped, base_url
    )
    for attachment in attachments:
        sibling_group.add_attachment(attachment)

    log.debug(
        "%s have no value." %
        ", " .join(k for k, v in sibling_group.as_dict().items() if not v)
    )

    log.debug(
        "SiblingGroup data successfully generated. Returning `%s`" %
        sibling_group.get_field("Name")
    )

    return sibling_group
