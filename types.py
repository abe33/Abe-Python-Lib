# -*- coding: utf-8 -*-
from abe.utils import *

import pyamf, re

class Type:
	
	type = None
	struct = None
	parent_type=None
	form_struct=None
	help_text=None
	
	class __amf__:
		external = True
		amf3 = True

	def __init__(self, type=None, struct=None, parent_type=None, form_struct=None,  help_text=None):
		self.type = type 
		self.struct = struct
		self.parent_type = parent_type if parent_type is not None else "object"
		self.form_struct = form_struct if form_struct is not None else struct
		self.help_text = help_text

	def __writeamf__(self, output):
#		print "write type"
		output.writeUTF( self.type )
#		print "write parent type"
		output.writeUTF( self.parent_type )
#		print "write struct"
		output.writeObject( self.struct )
#		print "write form struct"
		output.writeObject( self.form_struct )
#		print "write help text"
		output.writeUTF( self.help_text )

	def __readamf__(self, input):
		
		self.type = input.readUTF()
#		print "read type %s" % self.type
		self.parent_type = input.readUTF()
#		print "read parent type %s" % self.parent_type
		self.struct = input.readObject()
#		print "read struct %s" % str(self.struct)
		self.form_struct = input.readObject()
#		print "read form struct %s" % str(self.form_struct)
		self.help_text = input.readUTF()
#		print "read help text %s" % self.help_text
	
	def __repr__(self):
		return "<%s type>" % self.type

class TypeInstance:
	id = None
	type = None
	data = None
	
	class __amf__:
		external = True
		amf3 = True

	def __init__(self, type=None, data=None, id=None ):
		self.id = id if id != "" else None
		self.type = type 
		self.data = data

	def get_type_name(self):
		return self.type.type
	type_name = property( get_type_name )

	def is_valid_id(self,  id):
		sid = str(id)
		return id is not None and sid != "" and sid != "None"

	def __writeamf__(self, output):
		output.writeUTF( str( self.id ) )
		output.writeObject( self.type )
		output.writeObject( self.data )

	def __readamf__(self, input):
		
		id = input.readUTF()
#		print "read id %s (%s) : %s vs %s" % ( id, type(id),  self.is_valid_id( id ), self.id )
		if self.is_valid_id( id ) : 
			self.id = int( id )
		
#		print "self.id %s" % self.id
		self.type = input.readObject()
#		print "read type %s" % str( self.type )
		self.data = input.readObject()
#		print "read data %s" % str( self.data )
	
	def __repr__(self):
		return "<%s instance>" % self.type_name

pyamf.register_class( TypeInstance, 'aesia.com.patibility.types.TypeInstance' )
pyamf.register_class( Type, 				'aesia.com.patibility.types.Type' )

def instance_from_type( type ):
	if 'type' in type :
		a = type['type'].split( "." )
		cls = get_definition( "".join(a[-1:]), ".".join(a[:-1]))
		del type['type']
		o = cls( **type )
		return o
	else:
		raise KeyError(_(u"The type property of the argument dict is mandatory."))

def instance_from_type_instance( instance ):
	print instance 
	if isinstance( instance,  TypeInstance ) :
		a = instance.type_name.split( "." )
		cls = get_definition( "".join(a[-1:]), ".".join(a[:-1]))

		if instance.id is not None and issubclass( cls, models.Model ) : 
			o = cls.objects.get(id=instance.id)
			for k in instance.data : 
				d = instance.data[k]
				if d is not None and type(d) is type( getattr(o, k) ) : 
					setattr(o,  k, d )

		elif issubclass( cls, models.Model ) :
			o = cls()
			for k in instance.data : 
				d = instance.data[k]
				if d is not None and type(d) is type( getattr(o, k) )  : 
					setattr(o,  k, d )

		else:
			o = cls( **instance.data )
		return o
	else:
		raise ValueError(_(u"The argument must be a valid TypeInstance object."))
