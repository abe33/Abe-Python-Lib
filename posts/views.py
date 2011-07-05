# -*- coding: utf-8 -*-
from django.shortcuts import render_to_response
from django.shortcuts import redirect
from django.template import RequestContext
from django.template.loader import render_to_string
from django.http import *
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from django.utils import simplejson
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count
from tagging.models import *

from abe.posts.models import *
from abe.posts.templatetags import posts as posts_tags
from abe.posts import settings as msettings
from abe.utils import *

import math
import re


def post_list_generic ( request, 
                        posts_list, 
                        page_title='Untitled page', 
                        next_page_view="", 
                        rss_page_view="", 
                        pages_args=None, 
                        page_index=msettings.START_PAGE, 
                        num=msettings.NUM_POST_PER_PAGE ):
    if len( posts_list ) == 0:
        return render_to_response( "posts/post_list.html", 
                                   {
                                      'page_title':page_title,
                                   }, 
                                   RequestContext( request ) )

    paginator = Paginator( posts_list,  int(num) )
    page = paginator.page( int(page_index) )

    has_next_page = page.has_next()
    has_previous_page = page.has_previous()
    rss_page_url = None
    next_page_url = None
    previous_page_url = None
    
    if rss_page_view is not None :
        rss_page_url = reverse( rss_page_view,  kwargs=pages_args )

    if has_next_page :
        pages_args["page"] = page.next_page_number()
        next_page_url = reverse( next_page_view,  kwargs=pages_args )

    if has_previous_page :
        pages_args["page"] = page.previous_page_number()
        previous_page_url = reverse( next_page_view,  kwargs=pages_args )
    
    if request.GET.has_key( "json" ):
        return HttpResponse( simplejson.dumps( [o.to_dict() for o in page.object_list ] ) )
    elif request.GET.has_key( "xml" ):
        return render_to_response( "posts/xml_post_list.html", 
                                   {
                                       'posts_list':page.object_list, 
                                       'page_title':page_title,
                                       'page_index':page_index, 
                                       'pages_count':paginator.count, 
                                       'has_next_page':has_next_page, 
                                       'has_previous_page':has_previous_page, 
                                       'next_page_url':next_page_url, 
                                       'previous_page_url':previous_page_url, 
                                       'rss_page_url':rss_page_url, 
                                   }, 
                                   RequestContext( request ) )
    else:
        return render_to_response( "posts/post_list.html", 
                                   {
                                       'posts_list':page.object_list, 
                                       'page_title':page_title,
                                       'page_index':page_index, 
                                       'pages_count':paginator.count, 
                                       'has_next_page':has_next_page, 
                                       'has_previous_page':has_previous_page, 
                                       'next_page_url':next_page_url, 
                                       'previous_page_url':previous_page_url, 
                                       'rss_page_url':rss_page_url, 
                                   }, 
                                   RequestContext( request ) )


def page_not_found( request ):
     return render_to_response( "404.html", 
                                {
                                    'root_url':reverse("index"), 
                                    'page_title':_(u'404 Error')
                                }, 
                                RequestContext( request ) )

@login_required
def post_preview ( request,  id ): 
    p = Post.objects.get(id=id)
    
    return render_to_response( "posts/post_details.html", 
                               {
                                   'post':p,
                                   'id':id, 
                                   'page_title':_(u'Post - %(name)s') % {'name':p.name}, 
                               }, 
                               RequestContext( request ) )

def post_details( request, year,  month,  day,  slug):
    p = Post.objects.get( Q(published_date__year=year),
                                      Q(published_date__month=month),
                                      Q(published_date__day=day),
                                      Q(slug=slug) )
    if request.GET.has_key( "json" ):
        return HttpResponse( simplejson.dumps( p.to_dict() ) )
    elif request.GET.has_key( "xml" ):
        return render_to_response( "posts/xml_post_view.html", 
                                   {
                                        'post':p,
                                        'page_title':_(u'Post - %(name)s') % { 'name':p.name }, 
                                   }, 
                                   RequestContext( request ) )
    else:
        return render_to_response( "posts/post_details.html", 
                                   {
                                       'post':p, 
                                       'page_title':_(u'Post - %(name)s') % { 'name':p.name }, 
                                   }, 
                                   RequestContext( request ) )

def orphan_page( request, orphan_id ):
    post = Post.objects.get(orphan_id=orphan_id)
    if request.GET.has_key( "json" ):
        return HttpResponse( simplejson.dumps( post.to_dict() ) )
    elif request.GET.has_key( "xml" ):
        return render_to_response( "posts/xml_post_view.html", 
                                   {
                                        'post':p,
                                        'page_title':_(u'Post - %(name)s') % { 'name':post.name }, 
                                   }, 
                                   RequestContext( request ) )
    else:
        return render_to_response( "posts/post_details.html", 
                                   {
                                       'post':post, 
                                       'page_title':post.name, 
                                   }, 
                                   RequestContext( request ) )

def post_list( request, page=msettings.START_PAGE,  num=msettings.NUM_POST_PER_PAGE ):
    return post_list_generic( request,  
                              Post.objects.filter(published=True, orphan=False).order_by("-published_date"), 
                              _(u"Posts"), 
                              "post_archive", 
                              "post_rss", 
                              {}, 
                              page, 
                              num )

