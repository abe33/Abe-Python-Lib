# -*- coding: utf-8 -*-
from django.contrib.admin.filterspecs import FilterSpec
from django.contrib import admin
from django.conf import settings as locsettings
from django.utils.translation import ugettext as _

from abe.missions.models import *

class MissionAdmin(admin.ModelAdmin):
	list_display=("__unicode__", "enabled",  )
	list_display_links = ('__unicode__', )
	fieldsets = [
		( 'General',	{'fields': ['name', 'enabled', 'auto_activate'] }),
		( 'Conditions', {'fields':[ 'pre_conditions', 'conditions', 'validity_conditions' ] }), 
		( 'Rewards',	{'fields': ['rewards', 'failure_rewards'] }),
	]

class MissionProfileAdmin(admin.ModelAdmin):
	list_display=("__unicode__", )
	list_display_links = ('__unicode__', )
	fieldsets = [
		( 'User',			{'fields': ['user', ] }),
		( 'Missions', 		{'fields':[ 'missions_done', 'missions_active', 'missions_available', 'missions_elligible', ] })
	]

class MissionDescriptorAdmin( admin.ModelAdmin ):
	list_display=("mission", )
	list_display_links = ('mission', )
	fieldsets = [
		( 'General',	{'fields': ['mission','description' ] }),
	]

admin.site.register(Mission, MissionAdmin )
admin.site.register(MissionProfile, MissionProfileAdmin )
admin.site.register(MissionDescriptor, MissionDescriptorAdmin )
