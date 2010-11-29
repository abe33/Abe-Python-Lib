# -*- coding: utf-8 -*-
import re

OBJECTS_LIST_SEPARATOR = "\n"
OBJECTS_TYPE_RE = re.compile("^[^{]+")

MISSION_NOTIFICATION_TOKEN = "[[mission_notification_token]]"
MISSION_MIDDLEWARE_INSTANCE= None
