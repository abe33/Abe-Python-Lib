# -*- coding: utf-8 -*-
from django.conf import settings

import re
import operator

OBJECTS_LIST_SEPARATOR =  getattr( settings, "OBJECTS_LIST_SEPARATOR","\n")
OBJECTS_TYPE_RE = getattr( settings, "OBJECTS_TYPE_RE", re.compile("^(([^{]+)\.)?([^{]+)") )

MISSION_NOTIFICATION_TOKEN = getattr( settings, "MISSION_NOTIFICATION_TOKEN", "[[mission_notification_token]]")

MISSION_MIDDLEWARE_INSTANCE=  None

MISSION_MIDDLEWARE_DEBUG = getattr( settings, "MISSION_MIDDLEWARE_DEBUG", True )

MISSION_DESCRIPTOR_CLASS = getattr( settings, "MISSION_DESCRIPTOR_CLASS", "abe.missions.models.MissionDescriptor" )

MISSION_RESULTS_PROCESSOR = getattr( settings, "MISSION_RESULTS_PROCESSOR", "abe.missions.middleware.default_mission_results_processor" )
MISSION_RESPONSE_PROCESSOR = getattr( settings, "MISSION_RESPONSE_PROCESSOR", "abe.missions.middleware.default_mission_response_processor" )
MISSION_CONTEXT_PROCESSOR = getattr( settings, "MISSION_CONTEXT_PROCESSOR", "abe.missions.middleware.default_mission_context_processor" )

MISSION_TRIGGERS_LIST =  getattr( settings, "MISSION_TRIGGERS_LIST", "" )

MISSION_CONDITIONS_LIST = getattr( settings, "MISSION_CONDITIONS_LIST", (
																														 "abe.missions.conditions.MissionCondition",
																														 
																														 "abe.missions.conditions.TimeBombCondition", 
																														 "abe.missions.conditions.TrueCondition", 
																														 "abe.missions.conditions.NumericComparisonCondition", 
																														 
																														 "abe.missions.conditions.MissionRequiredCondition",
																														 "abe.missions.conditions.MissionsDoneCountCondition",
																														 "abe.missions.conditions.MissionStartedSinceCondition", 
																														 
																														) )

MISSION_REWARDS_LIST = getattr( settings, "MISSION_REWARDS_LIST", (
																													"abe.missions.rewards.MissionReward",
																												))

COMPARISON_OPERATORS_MAP = getattr( settings, "COMPARISON_OPERATORS_MAP", {
																																	'==':operator.eq, 
																																	'!=':operator.ne, 
																																	'>=':operator.ge, 
																																	'>':operator.gt, 
																																	'<=':operator.le, 
																																	'<':operator.lt, 
																																} )


