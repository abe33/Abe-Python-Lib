# -*- coding: utf-8 -*-
from django.contrib.auth.decorators import *

from pyamf.remoting.gateway.django import DjangoGateway
import pyamf, sys, traceback

from abe.missions.decorators import *
from abe.missions.models import *
from abe.missions.settings import *
from abe.utils import *
from abe.types import *

from datetime import *

def debug(request, *args ):
	print args
	for k in args :
		print type( k )

	return args

#@login_required
def missions_all ( request ):
	return [ o.to_vo() for o in Mission.objects.all() ]

#@login_required
def mission_type( request ):
	return Mission.to_type()

#@login_required
def missions_contitions_types( request ):
	conditions = MISSION_CONDITIONS_LIST
	res = []
	for cls in conditions :
		cls = get_definition_with_path(cls)
		res.append( cls.to_type() )
	return res

#@login_required
def missions_rewards_types( request ):
	rewards = MISSION_REWARDS_LIST
	res = []
	for cls in rewards :
		cls = get_definition_with_path(cls)
		res.append( cls.to_type() )
	return res

#@login_required
def mission_descriptor_type( request ):
	cls = get_definition_with_path( MISSION_DESCRIPTOR_CLASS )
	return cls.to_type()

#@login_required
def mission_descriptors( request ):
	cls = get_definition_with_path( MISSION_DESCRIPTOR_CLASS )
	res = [ o.to_vo() for o in cls.objects.all() ]
	return res

#@login_required
def mission_set_descriptor( request, m, desc ):
	mission = instance_from_type_instance( m )
	descriptor = instance_from_type_instance( desc )
	descriptor.save()
	return descriptor.to_vo()

#@login_required
def mission_add( request, mission ):
	m = instance_from_type_instance( mission )
	m.save()
	return m.to_vo()

#@login_required
def mission_remove( request, mission ):
	pass

#@login_required
def mission_update( request, mission, change_list ):
	m = instance_from_type_instance( mission )
	bool = False
	for k in change_list:
		if k in ["pre_conditions",  "conditions", "validity_conditions"]:
			l = MissionConditionList( [ instance_from_type_instance( o ) for o in mission.data[k] ] )
			setattr( m, k, l )
			bool = True
		elif k in ["rewards",  "failure_rewards"] :
			l =  [ instance_from_type_instance( o ) for o in mission.data[k] ] 
			setattr( m,  k, l )
			bool = True
		else :
			setattr( m, k, mission.data[k] )
			bool = True

	if bool : 
		m.save()

	return True

#@login_required
def mission_publish(request, mission):
	pass

#@login_required
@mission_gateway_triggers("trigger")
def missions_middleware_update(request):
	MISSION_MIDDLEWARE_INSTANCE.update_missions_map()
	
	print MISSION_MIDDLEWARE_INSTANCE.missions_map
	
	return True

#@login_required
def mission_add_condition ( request, mission_id, condition ):
	pass

#@login_required
def mission_remove_condition ( request, mission_id, condition ):
	pass

#@login_required
def mission_add_pre_condition ( request, mission_id, condition ):
	pass

#@login_required
def mission_remove_pre_condition ( request, mission_id, condition ):
	pass

#@login_required
def mission_add_validity_condition ( request, mission_id, condition ):
	pass

#@login_required
def mission_remove_validity_condition ( request, mission_id, condition ):
	pass

#@login_required
def mission_add_reward ( request, mission_id, condition ):
	pass

#@login_required
def mission_remove_reward ( request, mission_id, conditmethodion ):
	pass

#@login_required
def mission_set_name ( request, mission_id, name ):
	pass

#@login_required
def mission_set_condition_arg( request, mission_id, key, value ):
	pass

#@login_required
def mission_set_pre_condition_arg( request, mission_id, key, value ):
	pass

#@login_required
def mission_set_validity_condition_arg( request, mission_id, key, value ):
	pass

#@login_required
def mission_set_reward_arg( request, mission_id, key, value ):
	pass

services = {
	'missions.debug':debug, 
	'missions.all': missions_all, 
	'missions.conditionsTypes':missions_contitions_types, 
	'missions.rewardsTypes':missions_rewards_types, 
	'missions.descriptorType':mission_descriptor_type, 
	'missions.missionType':mission_type, 
	'missions.descriptors':mission_descriptors, 
	'missions.add': mission_add, 
	'missions.remove':mission_remove, 
	'missions.update':mission_update, 
	'missions.setDescriptor':mission_set_descriptor, 
	'missions.middlewareUpdate':missions_middleware_update, 
	
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

missions_gateway = DjangoGateway( services, debug=True )
