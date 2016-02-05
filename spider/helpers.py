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

"""Helper/Misc functions and the like to make life easier for everyone."""
from twisted.logger import Logger

log = Logger()


def return_type(t):
    """
    A decorator method to do runtime type verification for method returns.

    @type t: any
    @param t: The class of a type f should return
    """
    def wrap(f):
        def wrapped_f(*args, **kwargs):
            # Run the decorated method/function and get the returned object
            result = f(*args, **kwargs)

            # If not a list, do a regular type check
            if not isinstance(result, t):
                raise TypeError(
                    "%s returned a result with type %s and not %s." % (
                        f.__name__, type(result), t
                    )
                )
            return result
        return wrapped_f
    return wrap
