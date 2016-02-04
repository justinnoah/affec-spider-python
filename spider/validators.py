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


"""Data validators."""

import re

from twisted.logger import Logger

log = Logger()


def is_valid(a):
    """Only return valid."""
    return True


def valid_phone(number):
    """
    Simple US phone number validator.

    Valid number must be 7, 10, or 11 numbers depending on country and
    area code inclusion.

    To validate, all non-integers are stripped out and length is measured.
    If a number happens to have a length of 11, the first number must be a 1
    """
    # Initial state of False
    non_digit = re.compile("\D")
    cleaned = non_digit.sub('', number)

    length = len(cleaned)
    if length == 11 and cleaned.startswith("1"):
        return cleaned
    elif length in [10, 7]:
        return cleaned

    # Return the state of validity
    return None


def valid_address(addr):
    """Address validator/parser."""
    # Sanitize-ish
    multispace = re.compile("\s+")
    addr = multispace.sub(" ", addr)

    addr_split = [
        x for x in addr.title().split(" ") if x not in ["", '', None]
    ]

    sane_addr = []
    for w in addr_split:
        if len(w) == 2:
            w = w.upper()

        if w not in ["N", "S", "E", "W", "NW", "NE", "SW", "SE"]:
            sane_addr.append(w)
        else:
            sane_addr.append(w)

    addr = " ".join(sane_addr)

    log.debug("Address: %s" % addr)

    from pyparsing import (
        oneOf, CaselessLiteral, Optional, originalTextFor, Combine, Word, nums,
        alphas, White, FollowedBy, MatchFirst, Keyword, OneOrMore, Regex,
        alphanums, Suppress
    )

    # define number as a set of words
    units = oneOf(
        "Zero One Two Three Four Five Six Seven Eight Nine Ten "
        "Eleven Twelve Thirteen Fourteen Fifteen Sixteen Seventeen "
        "Eighteen Nineteen",
        caseless=True
    )
    tens = oneOf(
        "Ten Twenty Thirty Forty Fourty Fifty Sixty Seventy Eighty Ninety",
        caseless=True
    )
    hundred = CaselessLiteral("Hundred")
    thousand = CaselessLiteral("Thousand")
    OPT_DASH = Optional("-")
    numberword = (((
        units + OPT_DASH + Optional(thousand) + OPT_DASH +
        Optional(units + OPT_DASH + hundred) + OPT_DASH + Optional(tens)
    ) ^ tens) + OPT_DASH + Optional(units))

    # number can be any of the forms 123, 21B, 222-A or 23 1/2
    housenumber = originalTextFor(
        numberword | Combine(
            Word(nums) +
            Optional(OPT_DASH + oneOf(list(alphas))+FollowedBy(White()))
        ) + Optional(OPT_DASH + "1/2")
    )
    numberSuffix = oneOf("st th nd rd", caseless=True).setName("numberSuffix")
    streetnumber = originalTextFor(
        Word(nums) + Optional(OPT_DASH + "1/2") + Optional(numberSuffix)
    )

    # just a basic word of alpha characters, Maple, Main, etc.
    name = ~numberSuffix + Word(alphas)

    # types of streets - extend as desired
    type_ = Combine(MatchFirst(map(
        Keyword,
        "Street St ST Boulevard Blvd Lane Ln LN Road Rd RD Avenue Ave AVE "
        " Circle Cir Cove Cv Drive Dr DR Parkway Pkwy PKWY Court Ct Square Sq "
        "Loop Lp LP".split()
    )) + Optional(".").suppress())

    # street name
    nsew = Combine(
        oneOf("N S E W North South East West NW NE SW SE", caseless=True) +
        Optional(".")
    )
    streetName = (
        Combine(
            Optional(nsew) + streetnumber + Optional("1/2") +
            Optional(numberSuffix), joinString=" ", adjacent=False
        ) ^ Combine(
            ~numberSuffix + OneOrMore(~type_ + Combine(
                Word(alphas) + Optional(".") + Optional(",")
            )),
            joinString=" ",
            adjacent=False
        ) ^ Combine("Avenue" + Word(alphas), joinString=" ", adjacent=False)
    ).setName("streetName")

    # PO Box handling
    acronym = lambda s: Regex(r"\.?\s*".join(s)+r"\.?")
    poBoxRef = (
        (acronym("PO") | acronym("APO") | acronym("AFP")) +
        Optional(CaselessLiteral("BOX"))
    ) + Word(alphanums)("boxnumber")

    # basic street address
    streetReference = \
        streetName.setResultsName("name") + \
        Optional(type_).setResultsName("type")
    direct = housenumber.setResultsName("number") + streetReference
    intersection = (
        streetReference.setResultsName("crossStreet") +
        ('@' | Keyword("and", caseless=True)) +
        streetReference.setResultsName("street")
    )
    suiteRef = (
        oneOf("Suite Ste Apt Apartment Room Rm #", caseless=True) +
        Optional(".") +
        Word(alphanums+'-')
    )
    streetAddress = ((
        poBoxRef("street")
        ^ (direct + Optional(suiteRef)).setResultsName("street")
        ^ (streetReference + Optional(suiteRef)).setResultsName("street")
        ^ intersection
    ) + Optional(Suppress(',') + Optional(Suppress('.')))
    ).setResultsName("streetAddress")

    city = (
        OneOrMore(Word(alphas)) + Optional(Suppress(","))
    ).setResultsName("city")

    states_abbr = oneOf(
        "AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN"
        "MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA"
        "WA WV WI WY",
        caseless=True
    )
    state_names = oneOf(
        ["Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado",
         "Connecticut", "Delaware", "Florida", "Georgia", "Hawaii", "Idaho",
         "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky", "Louisiana",
         "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota",
         "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada", "Ohio",
         "Oklahoma", "Oregon", "Pennsylvania", "Tennessee", "Texas", "Utah",
         "Vermont", "Virginia", "Washington", "Wisconsin", "Wyoming",
         "New Hampshire", "New Jersey", "New Mexico", "New York",
         "North Carolina", "North Dakota", "Rhode Island", "South Carolina",
         "South Dakota", "West Virginia"],
        caseless=True
    )
    state = (
        states_abbr.setResultsName("state")
        ^ state_names.setResultsName("state")
    ) + Optional(".") + Optional(",")
    zipCode = Word(nums).setResultsName("zip")

    us_address = (
        streetAddress + city + state + zipCode
    ).parseString(addr)
    log.debug("Parsed address: %s" % us_address)

    return us_address


def valid_email(email):
    """Placeholder until is_email is renamed."""
    return is_email(email)


def is_email(email):
    """
    Simple email validator.

    A valid email contains only one @ and the @ exists neither
    at the start nor the end of the string
    """
    # email length - 1 for indexing into the address
    email_len = len(email) - 1
    count = 0

    # At least 3 characters are required for a valid email
    if email_len < 3:
        return None

    # Short circuit on invalid findings
    for i, v in enumerate(email):
        if v == '@':
            count += 1
            if i in [0, email_len]:
                return None
            elif count > 1:
                return None

    # Upon searching the entire "email address" and the loop wasn't
    # short circuited, a valid email was passed
    return email


def is_age(age):
    """
    A simple age validator.

    Should be an integer, that is all
    """
    valid = False

    # Remove excess spaces
    age_stripped = age.strip()
    if str(int(age_stripped)) == age_stripped:
        valid = True

    return valid

# Plug and play validation
dict_of_validators = {
    "age": is_age,
    "email": is_email,
    "address": valid_address,
    "name": is_valid,
    "tareId": is_valid,
    "phone": is_valid,
}
