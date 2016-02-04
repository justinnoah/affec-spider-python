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

from bs4 import BeautifulSoup
from twisted.logger import Logger

from data_types import Contact, SiblingGroup
from only_child_parser import gather_profile_details_for as gather_child
from utils import parse_name
from validators import valid_email, valid_phone

log = Logger()

ALL_CHILDREN_SELECTOR = "div#pageContent > div > div:nth-of-type(5) > div"
CASE_WORKER_SELECTOR = "div#pageContent > div > div:nth-of-type(6)"

# These are the magic phrases that get the data from a TARE profile page
# They also happen to represent some, if not all of the fields to be updated
CHILD_SELECTORS = {
    "Name": (
        "div > div:nth-of-type(2) > a"
    ),
    # TARE Id
    "Case_Number__c": (
        "div#pageContent > div > div:nth-of-type(6) > div:nth-of-type(2)"
    ),
    "Children_s_Bio__c": [
        "> div:nth-of-type(8)",
        "> div:nth-of-type(9)",
        "> div:nth-of-type(10)",
        "> div:nth-of-type(11)",
        "> div:nth-of-type(12)",
        "> div:nth-of-type(13)",
    ],
}

CONTACT_SELECTORS = {
    "FirstName": "div:nth-of-type(4)",
    "LastName": "div:nth-of-type(4)",
    "Phone": "div:nth-of-type(5)",
    "Email": "div:nth-of-type(6)",
}


def parse_children_in_group(soup, session, base_url):
    """Parse each child's name out of the sibling group."""
    children = []
    children_to_parse = soup.select(ALL_CHILDREN_SELECTOR)
    for i, child_link in enumerate(children_to_parse):
        small_soup = BeautifulSoup(str(child_link), "lxml")
        _sub_link = small_soup.select_one(
            CHILD_SELECTORS.get("Name")
        )
        if _sub_link:
            sub_link = _sub_link.get("href")
            link = "%s%s" % (base_url, sub_link)
            child = gather_child(link, session, base_url)
            log.debug("link: %s" % link)
            children.append(child)

    return children


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


def gather_profile_details_for(link, session, base_url):
    """
    Given a TARE URL, pull the following data about a child.

    Photos, Name, TareId, Age (to be converted to a birthdate), others
    """
    log.debug("Cloning siblings, contact, and fields objects")
    log.info("Sibling Group:\n%s" % link)
    # Data required to have for a sibling group
    sibling_group = SiblingGroup()
    contact_info = Contact()
    fields = list(sibling_group.get_variable_fields())

    # "Import" the html into BeautifulSoup for easy traversal
    req = session.get(link)
    try:
        if "/Application/TARE/Home.aspx/Error" in req.url:
            raise Exception("TARE Server had an error for link: %s" % link)
        elif link != req.url:
            raise Exception("TARE redirected away from the url %s" % link)
    except Exception, e:
        log.debug("%s" % e)

    html_data = req.text
    souped = BeautifulSoup(html_data, 'lxml')

    log.debug("Parsing Caseworker data for Sibling Group")
    cw_soup = souped.find(
        "span", string="TARE Coordinator"
    ).parent.parent.parent
    # Parse Case Worker data for the group
    cw_data = parse_case_worker_details(cw_soup)
    contact_info.update_fields(cw_data)

    log.info("Begin parsing child links from: %s" % link)
    # Parse children
    children_in_group = parse_children_in_group(souped, session, base_url)
    log.info("Done with: %s" % link)
    names = [
        child.get_field("Name") for child in children_in_group
    ]
    sibling_group.update_field("Name", ", ".join(names))
    fields.remove("Name")

    divs = cw_soup.select("> div")
    tare_id = divs[1].text.strip()
    region = divs[3].text.strip()
    sibling_group.update_field("Case_Number__c", tare_id)
    fields.remove("Case_Number__c")
    sibling_group.update_field("Children_s_Webpage__c", link)

    for field in fields:
        selector = CHILD_SELECTORS.get(field)
        if field == "Children_s_Bio__c":
            # Start with a blank bio
            bio = ""
            headers = souped.find_all("div.groupHeader")
            bodies = souped.find_all("div.groupBody")
            zipped = zip(headers, bodies)

            # Add all the headers and bodies to the bio
            for header, body in zipped:
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
        else:
            log.info("%s not yet supported for Siblings" % field)

    for child in children_in_group:
        sibling_group.add_child(child)

    sibling_group.update_field('Caseworker__c', contact_info)

    log.debug(
        "Child data successfully generated. Returning `%s`" %
        sibling_group.get_field("Name")
    )

    return sibling_group
