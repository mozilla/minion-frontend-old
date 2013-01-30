# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from django.utils.html import escapejs
from jingo import register

#
# This is the place to register Django template filters with the jingo
# template engine. If you see a filter in the Django documentation [1]
# that is not included with Jingo then you can simply import and
# register it here as shown below.
#
# [1] https://docs.djangoproject.com/en/dev/ref/templates/builtins/
#

register.filter(escapejs)
