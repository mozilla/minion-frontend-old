# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from django.contrib.auth.models import User
from django.db import models

class Scan(models.Model):
    scan_id = models.CharField(max_length=100, primary_key = True)
    scan_creator = models.ForeignKey(User)
    scan_date = models.DateTimeField(auto_now_add=True)
    scan_url = models.URLField()
    scan_plan = models.CharField(max_length=100)
