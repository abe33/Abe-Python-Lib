# -*- coding: utf-8 -*-
from django.contrib.auth.decorators import *

from pyamf.remoting.gateway.django import DjangoGateway
import pyamf

from abe.missions.decorators import *
from abe.missions.models import *
from abe.missions.settings import *
from abe.utils import *

from datetime import *

def debug(request, *args ):
	print args
	for k in args :
		print type( k )
	return args

#@login_required
def missions_all ( request ):
	from abe.missions.settings import MISSION_MIDDLEWARE_INSTANCE as instance
	m = instance.missions_map
	d = {}
	for i in m : 
		d[ str(i) ] = m[i].to_vo()
	return d
	
#@login_required
def mission_type( request ):
	return {
					'type':"abe.missions.models.Mission",
					'help':Mission.__doc__, 
					'name':"String", 
					'active':"Boolean", 
					'conditions':"Array(abe.missions.conditions.MissionCondition)", 
					'pre_conditions':"Array(abe.missions.conditions.MissionCondition)", 
					'validity_conditions':"Array(abe.missions.conditions.MissionCondition)", 
					'rewards':"Array(abe.missions.rewards.MissionReward)"
				}
	
#@login_required
def missions_contitions_types( request ):
	conditions = MISSION_CONDITIONS_LIST
	res = []
	for cls in conditions :
		cls = get_class_with_path(cls)
		res.append( cls().to_type() )
	return res

#@login_required
def missions_rewards_types( request ):
	rewards = MISSION_REWARDS_LIST
	res = []
	for cls in rewards :
		cls = get_class_with_path(cls)
		res.append( cls().to_type() )
	return res

@login_required
def mission_descriptor_type( request ):
	cls = get_class_with_path( MISSION_DESCRIPTOR_CLASS )
	return cls().to_type()
	pass 

@login_required
def mission_add( request, mission ):
	pass

@login_required
def mission_remove( request, mission ):
	pass

@login_required
def mission_publish(request, mission):
	pass

@login_required
def mission_add_condition ( request, mission_id, condition ):
	pass

@login_required
def mission_remove_condition ( request, mission_id, condition ):
	pass

@login_required
def mission_add_pre_condition ( request, mission_id, condition ):
	pass

@login_required
def mission_remove_pre_condition ( request, mission_id, condition ):
	pass

@login_required
def mission_add_validity_condition ( request, mission_id, condition ):
	pass

@login_required
def mission_remove_validity_condition ( request, mission_id, condition ):
	pass

@login_required
def mission_add_reward ( request, mission_id, condition ):
	pass

@login_required
def mission_remove_reward ( request, mission_id, condition ):
	pass

@login_required
def mission_set_name ( request, mission_id, name ):
	pass

@login_required
def mission_set_condition_arg( request, mission_id, key, value ):
	pass

@login_required
def mission_set_pre_condition_arg( request, mission_id, key, value ):
	pass

@login_required
def mission_set_validity_condition_arg( request, mission_id, key, value ):
	pass

@login_required
def mission_set_reward_arg( request, mission_id, key, value ):
	pass

services = {
	'missions.debug':debug, 
	'missions.all': missions_all, 
	'missions.conditionsTypes':missions_contitions_types, 
	'missions.rewardsTypes':missions_rewards_types, 
	'missions.descriptorType':mission_descriptor_type, 
	'missions.missionType':mission_type, 
	'missions.add': mission_add, 
	'missions.remove':mission_remove, 
	'missions.addCondition':mission_add_condition, 
	'missions.removeCondition':mission_remove_condition, 
	'missions.addPreCondition':mission_add_pre_condition, 
	'missions.removePreCondition':mission_remove_pre_condition, 
	'missions.addValidityCondition':mission_add_validity_condition, 
	'missions.removeValidityCondition':mission_remove_validity_condition, 
	'missions.addReward':mission_add_reward, 
	'missions.removeReward':mission_remove_reward, 
	'missions.setName':mission_set_name, 
	'missions.setConditionArg':mission_set_condition_arg, 
	'missions.setPreconditionArg':mission_set_pre_condition_arg, 
	'missions.setValidityConditionArg':mission_set_validity_condition_arg, 
	'missions.setRewardArg':mission_set_reward_arg, 
}

missions_gateway = DjangoGateway( services )
