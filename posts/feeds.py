# -*- coding: utf-8 -*-
from django.contrib.syndication.views import Feed
from abe.posts.models import *
from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse
from django.shortcuts import *

class LatestPostFeed(Feed):
	title = _(u"Latest published posts")
	link = ""
	description = _(u"Latest published posts")

	def link(self):
		return reverse("index")

	def items(self):
		return Post.objects.filter(published=True).order_by('-published_date')[:10]

	def item_title(self, item):
		return item.name

	def item_description(self, item):
		return item.content_or_excerpt()

class LatestPostByCategoryFeed(Feed):
	title = ""
	link = ""
	description = ""

	def get_object(self, request, category):
		return get_object_or_404(PostCategory, name=category)

	def items(self, cat ):
		return Post.objects.filter(published=True,  category__name=cat.name).order_by('-published_date')[:10]

	def title(self,  cat ):
		return _(u"Latest published posts in category %s" % cat.name)

	def link(self, cat ):
		return reverse("post_by_category",  kwargs={'category':cat.name})

	def item_title(self, item):
		return item.name

	def item_description(self, item):
		return item.content_or_excerpt()

class LatestPostByTagFeed(Feed):
	title = ""
	link = ""
	description = ""

	def title(self,  tag ):
		return _(u"Latest published posts with tag %s" % tag)

	def get_object(self, request, tag):
		return tag

	def link(self, tag ):
		return reverse("post_by_tag",  kwargs={'tag':tag})

	def items(self, tag ):
		return Post.objects.filter(published=True,  tags__contains=tag).order_by('-published_date')[:10]

	def item_title(self, item):
		return item.name

	def item_description(self, item):
		return item.content_or_excerpt()
