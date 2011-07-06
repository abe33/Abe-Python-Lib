# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
from abe.posts.feeds import *


urlpatterns = patterns('abe.posts',
    url( r'^$', 'views.post_list', name="post_list" ),
    url( r'post/page/(?P<page>\d+)/$', 'views.post_list', name="post_archive" ),
    url( r'post/page/(?P<page>\d+)/(?P<num>\d+)/$', 'views.post_list', name="post_archive_num" ),
    url( r'post/rss/$', LatestPostFeed(), name="post_rss"), 
    url( r'post/search/$', 'views.search', name="search"), 

    url( r'page/(?P<orphan_id>[\w_-]+)/$', 'views.orphan_page', name="orphan_page"), 

    url( r'post/(?P<year>\d{4})/(?P<month>\d{1,2})/(?P<day>\d{1,2})/(?P<slug>[\w_-]+)/$', 'views.post_details', name="post_details"), 
    url( r'post/preview/(?P<id>\d+)/$', 'views.post_preview', name="post_preview"), 

    url( r'post/category/(?P<category>[\w_ -]+)/$', 'views.post_by_category', name="post_by_category" ),
    url( r'post/category/(?P<category>[\w_ -]+)/page/(?P<page>\d+)/$', 'views.post_by_category', name="post_by_category_archive" ),
    url( r'post/category/(?P<category>[\w_ -]+)/page/(?P<page>\d+)/(?P<num>\d+)/$', 'views.post_by_category', name="post_by_category_archive_num" ),
    url( r'post/category/(?P<category>[\w_ -]+)/rss/$', LatestPostByCategoryFeed(), name="post_by_category_rss"), 

    url( r'post/group/(?P<group>[\w_ -]+)/$', 'views.post_by_group', name="post_by_group" ),
    url( r'post/group/(?P<group>[\w_ -]+)/page/(?P<page>\d+)/$', 'views.post_by_group', name="post_by_group_archive" ),
    url( r'post/group/(?P<group>[\w_ -]+)/page/(?P<page>\d+)/(?P<num>\d+)/$', 'views.post_by_group', name="post_by_group_archive_num" ),

    url( r'post/tag/(?P<tag>[\w_ -]+)/$', 'views.post_by_tag', name="post_by_tag" ),
    url( r'post/tag/(?P<tag>[\w_ -]+)/page/(?P<page>\d+)/$', 'views.post_by_tag', name="post_by_tag_archive" ),
    url( r'post/tag/(?P<tag>[\w_ -]+)/page/(?P<page>\d+)/(?P<num>\d+)/$', 'views.post_by_tag', name="post_by_tag_archive_num" ),
    url( r'post/tag/(?P<tag>[\w_ -]+)/rss/$', LatestPostByTagFeed(), name="post_by_tag_rss"),

    url( r'post/archives/$', 'views.archives_list', name="archives_list"), 
    url( r'post/archives/(?P<year>\d{4})/$', 'views.post_by_year', name="post_by_year"), 
    url( r'post/archives/(?P<year>\d{4})/page/(?P<page>\d+)/$', 'views.post_by_year', name="post_by_year_archive"), 
    url( r'post/archives/(?P<year>\d{4})/page/(?P<page>\d+)/(?P<num>\d+)/$', 'views.post_by_year', name="post_by_year_archive_num"), 

    url( r'post/archives/(?P<year>\d{4})/(?P<month>\d{1,2})/$', 'views.post_by_month', name="post_by_month"), 
    url( r'post/archives/(?P<year>\d{4})/(?P<month>\d{1,2})/page/(?P<page>\d+)/$', 'views.post_by_month', name="post_by_month_archive"), 
    url( r'post/archives/(?P<year>\d{4})/(?P<month>\d{1,2})/page/(?P<page>\d+)/(?P<num>\d+)/$', 'views.post_by_month', name="post_by_month_archive_num"), 

    url( r'links/$', 'views.links_list', name="links_list"), 
    url( r'links/(?P<category>[\w_ -]+)/$', 'views.links_list_by_category', name="links_list_by_category"), 
)
