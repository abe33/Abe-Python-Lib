# -*- coding: utf-8 -*-
import datetime

from django.db import models
from django.utils.translation import ugettext as _
from django.template.defaultfilters import *
from django.contrib.comments.models import Comment
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.contrib.sitemaps import ping_google
from django.contrib.sitemaps import Sitemap

from tagging import fields
from babelfish.models import BabelFishModel, BabelFishField

def sort_posts( o ):
    return o.group_order if o.group_order is not None else o.published_date.strftime("%Y%m%j%H%M%S")

class PostCategory( BabelFishModel ):
    translate_fields = ('name', 'description')
    bf_translations = BabelFishField( translate_fields )

    slug = models.CharField( _(u"Category Slug"), max_length=50, null=True, blank=True )
    
    name = models.CharField( _(u"Category Name"), max_length=50 )
    description = models.TextField(_(u"Category Description"), 
                                    null=True,
                                    blank=True, 
                                    help_text=_(u"The category description is generally used in category pages, "
                                                u"or as a link description while linking to a category."))
    
    creation_date = models.DateTimeField( _(u"Creation date"),  auto_now_add=True )
    update_date = models.DateTimeField( _(u"Update date"),  auto_now=True )
    
    allow_comments = models.BooleanField(_(u"Allow comments"),  default=True )
    
    parent = models.ForeignKey( 'PostCategory', blank=True, null=True, related_name='children' )
    
    def get_count(self):
        if hasattr( self, "count" ):
            return self.count
        else :
            setattr( self, "count", self.post_set.filter(published=True).count() )
            return self.count
      
    def get_absolute_url(self):
        return reverse( "post_by_category", kwargs={'category':self.slug} )

    def __unicode__(self):
        return u"%s" % self.name
    
    def has_children_categories(self):
        return len(self.get_children_categories()) > 0
        
    def get_children_categories(self):
        if hasattr( self, "children_categories" ):
            return self.children_categories
        else:   
            setattr( self, "children_categories", self.children.all() )
            return self.children_categories

    def to_dict(self):
        return {
                'name':self.name,
                'description':self.description,
                'slug':self.slug,
                }
                
    def save(self):
        self.translate()
        
        if self.slug is None :
            self.slug = slugify( self.name )
            
        super( PostCategory,  self ).save()

    class Meta:
        auto_translate=True
        verbose_name=_(u"Post Category")
        verbose_name_plural=_(u"Post Categories")

class PostGroup( BabelFishModel ):
    translate_fields = ('name', 'description')
    bf_translations = BabelFishField( translate_fields )
    
    name = models.CharField( _(u"Category Name"), max_length=50 )
    slug = models.CharField( _(u"Category Slug"), max_length=50, null=True, blank=True )
    description = models.TextField(_(u"Category Description"), 
                                    null=True,
                                    blank=True, 
                                    help_text=_(u"The category description is generally used in category pages, "
                                                u"or as a link description while linking to a category."))
    
    def __unicode__(self):
        return u"%s" % self.name
    
    def get_absolute_url(self):
        return reverse( "post_by_group", kwargs={'group':self.slug} )    
    
    def has_previous( self, post ):
        posts = self.sorted_posts()
        if posts.index(post) > 0 : 
            return True
        else:
            return False
    
    def get_previous( self, post ):
        posts = self.sorted_posts()
        if self.has_previous( post ):
            return posts[ posts.index( post ) - 1 ]
        else :
            return None
            
    def has_next( self, post ):
        posts = self.sorted_posts()
        if posts.index(post) < len(posts)-1 : 
            return True
        else:
            return False
    
    def get_next( self, post ):
        posts = self.sorted_posts()
        if self.has_next( post ):
            return posts[ posts.index( post ) + 1 ]
        else :
            return None
        
    def sorted_posts(self):
        if not hasattr( self, "posts" ) : 
            self.posts = self.post_set.all()
            self.posts = sorted( self.posts, key=sort_posts )
        
        return self.posts
    
    def save(self):
        self.translate()
        
        if self.slug is None :
            self.slug = slugify( self.name )
            
        super( PostGroup,  self ).save()
    
    class Meta:
        auto_translate=True
        verbose_name=_(u"Post Group")
        verbose_name_plural=_(u"Post Groups")
    

