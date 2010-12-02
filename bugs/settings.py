# -*- coding: utf-8 -*-
from django.conf import settings

PAIN_PREFIX = getattr( settings, "PAIN_PREFIX",'.pain%s')
PAIN_BLOCK_PREFIX = getattr( settings, "PAIN_BLOCK_PREFIX",'.block')
PAIN_AFFECTED_PREFIX = getattr( settings, "PAIN_AFFECTED_PREFIX",'.affected')
PAIN_DONE_PREFIX = getattr( settings, "PAIN_DONE_PREFIX",'.done')

PAIN_COLOR = getattr( settings, "PAIN_COLOR",0x999999)
PAIN_BLOCK_COLOR = getattr( settings, "PAIN_BLOCK_COLOR",0xff6666)
PAIN_AFFECTED_COLOR = getattr( settings, "PAIN_AFFECTED_COLOR",0x66aaFF)
PAIN_DONE_COLOR = getattr( settings, "PAIN_DONE_COLOR", 0x66ff66)

CURRENT_MILESTONE = getattr( settings, "CURRENT_MILESTONE",  1)
