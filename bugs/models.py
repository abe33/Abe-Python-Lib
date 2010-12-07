# -*- coding: utf-8 -*-

from django.db import models

# Create your models here.
from django.utils.translation import ugettext_lazy as _
from django.db import models
from django.conf import settings
from django.template.context import RequestContext
from django.template.loader import render_to_string
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.template.defaultfilters import *
from django.contrib.comments.models import Comment
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import simplejson as json

from tagging import fields
# Le calcul de la pénibilité d'un ticket s'effectuant à partir 
# de critères objectifs, le créateur d'un ticket est encouragé
# à utiliser des valeurs préprogrammés pour chaque critère de
# calcul. Ci-dessous se trouve toutes les listes pour chaque critère. 

# Choix prédéfinis pour le type du problème 
TYPE_CHOICES = (
    (1, _(u"1 - Documentation - An issue in the documentation.")),
    (2, _(u"2 - Localization - An issue with the localization.")),
    (3, _(u"3 - GFX or SFX Polish - An aesthetic issue with graphics or sounds.")),
    (4, _(u"4 - Balance - Enables degenerate usage strategies that harm the experience.")),
    (5, _(u"5 - Minor ergonomy - Impairs usability in secondary scenarios.")),
    (6, _(u"6 - Major ergonomy - Impairs usability in key scenarios.")),
    (7, _(u"7 - Crash - Bug causes crash or data loss. Asserts in the Debug release."))
)  
# Choix prédéfinis pour la priorité du problème
PRIORITY_CHOICES = (
    (1, _(u"1 - Nuisance - Not a big deal but noticeable. Extremely unlikely to affect sales.")),
    (2, _(u"2 - Minor pain - Users won’t like this once they notice it. A moderate number of users won’t buy.")),
    (3, _(u"3 - Medium pain - A User would likely not purchase the product. Will show up in review. Clearly a noticeable issue.")),
    (4, _(u"4 - Major pain - A User would return the product. Cannot RTM. The Team would hold the release for this bug.")),
    (5, _(u"5 - Critical - Blocking further progress on the daily build.")),
) 
# Choix prédéfinis pour la redondance du problème
LIKELIHOOD_CHOICES = (
    (1, _(u"1 - Will affect almost no one.")),
    (2, _(u"2 - Will only affect a few users.")),
    (3, _(u"3 - Will affect average number of users.")),
    (4, _(u"4 - Will affect most users.")),
    (5, _(u"5 - Will affect all users.")),
)
# Status possible pour un ticket
STATUS_CHOICES = (
	(0, _(u"Unconfirmed") ), 
	(1, _(u"Confirmed")), 
	(2, _(u"Open") ), 
	(3, _(u"Solved") ), 
	(4, _(u"Unsolvable") ), 
)

class DictField(models.TextField):
	__metaclass__ = models.SubfieldBase

	def to_python(self, value):
		if value != "" and value is not None :
			value = json.loads(value)
			assert isinstance(value, dict)
		return value

	def get_db_prep_save(self, value, connection ):
		print value
		if value != "" and value is not None : 
			assert isinstance(value, dict)
			value = json.dumps(value, cls=DjangoJSONEncoder )
		return super( DictField, self).get_db_prep_save( value=value,  connection=connection )

# Valeur maximum de pénibilité que peut obtenir un ticket
MAX_POSSIBLE_PAIN_SCORE = 175

# Valeur par défaut pour le niveau d'éxigence d'une étape
DEFAULT_MILESTONE_MAXIMUM_PAIN_LEVEL = 50

class MileStone(models.Model): 
	"""
	Une MileStone représente une étape de développement.
	Il n'y a en général qu'une seule étape d'active à la fois.
	Une MileStone définie un niveau de tolérance maximum aux bugs, 
	tout tickets dont la pénibilité excède ce niveau devra être corrigé
	pour pouvoir considérer l'étape comme accompli
	"""
	name = models.CharField( _(u"Milestone name"), max_length=50 )

	description = models.TextField( _(u"Description"), blank=True,
									help_text=_(u"The milestone description should notice the goal to achieve in this milestone, "
													  u"for instance the modules to implement." ) )

	max_pain_level = models.SmallIntegerField( _(u"Pain threshold"), default=DEFAULT_MILESTONE_MAXIMUM_PAIN_LEVEL,
											   help_text=_(u"The maximum pain level for this milestone. All tickets with a pain value above "
																  u"that limit have to be fixed before ending the milestone." ) )

	public = models.BooleanField(_(u"Public"), default=False, 
								 help_text=_(u"Does this milestone is available to users or is it an internal milestone." ) )

	active = models.BooleanField(_(u'Active'), default=False,
								 help_text=_(u"Define in which milestone the process is currently in. "
													u"Only one milestone can be active at one time, if you activate a milestone, "
													u"the latest active milestone is deactivated." ) )

	creation_date = models.DateTimeField ( _(u"Creation date"), 
										   auto_now_add=True )

	update_date = models.DateTimeField ( _(u"Update date"), 
										 auto_now=True )

	def save(self):
		active = MileStone.objects.filter(active=True)
		if self.pk:
			active = active.exclude(pk=self.pk)
		if active and self.active:
			for c in active:
				c.active = False
				super(MileStone, c).save()
			active = None
		if not active:
			self.active = True
		super(MileStone, self).save()

	@staticmethod
	def active_milestone():
		active = MileStone.objects.filter(active=True)
		return active[0]

	def __unicode__(self): 
		return u'%s' % self.name 

	class Meta: 
		ordering = ('name',) 
		verbose_name = _('MileStone') 
		verbose_name_plural = _(u'MileStones') 