class Post ( BabelFishModel ) :
    
    translate_fields=('name','excerpt','content')
    bf_translations = BabelFishField( translate_fields )

    author = models.ForeignKey( User, verbose_name=_(u"Author"), blank=True, null=True )

    name = models.CharField( _(u"Post title"),  max_length=50 )
    slug = models.CharField( _(u"Post slug"),  blank=True,  null=True,  max_length=50 )    
    
    excerpt = models.TextField(_(u"Post excerpt"),  null=True,  blank=True)
    content = models.TextField(_(u"Post content"),  null=True,  blank=True)
    
    featured = models.BooleanField(_(u"Featured"), default=False, blank=True )
    tags = fields.TagField(_(u"Tags"),  null=True,  blank=True) 
    category = models.ForeignKey( PostCategory, verbose_name=_(u"Category") )
    allow_comments = models.BooleanField(_(u"Allow comments"),  default=True )
    
    group = models.ForeignKey( PostGroup, verbose_name=_(u"Group"), blank=True,  null=True )
    group_order=models.IntegerField(_(u"Group Order"), blank=True, null=True )
    
    published = models.BooleanField(_(u"Published"))
    published_date = models.DateTimeField( _(u"Published date"), blank=True,  null=True )
    
    orphan = models.BooleanField(_(u"Orphan page"),  default=False )
    orphan_id = models.CharField( _(u"Orphan page ID"),  max_length=50,  blank=True,  null=True )
    
    creation_date = models.DateTimeField( _(u"Creation date"),  auto_now_add=True )
    update_date = models.DateTimeField( _(u"Update date"),  auto_now=True )
    
    def comments_count(self):
        if self.allow_comments :
            return Comment.objects.filter(object_pk=self.id,).count()
        else :
            return _(u"None")
    comments_count.short_description = _(u"Comments")

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
    
    def has_group(self):
        return self.group is not None
    
    def has_previous_post_in_group(self):
        if not self.has_group():
            return False
        else:
            return self.group.has_previous( self )
    
    def has_next_post_in_group(self):
        if not self.has_group():
            return False
        else:
            return self.group.has_next( self )
    
    def get_next_post_in_group(self):
        if self.has_next_post_in_group():
            return self.group.get_next( self )
        else:
            return None
    
    def get_previous_post_in_group(self):
        if self.has_previous_post_in_group():
            return self.group.get_previous( self )
        else:
            return None
    
    def has_previous(self):
        try :
            self.get_previous_by_published_date()
            return True
        except:
            return False
    
    def has_next(self):
        try :
            self.get_next_by_published_date()
            return True
        except:
            return False
    
    def get_previous(self):
        return self.get_previous_by_published_date()
    
    def get_next(self):
        return self.get_next_by_published_date()

    def has_hidden_content(self):
        return len( self.excerpt.strip() ) > 0
        
    def content_or_excerpt(self):
        if len( self.excerpt.strip() ) == 0:
            return self.content
        else:
            return self.excerpt

    def save(self):
        self.translate()
    
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
    
    def to_dict(self):
        return {
                'id':self.id,
                'name':self.name,
                'url':self.get_absolute_url(),
                'excerpt':self.excerpt,
                'content':self.content,
                'tags':self.tags,
                'category':self.category.name,
                'orphan':self.orphan,
                'orphan_id':self.orphan_id,
                'published_date':str( self.published_date ),
                'featured':self.featured,
                }

    class Meta:
        auto_translate=True
        verbose_name=_(u"Post")
        verbose_name_plural=_(u"Posts")
        ordering = ["-published_date", ]

class PostSitemap(Sitemap):
    changefreq = "never"
    priority = 0.5

    def items(self):
        return Post.objects.filter(published=True, orphan=False)

    def lastmod(self, obj):
        return obj.published_date

class SiteLinkCategory( BabelFishModel ):
    translate_fields = ('name','description')
    bf_translations = BabelFishField( translate_fields )
    
    name = models.CharField( _(u"Link Category title"),  max_length=50 )
    description = models.TextField(_(u"Link Category description"),  null=True,  blank=True)
    slug = models.CharField( _(u"Link Category Slug"), max_length=50, null=True, blank=True )
    
    creation_date = models.DateTimeField( _(u"Creation date"),  auto_now_add=True )
    update_date = models.DateTimeField( _(u"Update date"),  auto_now=True )
    
    parent = models.ForeignKey( 'SiteLinkCategory', blank=True, null=True, related_name='children' )
    
    def has_children_categories(self):
        return len(self.get_children_categories()) > 0
        
    def get_children_categories(self):
        if hasattr( self, "children_categories" ):
            return self.children_categories
        else:   
            setattr( self, "children_categories", self.children.all() )
            return self.children_categories
    
    def get_count(self):
        if hasattr( self, "count" ):
            return self.count
        else :
            setattr( self, "count", self.sitelink_set.all().count() )
            return self.count
      
    def get_absolute_url(self):
        return reverse( "links_list_by_category", kwargs={'category':self.slug} )

    def __unicode__(self):
        return u"%s" % self.name

    def to_dict(self):
        return {
                'name':self.name,
                'description':self.description,
                'slug':self.slug,
                }
                
    def save(self):
        self.translate()
        
        if self.slug is None :
            self.slug = slugify( self.name )
            
        super( SiteLinkCategory, self ).save()

    class Meta:
        auto_translate=True
        verbose_name=_(u"Site Links Category")
        verbose_name_plural=_(u"Site Links Categories")
        ordering = ["name",]

class SiteLink ( BabelFishModel ) :
    translate_fields = ('name','description')
    bf_translations = BabelFishField( translate_fields )

    name = models.CharField( _(u"Link title"),  max_length=50 )
    url = models.URLField( _(u"Link url"),  max_length=200,  verify_exists=True )
    icon = models.ImageField( upload_to="uploads/",  verbose_name=_(u"Link icon"),  null=True, blank=True )
    description = models.TextField(_(u"Link description"),  null=True,  blank=True)
    
    category = models.ForeignKey( SiteLinkCategory, verbose_name=_(u"Link Category"), null=True, blank=True )
    featured = models.BooleanField(_(u"Featured"), default=False, blank=True )
    rel = models.CharField( _(u"Relation Tag"), max_length=50, null=True,  blank=True )

    creation_date = models.DateTimeField( _(u"Creation date"),  auto_now_add=True )
    update_date = models.DateTimeField( _(u"Update date"),  auto_now=True )
    
    def to_dict( self):
        return {
                'name':self.name,
                'url':self.url,
                'icon':str(self.icon),
                'description':self.description,
                'featured':self.featured,
                'rel':self.rel
                }

    def __unicode__(self):
        return u"%s" % self.name

    class Meta:
        auto_translate=True
        verbose_name=_(u"Site Link")
        verbose_name_plural=_(u"Site Links")
        ordering = ["name", ]