def post_by_tag ( request,  tag, page=msettings.START_PAGE,  num=msettings.NUM_POST_PER_PAGE ):
     return post_list_generic( request,  
                               Post.objects.filter(published=True, orphan=False,  tags__contains=tag).order_by("-published_date"), 
                               (u"Tag : %(tag)s") % {'tag':tag} , 
                               "post_by_tag_archive", 
                               "post_by_tag_rss", 
                               {
                                   'tag':tag
                               }, 
                               page, 
                               num )

def post_by_category( request,  category, page=msettings.START_PAGE,  num=msettings.NUM_POST_PER_PAGE ):
    cat = PostCategory.objects.get(slug=category)
    return post_list_generic( request,  
                              Post.objects.filter(published=True, orphan=False,  category__slug=category).order_by("-published_date"), 
                              _(u"Category : %(cat)s") % {'cat':cat.name} , 
                              "post_by_category_archive", 
                              "post_by_category_rss", 
                              {
                                  'category':category
                              }, 
                              page, 
                              num )

def post_by_year( request,  year, page=msettings.START_PAGE,  num=msettings.NUM_POST_PER_PAGE ):
    return post_list_generic( request,  
                              Post.objects.filter(published=True, orphan=False,  published_date__year=year).order_by("-published_date"), 
                              _(u"Posts for %(year)s") % { 'year':year}, 
                              "post_by_year_archive", 
                              None, 
                              {
                                  'year':int(year)
                              }, 
                              page, 
                              num )

def post_by_month( request,  year,  month, page=msettings.START_PAGE,  num=msettings.NUM_POST_PER_PAGE ):
    return post_list_generic( request,  
                              Post.objects.filter(published=True, orphan=False, published_date__year=year, published_date__month=month).order_by("-published_date"), 
                              _(u"Posts for the %(month)s %(year)s") % { 'month':month, 'year':year }, 
                              "post_by_month_archive", 
                              None, 
                              {
                                  'year':int(year), 
                                  'month':int(month),
                              }, 
                              page, 
                              num )

def post_by_group( request, group, page=msettings.START_PAGE,  num=msettings.NUM_POST_PER_PAGE ):
    g = PostGroup.objects.get(slug=group)
    return post_list_generic( request,  
                              g.sorted_posts(), 
                              _(u"Posts for the %(group)s series") % { 'group':g.name }, 
                              "post_by_month_archive", 
                              None, 
                              {
                                  'group':g.slug,
                              }, 
                              page, 
                              num )
def links_list ( request ):
    l = SiteLink.objects.all()
    
    if request.GET.has_key( "json" ):
        return HttpResponse( simplejson.dumps( [ o.to_dict() for o in l ] ) )
    elif request.GET.has_key( "xml" ):
        return render_to_response( "posts/xml_links_index.html", 
                                   {
                                       'links':l, 
                                       'page_title':_(u'Links')
                                   }, 
                                   RequestContext( request ) )
    else:
        return render_to_response( "posts/links_index.html", 
                                   {
                                       'links':l, 
                                       'page_title':_(u'Links')
                                   }, 
                                   RequestContext( request ) )

def archives_list ( request ):
    posts = Post.objects.filter(published=True, orphan=False)
    comments = Comment.objects.all()
    archives = posts.dates('published_date', 'month', order='DESC')
    total_count = posts.count()
    counts = []
    for date in archives :
        sub_posts = posts.filter( published_date__year=date.year, 
                                  published_date__month=date.month)
        count = sub_posts.count()
        counts.append( {
                           'date':date, 
                           'count':count, 
                           'ratio': int( float( count ) /  float( total_count ) * 100 ),
                       } )
        
    if request.GET.has_key( "json" ):
        for k in counts:
            k["date"] = str(k["date"])
        return HttpResponse( simplejson.dumps( {
                                   'total_count':total_count, 
                                   'archives_counts':counts, 
                            } ) )
    elif request.GET.has_key( "xml" ):
        return render_to_response( "posts/xml_archives_index.html", 
                                   {
                                       'total_count':total_count, 
                                       'archives_counts':counts, 
                                       'page_title':_(u'Archives')
                                   }, 
                                   RequestContext( request ) )
    else:
        return render_to_response( "posts/archives_index.html", 
                               {
                                   'total_count':total_count, 
                                   'archives_counts':counts, 
                                   'page_title':_(u'Archives')
                               }, 
                               RequestContext( request ) )

def search( request ):
    query_string = ''
    found_entries = None
    if ('q' in request.GET ) and request.GET['q'].strip():
        query_string = request.GET['q']
        
        entry_query = get_query(query_string, ['name', 'excerpt','content', 'tags'])
        
        found_entries = Post.objects.filter(entry_query).filter(published=True, orphan=False).order_by('-published_date')

    return post_list_generic( request,  
                              found_entries, 
                              _(u"Search : %(query)s") % { 'query':query_string }, 
                              None, 
                              None, 
                              {} )


