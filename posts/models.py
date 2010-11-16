# -*- coding: utf-8 -*-
import datetime

from django.db import models
from django.utils.translation import ugettext as _
from django.template.defaultfilters import *
from django.contrib.comments.models import Comment

from tagging import fields

# Create your models here.
class PostCategory( models.Model ):
	name = models.CharField( _(u"Nom de la catégorie"),  max_length=50 )
	description = models.TextField(_(u"Description de la catégorie"),  null=True,  blank=True)
	
	creation_date = models.DateTimeField( _(u"Date de création"),  auto_now_add=True )
	update_date = models.DateTimeField( _(u"Date de mise à jour"),  auto_now=True )
	
	allow_comments = models.BooleanField(_(u"Commentaires Autorisés"),  default=True )
	
	@models.permalink
	def get_absolute_url(self):
		return ( "post_by_category",  (),  {'category':self.name} )

	def __unicode__(self):
		return u"%s" % self.name

	class Meta:
		verbose_name=_(u"Post Category")
		verbose_name_plural=_(u"Post Categories")

class Post ( models.Model ) :
	name = models.CharField( _(u"Titre du billet"),  max_length=50 )
	slug = models.CharField( _(u"Version urlisée du titre"),  blank=True,  null=True,  max_length=50 )
	
	excerpt = models.TextField(_(u"Le chapeau de ce billet"),  null=True,  blank=True)
	content = models.TextField(_(u"Le contenu de ce billet"),  null=True,  blank=True)
	
	published = models.BooleanField(_(u"Publié"))
	tags = fields.TagField(_(u"Tags"),  null=True,  blank=True) 
	category = models.ForeignKey( PostCategory, verbose_name=_(u"Catégorie") )
	
	allow_comments = models.BooleanField(_(u"Commentable"),  default=True )
	
	orphan = models.BooleanField(_(u"Page Orpheline"),  default=False )
	orphan_id = models.CharField( _(u"Identifiant de page orpheline"),  max_length=50,  blank=True,  null=True )
	
	creation_date = models.DateTimeField( _(u"Date de création"),  auto_now_add=True )
	update_date = models.DateTimeField( _(u"Date de mise à jour"),  auto_now=True )
	published_date = models.DateTimeField( _(u"Date de publication"), blank=True,  null=True )

	def comments_count(self):
		if self.allow_comments :
			return Comment.objects.filter(object_pk=self.id,).count()
		else :
			return _(u"None")
	comments_count.short_description = _(u"Commentaires")

	@models.permalink
	def get_absolute_url(self):
		if self.published :
			if self.orphan : 
				return ( "orphan_page",  (),  {'orphan_id':self.orphan_id} )
			else : 
				return ( "post_details",  (),  {'year':self.published_date.year, 
																  'month':self.published_date.month,  
																  'day':self.published_date.day, 
																  'slug':self.slug} )
		else:
			return ("post_preview", (),  { 'id':self.id })

	def has_hidden_content(self):
		return len( self.excerpt.strip() ) > 0
		
	def content_or_excerpt(self):
		if len( self.excerpt.strip() ) == 0:
			return self.content
		else:
			return self.excerpt

	def save(self):
		if self.slug is None :
			self.slug = slugify( self.name )
		
		if self.orphan : 
			if self.orphan_id is None or self.orphan_id == "" : 
				self.orphan_id = slugify(self.name)
			else : 
				self.orphan_id = slugify(self.orphan_id)
		
		if self.published and self.published_date is None:
			self.published_date = datetime.datetime.now()
		
		super( Post,  self ).save()

	def __unicode__(self):
		return u"%s" % self.name

	class Meta:
		verbose_name=_(u"Post")
		verbose_name_plural=_(u"Posts")
		ordering = ["-published_date", ]

class SiteLink ( models.Model ) :
	name = models.CharField( _(u"Titre du lien"),  max_length=50 )
	url = models.URLField( _(u"URL du lien"),  max_length=200,  verify_exists=True )
	icon = models.ImageField( upload_to="images/",  verbose_name=_(u"Icône du lien"),  null=True,  blank=True )
	description = models.TextField(_(u"Description du lien"),  null=True,  blank=True)
	creation_date = models.DateTimeField( _(u"Date de création"),  auto_now_add=True )
	update_date = models.DateTimeField( _(u"Date de mise à jour"),  auto_now=True )

	def __unicode__(self):
		return u"%s" % self.name

	class Meta:
		verbose_name=_(u"Site Link")
		verbose_name_plural=_(u"Site Links")
		ordering = ["name", ]