class Component(models.Model): 
	"""
	Un compsant représente un élément indépendant et réutilisable dans un programme. 
	Dans notre cas, on pourra considérer comme composant tout élément pour lequel on souhaite
	avoir un suivi de bugs individualisé.
	"""
	name = models.CharField( _(u"Component name"), max_length=50 )
	description = models.TextField( _(u"Description"), blank=True,
									help_text="A short description of the component's role in the program." )

	creation_date = models.DateTimeField ( _(u"Creation date"), 
										   auto_now_add=True )

	update_date = models.DateTimeField ( _(u"Update date"), 
										 auto_now=True )

	def __unicode__(self): 
		return u'%s' % self.name 

	class Meta: 
		ordering = ('name',) 
		verbose_name = _('Component') 
		verbose_name_plural = _(u'Components') 

class Ticket(models.Model): 
	"""
	Un ticket représente un bug, un problème d'ergonomie, de compréhension.
	Tout élément qui nuit d'un manière ou d'une autre à l'expérience de 
	l'utilisateur. Chaque ticket possède une valeur unique définissant le
	niveau d'importance du problème au regard des utilisateurs. Cette valeur
	est appelée pénibilité (ou pain) et est déduite à partir de critères
	objectifs.
	"""
	name = models.CharField( _(u"Ticket title"), 
											max_length=100, 
											help_text=_(u"Try to give the most concise and accurate description of the bug such as : <br/>"
																u"<i>Enemies disappear while colliding with player.</i><br/>"
																u"<i>Results not saved at the end of the play.</i>" ) )

	description = models.TextField( _(u"Description"), 
													help_text=_(u"Write here the full description of the bug. "
																		u"A good bug description contains the following elements :<ol>"
																		u"<li>The steps which leads to the bugs, if they are known, else " 
																		u"a description of the context in which the bug occurs.</li>"
																		u"<li>The bugs consequences. What does happen to the program.</li>"
																		u"<li>The expected result. How the program should behave in normal time.</li>"
																		u"<li>A <a href='http://en.wikipedia.org/wiki/Workaround' rel='nofollow'>Workaround</a> if it is known.</li></ol>" ) )

	tags = fields.TagField(_(u"Tags"),  null=True,  blank=True,  help_text=_(u"Tags can be used to to group bugs by similarities, "
																													u"such as <code>memory leak</code>, <code>crash</code>, "
																													u"<code>killer</code>, etc...")) 

	pain = models.FloatField( _(u"User Pain"), 
											null=True, 
											blank=True, 
											editable=False )

	type = models.SmallIntegerField( _(u"What type of bug is this?"), 
														 choices=TYPE_CHOICES,
														 blank=True, 
														 null=True, 
														 help_text=_(u"Select the value corresponding to the issue you encounter."), 
														default=1)

	priority = models.SmallIntegerField( _(u"How will those affected feel about the bug?"), 
															 choices=PRIORITY_CHOICES,
															 blank=True, 
															 null=True, 
															 help_text=_(u"Select the value corresponding to the issue you encounter."), 
															default=1)

	likelihood = models.SmallIntegerField( _(u"Who will be affected by this bug?"), 
																choices=LIKELIHOOD_CHOICES,
																blank=True, 
																null=True, 
																help_text=_(u"Select the value corresponding to the issue you encounter." ), 
																default=1)

	killer_bug = models.BooleanField(_(u"Killer bug"), 
												 default=False, 
												 help_text=_(u"A killer bug is a bug which appears to be pretty "
																	u"hard and risky to fix but still must be corrected. "
																	u"The teams leaders must find a solution.") )

	active = models.BooleanField(_(u"Active"), 
												 default=True, 
												 help_text=_(u"A ticket is active until it's state is changed to <code>Solved</code> or <code>Unsolvable</code>.") )

	status = models.SmallIntegerField( _(u"Ticket' status"), 
															choices=STATUS_CHOICES, 
															help_text=_(u"The ticket' status indicates in which step the bugs is in the correction process."), 
															default=0, 
															blank=True)

	component = models.ForeignKey ( "bugs.Component", 
														  verbose_name= _(u"Component"), 
														  related_name="ticket_component",
														  help_text=_(u"The component concerned by the bug."), 
														  blank=True, 
														  null=True )

	creator = models.ForeignKey ( "auth.User", 
													verbose_name= _(u"Creator"), 
													related_name="ticket_creator" )

	assignees = models.ManyToManyField ( "auth.User", 
															 verbose_name= _(u"Assignees"), 
															 related_name="ticket_assignees", 
															 null=True, 
															 blank=True,
															 limit_choices_to={'is_superuser__exact':True}, 
															 help_text=_(u"The users who are in charges of the bug correction.") )

	assignee_head = models.ForeignKey( "auth.User", 
															  verbose_name=_(u"Assignee referee"), 
															  related_name="ticket_assignee_head", 
															  null=True, 
															  blank=True, 
															  limit_choices_to={'is_superuser__exact':True}, 
															  help_text=_(u"The referee for this bug.") )
	
	assignee_note = models.TextField( _(u"Assignees notes"), 
													blank=True,
													null=True, 
													help_text=_(u"Whatever the assignees consider worst noticing." ) )

	planified_to_milestone = models.ForeignKey ( "bugs.Milestone", 
																		 verbose_name= _(u"Planning"), 
																		 related_name="ticket_planified_to_milestone", 
																		 null=True, 
																		 blank=True,
																		 help_text=_(u"The milestone in which the bug is planned to be fixed." ) )

	closed_in_milestone = models.ForeignKey ( "bugs.Milestone", 
																		verbose_name= _(u"End"), 
																		related_name="ticket_closed_in_milestone", 
																		null=True, 
																		blank=True,
																		help_text=_(u"The milestone in which the bug was fixed." ) )

	creation_date = models.DateTimeField ( _(u"Creation date"), 
																 auto_now_add=True )

	update_date = models.DateTimeField ( _(u"Update date"), 
																auto_now=True )

	allow_comments = models.BooleanField(_(u"Allow comments"),  
																 default=True, 
																 help_text=_(u"Does users can comments tickets?"))

	contextual_data = DictField( _(u"Context") , 
												default=None, 
												null=True, 
												blank=True, 
												help_text=_(u"A dict object which should contains contextual data on the bug.") )

	attached_url = models.URLField( _(u"External datas"), 
														max_length=200, 
														verify_exists=True,
														default=None, 
														null=True, 
														blank=True, 
														help_text=_(u"A link to additionnal ressources for this ticket, such as screenshots, "
																			u"logs, or whatever that can be usefull to fix the bug.") )

	def pain_as_int (self):
		if self.pain is not None :
			return int(self.pain)
		else:
			return 0

	def block_milestone (self):
		if self.pain is not None : 
			return self.pain >= MileStone.active_milestone().max_pain_level
		else:
			return False

	def is_affected (self):
		return len( self.assignees.all() ) > 0

	def has_assignees(self):
		return len( self.assignees.all() ) > 0

	def is_assignee ( user ):
		return user in self.assignees.all()

	def is_done(self):
		return self.active is False
	
	def print_type( self, o ):
		print o, type( o ),  self.is_valid_int( o )

	def is_valid_int ( self,  value ):
		return value is not None and value != ""

	def save(self, **kwargs):
		print "save"
		if self.is_valid_int(self.type) and self.is_valid_int(self.priority) and self.is_valid_int(self.likelihood):
			self.pain = self.type * self.likelihood * self.priority * 100.0 / MAX_POSSIBLE_PAIN_SCORE
		
		if self.status in [3, 4]:
			self.active = False
		
		super(Ticket, self).save(**kwargs)
		
	def comments_count(self):
		if self.allow_comments :
			return Comment.objects.filter(object_pk=self.id,).count()
		else :
			return _(u"None")
	comments_count.short_description = _(u"Comments")

	def next_ticket(self):
		objects = Ticket.objects.filter(active=True).order_by('-pain')
		
		if self in objects :
			try:
				a = list( objects.values_list("id", flat=True) )
				i = a.index(self.pk)
			except:
				i = -1
			if i > -1 and i+1 < len(a) : 
				return objects[ i+1]
			else:
				return None
		else:
			return None
			
	def previous_ticket(self):
		objects = Ticket.objects.filter(active=True).order_by('-pain')
		
		if self in objects :
			try:
				a = list( objects.values_list("id", flat=True) )
				i = a.index(self.pk)
			except:
				i = -1
			if i > -1 and i-1 > -1 : 
				return objects[ i-1]
			else:
				return None
		else:
			return None

	@models.permalink
	def get_absolute_url(self):
		return ( 'ticket_detail', (),  {'id':self.id} )

	def __unicode__(self): 
		return u'%s' % self.name 

	class Meta: 
		ordering = ('-pain',) 
		verbose_name = _(u'Ticket') 
		verbose_name_plural = _(u'Tickets')
