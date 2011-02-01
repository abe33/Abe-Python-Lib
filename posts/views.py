# -*- coding: utf-8 -*-
from django.shortcuts import render_to_response
from django.shortcuts import redirect
from django.template import RequestContext
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count
from tagging.models import *

from abe.posts.models import *
from abe.posts import settings as msettings

import math
import re

def normalize_query(query_string,
                    findterms=re.compile(r'"([^"]+)"|(\S+)').findall,
                    normspace=re.compile(r'\s{2,}').sub):
    ''' Splits the query string in invidual keywords, getting rid of unecessary spaces
        and grouping quoted words together.
        Example:
        
        >>> normalize_query('  some random  words "with   quotes  " and   spaces')
        ['some', 'random', 'words', 'with quotes', 'and', 'spaces']
    
    '''
    return [normspace(' ', (t[0] or t[1]).strip()) for t in findterms(query_string)] 

def get_query(query_string, search_fields):
    ''' Returns a query, that is a combination of Q objects. That combination
        aims to search keywords within a model by testing the given search fields.
    '''
    query = None # Query to search for every search term        
    terms = normalize_query(query_string)
    for term in terms:
        or_query = None # Query to search for a given term in each field
        for field_name in search_fields:
            q = Q(**{"%s__icontains" % field_name: term})
            if or_query is None:
                or_query = q
            else:
                or_query = or_query | q
        if query is None:
            query = or_query
        else:
            query = query & or_query
    return query


def post_list_generic (   request, 
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
		#pages_args["num"] = num
		next_page_url = reverse( next_page_view,  kwargs=pages_args )

	if has_previous_page :
		pages_args["page"] = page.previous_page_number()
		#pages_args["num"] = num
		previous_page_url = reverse( next_page_view,  kwargs=pages_args )

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
	p = Post.objects.get(id=id),
	return render_to_response( "posts/post_details.html", 
												{
													'id':id, 
													'page_title':_(u'Post - %s') % p.name, 
												}, 
												RequestContext( request ) )

def post_details( request, year,  month,  day,  slug):
	p = Post.objects.get( Q(published_date__year=year),
									  Q(published_date__month=month),
									  Q(published_date__day=day),
									  Q(slug=slug) )
	return render_to_response( "posts/post_details.html", 
														{
															'post':p, 
															'page_title':_(u'Post - %s') % p.name, 
														}, 
														RequestContext( request ) )

def orphan_page( request, orphan_id ):
	post = Post.objects.get(orphan_id=orphan_id)
	return render_to_response( "posts/post_details.html", 
												{
													'post':post, 
													'page_title':post.name, 
												}, 
												RequestContext( request ) )

def post_list( request, page=msettings.START_PAGE,  num=msettings.NUM_POST_PER_PAGE ):
	return post_list_generic( request,  
										   Post.objects.filter(published=True, orphan=False).order_by("-published_date"), 
										   _(u"News"), 
										   "post_archive", 
										   "post_rss", 
										   {}, 
										   page, 
										   num )

def post_by_tag ( request,  tag, page=msettings.START_PAGE,  num=msettings.NUM_POST_PER_PAGE ):
	 return post_list_generic(	request,  
											Post.objects.filter(published=True, orphan=False,  tags__contains=tag).order_by("-published_date"), 
											(u"Tag : %s") % tag , 
											"post_by_tag_archive", 
											"post_by_tag_rss", 
											{
											'tag':tag
											}, 
											page, 
											num )

def post_by_category( request,  category, page=msettings.START_PAGE,  num=msettings.NUM_POST_PER_PAGE ):
	return post_list_generic( request,  
										   Post.objects.filter(published=True, orphan=False,  category__name=category).order_by("-published_date"), 
										   _(u"Category : %s") % category , 
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
										   _(u"Posts for %s") % year, 
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
										   _(u"Posts for the %s %s") % ( month, year ), 
										   "post_by_month_archive", 
										   None, 
										   {
											'year':int(year), 
											'month':int(month),
										   }, 
										   page, 
										   num )

def links_list ( request ):
	return render_to_response( "posts/links_list.html", 
												{
													'links':SiteLink.objects.all(), 
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
	return render_to_response( "posts/archives_list.html", 
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
										   _(u"Search : %s") % query_string, 
										   None, 
										   None, 
										   {} )
