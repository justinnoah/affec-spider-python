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

"""SitePlugin module for Tare."""

import string

from bs4 import BeautifulSoup
import requests
from requests.exceptions import HTTPError
from twisted.logger import Logger
from zope.interface import implements
from zope.interface.exceptions import DoesNotImplement

from data_types import AllChildren
from iplugin import SitePlugin
from . import only_child_parser, sibling_group_parser


class TareSite(object):
    """
    Site plugin for Tare.

    Plugin using interface SitePlugin (found in iplugin.py).
    """

    implements(SitePlugin)

    base_url = "https://www.dfps.state.tx.us"
    settings_name = "Tare"
    log = Logger()

    # The form data that the submission requires for a child search
    search_data = {
        "Name": "",
        "Age": "",
        "Behavioral": "",
        "Developmental": "",
        "Emotional": "",
        "Gender": "",
        "TAREId": "",
        "RiskFactors": "",
        "Physical": "",
        "Learning": "",
        "Medical": "",
        "GroupType": "",
        "Region": "",
        "Ethnicity": "",
        "AA": "false",
        "AN": "false",
        "BK": "false",
        "DC": "false",
        "HP": "false",
        "UD": "false",
        "WT": "false",
    }

    def __init__(self, config):
        """Fire it up."""
        self.log.debug("TARE plugin logging in.")
        # Verify requirements
        self.config = self._check_config(config)
        # Initialize our session, this does cookies and things
        self.session = requests.Session()
        # Login!
        res = self.session.post(
            "%s/Application/TARE/Account.aspx/Logon" % self.base_url,
            data={
                'UserName': self.config['username'],
                'Password': self.config["password"],
            }
        )

        if "Application/TARE/Account.aspx/LogOn" in res.url:
            raise ValueError("TARE: Invalid Login Credentials")

        self.log.debug("TARE logged in.")

    def _check_config(self, config):
        """Verify a user/pass for TARE is in the config."""
        required = ['username', 'password']
        for key in required:
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

    def get_all(self):
        """
        Return AllChildren on the tare website.

        @rtype: AllChildren
        @return: Returns an AllChildren object of all children and sibling
        groups found on the Tare website.
        """
        # To gather all Children and Sibling Groups from TARE,
        # a search of all names is required. So, from aa to zz,
        # all will be searched.
        first_name_starts = [
            "%s%s" % (x, y)
            for x in string.ascii_lowercase for y in string.ascii_lowercase
        ]
        # first_name_starts = ['ab']
        all_children = AllChildren()
        for fname in first_name_starts:
            results = self.search_profiles(fname)
            all_children.merge(results)

        return all_children

    def search_profiles(self, search="aa"):
        """
        TARE decided to revamp their search page.
        Thankfully it is *much* easier to parse.

        @type search: String
        @param search: Name parameter for search

        @rtrype: AllChildren
        @return: An AllChildren object containing the parsed data of the
        children and sibling groups found by the search
        """
        search_post_url = (
            "%s/Application/TARE/Search.aspx/NonMatchingSearchResults" %
            self.base_url
        )

        # Update POST data with search criteria
        self.search_data["Name"] = search

        self.log.info("Searching for children starting with %s" % search)
        req = self.session.post(search_post_url, self.search_data)

        try:
            req.raise_for_status()
        except HTTPError, e:
            self.log.error("Failed to search for: %s" % search)
            self.log.failure(e)
            return []

        # Get the results section of the page
        html = req.text
        soup = BeautifulSoup(html, "lxml")
        search_results = soup.select_one("div#results > ul")

        # Grab each result
        results_soup = BeautifulSoup(str(search_results), "lxml")
        results = results_soup.select("a.listLink")

        # The children and sibling groups to return
        all_children = AllChildren()

        # Iterate through the results and grab the link and name
        for result in results:
            # Shorten lines up a bit
            link = "%s%s" % (self.base_url, result.get('href'))

            # If the link contains Child.aspx, it's an only child
            if "Child.aspx" in link:
                child = only_child_parser.gather_profile_details_for(
                    link, self.session, self.base_url
                )
                all_children.add_child(child)
            # If the link contains Group.aspx, it's a sibling group
            elif "Group.aspx" in link:
                group = sibling_group_parser.gather_profile_details_for(
                    link, self.session, self.base_url
                )
                all_children.add_sibling_group(group)

        # Returned the parsed data
        return all_children

    def search_profiles_old_template(self, search="ad"):
        """Search TARE for children with names starting with `search`."""
        post_url = (
            "%s/Application/TARE/Search.aspx/NonMatchingSearchResults" %
            self.base_url
        )

        # Update POST data with search criteria
        self.search_data["Name"] = search

        self.log.info("Searching for children starting with %s" % search)
        req = self.session.post(post_url, self.search_data)

        try:
            req.raise_for_status()
        except HTTPError, e:
            self.log.error("Failed to search for: %s" % search)
            self.log.failure(e)
            return []

        html = req.text
        link_objs = self.parse_search_results(html)
        solo_links = []
        self.log.debug("Adding links of only child profiles to be scraped")
        for only in link_objs.get('only'):
            solo_links.append("%s%s" % (
                self.base_url,
                only.get('href')
            ))
        self.log.info("Found %s 'only childs'" % len(solo_links))
        # Gathering Only child, children
        solo_children = []
        self.log.debug("Begin Scraping of only child profiles")
        for link in solo_links:
            child = only_child_parser.gather_profile_details_for(
                link, self.session, self.base_url
            )
            solo_children.append(child)
        #    except Exception, e:
        #        print("An issue occured with: %s" % link)
        #        print("%s" % e)
        #        continue

        sibling_links = []
        for siblings in link_objs.get('siblings'):
            sibling_links.append("%s%s" % (
                self.base_url,
                siblings.get('href')
            ))

        self.log.info("Found %s 'sibling groups'" % len(sibling_links))
        sibling_children = []
        for link in sibling_links:
            siblings = sibling_group_parser.gather_profile_details_for(
                link, self.session, self.base_url
            )
            sibling_children.append(siblings)
        #    except Exception, e:
        #        print("An issue occured with: %s" % link)
        #        print("%s" % e)
        #        continue

        all_children = AllChildren()
        for child in solo_children:
            all_children.add_child(child)
        for group in sibling_children:
            all_children.add_sibling_group(group)

        return all_children

    def parse_search_results(self, html):
        """
        Parse links from a search.

        @type html: String
        @param html: Raw HTML from the TARE site.

        @rtype:
        """
        children_tags = {
            'only': [],
            'siblings': [],
        }

        # Beautify the html
        bs = BeautifulSoup(html, 'lxml')

        # Get all the links of 'Child Profiles' and 'Sibiling Profiles'
        children = bs.table.find_all("a", text="Child Profile")
        if children:
            children_tags['only'] = children
        sibling_groups = bs.table.find_all("a", text="Sibling Profile")
        if sibling_groups:
            children_tags['siblings'] = sibling_groups

        return children_tags

    def get_child_by_id(self, cid):
        """Tare definition of SitePlugin method."""
        raise DoesNotImplement("Skeleton only.")

    def get_sibling_group_by_id(self, sgid):
        """Tare definition of SitePlugin method."""
        raise DoesNotImplement("Skeleton only.")
