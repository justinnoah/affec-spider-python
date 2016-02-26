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

"""Delete salesforce objects."""
from configobj import ConfigObj, ConfigObjError
import os
import sys

from simple_salesforce import Salesforce
from salesforce_bulk_api import SalesforceBulkJob


def load_config(path="./config.ini"):
    """
    Load a config as a dict.

    @type path: String
    @param path: Path to config, default is in the same directory as this file

    @rtrype: ConfigObj
    @returns: the config
    """
    # OS agnostic path
    cfg_path = os.path.abspath(path)

    if not os.path.exists(cfg_path):
        raise Exception("%s does not exist!" % cfg_path)

    config = ConfigObj(cfg_path)

    # Verify the config has at least [sites], [databases], and at
    # least one plugin for each
    if 'database' not in config.sections:
        raise ConfigObjError("Section [database] is missing!")
    elif 'plugin' not in config['database']:
        raise ConfigObjError("Section [database] is missing a plugin!")

    return config['database']


def delete_em_all(w, sf):
    """Delete things in bulk."""
    all_of_them = sf.query_all("SELECT Id FROM %s" % w)
    print(
        "Deleting %s %s(s)" % (len(all_of_them["records"]), w)
    )
    ids = [[r["Id"]] for r in all_of_them["records"]]
    job = SalesforceBulkJob('delete', w)
    job.upload(["Id"], ids)
    # Simply waits for jobs to finish
    try:
        [res for res in job.results()]
    except:
        pass


def main(arg):
    """Delete all of a given type."""
    config = load_config()

    # bulk operations config
    os.environ['SALESFORCE_INSTANCE'] = ""
    os.environ['SALESFORCE_SANDBOX'] = config['Salesforce']['sandbox']
    os.environ['SALESFORCE_USERNAME'] = config['Salesforce']['username']
    os.environ['SALESFORCE_PASSWORD'] = config['Salesforce']['password']
    os.environ['SALESFORCE_SECURITY_TOKEN'] = config['Salesforce']['token']

    # Non-bulk operations config
    sf = Salesforce(
        username=config['Salesforce']['username'],
        password=config['Salesforce']['password'],
        security_token=config['Salesforce']['token'],
        sandbox=config['Salesforce']['sandbox'],
    )

    opts = {
        "siblings": "Sibling_Group__c",
        "children": "Children__c",
        "contacts": "Contact",
        "attachments": "Attachment",
    }
    if arg in opts:
        delete_em_all(opts[arg], sf)
    elif arg == "all":
        for k, v in opts.items():
            delete_em_all(v, sf)
    else:
        print("Unknown type: %s" % arg)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Incorrect number of arguments")
    else:
        main(sys.argv[1])
