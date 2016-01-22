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

"""Utility functions useful to TARE."""

from base64 import b64encode
from datetime import date
from math import floor
from cStringIO import StringIO

from PIL import Image
from dateutil.relativedelta import relativedelta
from twisted.logger import Logger

from data_types import Attachment

log = Logger()


def parse_name(name_copy):
    """
    Parse first and last name.

    Check for a comma.
    """
    info = {
        "FirstName": None,
        "LastName": None
    }

    if "," in name_copy:
        _split = name_copy.split(",")
        info["FirstName"] = _split[1].split(" ")[0]
        info["LastName"] = _split[0]
    else:
        _split = name_copy.split(" ")
        info["FirstName"] = _split[0]
        info["LastName"] = " ".join(_split[1:])

    return info


def get_birthdate(souped, selector):
    """
    Calculatie child's birthdate.

    Pull the child's age, calculaties a birthdate with a six month accuracy.
    """
    # Special case for the binthdate
    age = int(souped.select(selector)[0].string.strip())
    log.debug("get_birthdate> age: %s" % age)
    today = date.today()
    six_months = relativedelta(months=6)
    bday = today - six_months
    info = unicode(bday.isoformat())
    return info


def generate_thumbnail(img_data):
    """Create a thumbnail with height 230px."""
    # Create thumbnail of the image using the Pillow package
    img = Image.open(StringIO(img_data))
    # Width and height to scale for the thumbnail
    i_width, i_height = img.size
    ratio = i_height / 230.0
    new_width = floor(i_width * ratio)
    new_height = 230.0

    # Resize the image
    thumbnail = img.resize((int(new_width), int(new_height)), Image.ANTIALIAS)
    in_memory_save = StringIO()
    thumbnail.save(in_memory_save, format="jpeg")
    thumbnail_b64 = b64encode(in_memory_save.getvalue())

    return thumbnail_b64


def get_pictures_encoded(session, html, selector, url, thumbnail=False):
    """Pull Profile picture and create thumbnail of it. Height of 230px."""
    data = []

    for img in html.select(selector):
        img_url = "%s%s" % (url, img.get("src"))
        img_data = session.get(img_url).content
        img_data_b64 = b64encode(img_data)

        # Thumbnail
        thumbnail_b64 = None if not thumbnail else generate_thumbnail(img_data)

        data.append({'full': img_data_b64, 'thumbnail': thumbnail_b64})

    # Return a dictionary containing the base64 encoded versions
    # of the thumbnail and the full image
    return data


def create_attachment(b64_data, name):
    """Create a Salesforce attachment object from a jpeg."""
    attachment = Attachment()
    attachment.update_fields({
        "Body": b64_data,
        "Name": name,
    })

    return attachment
