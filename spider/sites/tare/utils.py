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
        fname = _split[1].strip()
        if " " in fname:
            info["FirstName"] = fname.split(" ")[0].strip()
        else:
            info["FirstName"] = _split[1].strip()
        info["LastName"] = _split[0].strip()
    else:
        _split = name_copy.split(" ")
        info["FirstName"] = _split[0].strip()
        info["LastName"] = " ".join(_split[1:])

    return info


def get_birthdate(age):
    """
    Calculatie child's birthdate.

    Pull the child's age, calculaties a birthdate with a six month accuracy.
    """
    age = int(age)
    today = date.today()
    six_months = relativedelta(years=age, months=6)
    bday = today - six_months
    info = unicode(bday.isoformat())
    return info


def generate_thumbnail(img_data):
    """Create a thumbnail with height 230px."""
    data = {"data": None, "length": None}
    try:
        # Create thumbnail of the image using the Pillow package
        img = Image.open(StringIO(img_data))
        # Width and height to scale for the thumbnail
        i_width, i_height = img.size

        # Skip really tiny images
        if i_width <= 10 and i_height <= 10:
            return dict({"data": None, "length": None})

        new_width = (230 * i_width) / i_height
        new_height = 230.0

        # Resize the image
        thumbnail = img.resize(
            (int(new_width), int(new_height)), Image.ANTIALIAS
        )
        in_memory_save = StringIO()
        thumbnail.save(in_memory_save, format="jpeg")
        in_mem_val = in_memory_save.getvalue()
        thumbnail_b64 = b64encode(in_mem_val)
        data.update({
            "data": thumbnail_b64,
            "length": len(in_mem_val)
        })
    except Exception, e:
        log.debug("%s" % e)

    return data


def scale_portrait(img_data):
    """Restrict the image size to a max of 1024x768 keeping original ratio."""
    try:
        data = {}
        # Scale the portrait to a standard size
        img = Image.open(StringIO(img_data))
        in_memory_save = StringIO()
        # Width and height to scale for the portrait
        i_width, i_height = img.size

        # Skip image if it's tiny
        if i_width <= 10 and i_height <= 10:
            return None

        # Do not rescale if smaller than 1024x768
        if i_width < 1024 and i_height < 768:
            img.save(in_memory_save, format="jpeg")
            in_mem_val = in_memory_save.getvalue()
            data["length"] = len(in_mem_val)
            data["data"] = b64encode(in_mem_val)
            return data

        # If wider than tall
        if i_width >= i_height:
            new_width = 768
            new_height = (768 * i_height) / i_width
        # if taller than wide
        else:
            new_height = 1024
            new_width = (1024 * i_width) / i_height

        scaled = img.resize((int(new_width), int(new_height)), Image.ANTIALIAS)
        scaled.save(in_memory_save, format="jpeg")
        in_mem_val = in_memory_save.getvalue()

        data["length"] = len(in_mem_val)
        data["data"] = b64encode(in_mem_val)
        return data
    except Exception, e:
        log.debug("%s" % e)
        return None


def get_pictures_encoded(session, base_url, urls, thumbnail=False):
    """Pull Profile picture and create thumbnail of it. Height of 230px."""
    data = []

    for url in urls:
        img_url = "%s%s" % (base_url, url)
        img_data = session.get(img_url).content
        img_data_b64 = scale_portrait(img_data)

        # Thumbnail
        thumbnail_b64 = None if not thumbnail else generate_thumbnail(img_data)

        data.append({
            'full': img_data_b64, 'thumbnail': thumbnail_b64
        })

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
