# -*- coding: utf-8 -*-
from django.conf import settings
from django.utils.translation import ugettext as _
from django.db.models import Q

from abe.posts.models import *
from abe.utils import *

MAX_CHARS_FOR_META_DESCRIPTION =  getattr( settings, "MAX_CHARS_FOR_META_DESCRIPTION", 200 )

def default_post_page_meta_description_processor ( results ):
    p = Post.objects.get( Q(published_date__year=results.group('year')) ,
                          Q(published_date__month=results.group('month')),
                          Q(published_date__day=results.group('day')),
                          Q(slug=results.group('slug')) )
    if p is not None : 
        return remove_html_tags(p.content_or_excerpt())[:MAX_CHARS_FOR_META_DESCRIPTION]
    else:
        return DEFAULT_META_DESCRIPTION

NUM_POST_PER_PAGE =  getattr( settings, "NUM_POST_PER_PAGE","4")
START_PAGE =  getattr( settings, "START_PAGE","1")

DEFAULT_META_DESCRIPTION =  getattr( settings, "DEFAULT_META_DESCRIPTION",_(u"This is a default description for this page.") )
URLS_META_DESCRIPTION =  getattr( settings, 
                                 "URLS_META_DESCRIPTION",
                                 (
                                    ("^/site/$", _(u"Welcome on the homepage of this site." ) ), 
                                    ("^/site/post/(?P<year>\d{4})/(?P<month>\d{1,2})/(?P<day>\d{1,2})/(?P<slug>[\w_-]+)/$", "abe.posts.settings.default_post_page_meta_description_processor" ), 
                                 ))

POST_ADMIN_CSS = getattr( settings, 
                          "POST_ADMIN_CSS",
                          ( "%scss/admin_enhancements.css" % settings.MEDIA_URL, ) )

POST_ADMIN_JS = getattr( settings, 
                         "POST_ADMIN_JS",
                         ( "%sjs/jquery-1.4.2.min.js" % settings.MEDIA_URL,
                           "%sjs/ckeditor/ckeditor.js" % settings.MEDIA_URL,
                           "%sjs/admin_enhancements.js" % settings.MEDIA_URL, ) )
