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

# Le calcul de la pénibilité d'un ticket s'effectuant à partir 
# de critères objectifs, le créateur d'un ticket est encouragé
# à utiliser des valeurs préprogrammés pour chaque critère de
# calcul. Ci-dessous se trouve toutes les listes pour chaque critère. 

# Choix prédéfinis pour le type du problème 
TYPE_CHOICES = (
    (1, _(u"1 - Documentation - Un problème dans la documentation.")),
    (2, _(u"2 - Localisation - Un problème dans la traduction.")),
    (3, _(u"3 - Finitions graphiques ou sonores - Un problème d'esthétique.")),
    (4, _(u"4 - Équilibrage - Provoque une déterioration dans l'efficience des stratégies prévues, amenant à une expérience dégradée.")),
    (5, _(u"5 - Ergonomie mineure - Affecte l'ergonomie dans le cas d'un scénario secondaire.")),
    (6, _(u"6 - Ergonomie majeure - Affecte l'ergonomie dans le cas d'un scénario clé.")),
    (7, _(u"7 - Crash - Le problème provoque un crash ou une perte de donnée. Exception levée dans le cas d'une version de debug."))
)  
# Choix prédéfinis pour la priorité du problème
PRIORITY_CHOICES = (
    (1, _(u"1 - Nuisance - Pas un gros problème mais est detectable. N'a probablement aucun effet sur les ventes.")),
    (2, _(u"2 - Plaie - Les utilisateurs  une fois qu'il l'ont découvert. Un nombre restreint n'acheterais pas à cause de ça.")),
    (3, _(u"3 - Certains utilisateurs n'achèteront probablement pas le produit. Sera indiqué dans un test. Clairement un problème notable.")),
    (4, _(u"4 - Majeur - Un utilisateur retournerait le produit. L'équipe doit stopper toute sortie pour ce bug.")),
    (5, _(u"5 - Critique - Bloque toute progression dans le travail quotidien.")),
) 
# Choix prédéfinis pour la redondance du problème
LIKELIHOOD_CHOICES = (
    (1, _(u"1 - Affecte pour ainsi dire personne.")),
    (2, _(u"2 - Affecte seulement quelques personnes (<=25%).")),
    (3, _(u"3 - Affecte près de la moitié des personnes (>25% & <=75%).")),
    (4, _(u"4 - Affecte la plupart des joueurs (>75%).")),
    (5, _(u"5 - Affecte toutes les personnes.")),
)

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
	name = models.CharField( _(u"Nom de l'étape"), max_length=50 )

	description = models.TextField( _(u"Description"), blank=True,
									help_text="Le but, ici, est de noter les enjeux de l'étape, les modules à implémenter par exemple."
									"Une fois arrivé dans les étapes publiques il y a de fortes chances qu'il n'y ai plus grand chose"
									"à décrire dans cette section." )

	max_pain_level = models.SmallIntegerField( _(u"Niveau Maximum de Pénibilité"), default=DEFAULT_MILESTONE_MAXIMUM_PAIN_LEVEL,
											   help_text="Le principe, c'est que cette étape ne devrait pas être finie "
											   "tant qu'il reste des tickets dont le niveau de pénibilité est supérieur "
											   "à cette valeur." )

	public = models.BooleanField(_(u"Publique"), default=False, 
								 help_text="À savoir si cette étape est une étape de développement interne (itération, milestone), "
								 "ou une étape de développement publique (release candidate, alpha, beta, version 1, 2, etc..." )

	active = models.BooleanField(_(u'Actif'), default=False,
								 help_text="Indique si cette étape est l'étape en cours dans le cycle de développement. "
								 "La méthode <i>save</i> du model a été réécrite pour empêcher que deux étape soit active "
								 "en même temps, par contre rien n'empêche qu'aucune étape ne soit active.")

	creation_date = models.DateTimeField ( _(u"Date de création"), 
										   auto_now_add=True )

	update_date = models.DateTimeField ( _(u"Date de modification"), 
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
	name = models.CharField( _(u"Nom du composant"), max_length=50 )
	description = models.TextField( _(u"Description"), blank=True,
									help_text="Une brève description de ce composant et de son rôle dans le programme." )

	creation_date = models.DateTimeField ( _(u"Date de création"), 
										   auto_now_add=True )

	update_date = models.DateTimeField ( _(u"Date de modification"), 
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
	name = models.CharField( _(u"Intitulé du Ticket"), max_length=100, 
							 help_text="Essayez de donner une description la plus précise et concise possible "
							 "de la nature du problème, tel que : <br/>"
							 "<i>Disparition d'un sprite suite à une collision.</i><br/>"
							 "<i>Résultats non sauvegardés en fin de partie.</i>" )

	description = models.TextField( _(u"Description"), blank=True,
									help_text="Une bonne description de bug se compose de quatre parties :<br/><i>"
									"<b>1</b> - La procédure permettant de reproduire le bug, si elle est connue, "
									"autrement une description du contexte dans lequel le bug se produit, "
									"les conditions de l'application à ce moment.<br/>"
									"<b>2</b> - Le résultat actuel, à quoi conduit le bug.<br/>"
									"<b>3</b> - Le résultat espéré, comment devrait se comporter l'application "
									"en temps normal.<br/>"
									"<b>4</b> - Un Workaround, s'il est possible d'en avoir un, et si celui-ci "
									"est connu, permettant de contourner le problème.</i>" )

	pain = models.FloatField( _(u"Pénibilité Utilisateur"), 
							  editable=False )

	type = models.SmallIntegerField( _(u"De quel type de bug s'agit-il ?"), 
									 choices=TYPE_CHOICES,
									 help_text="Sélectionnez la valeur correspondant "
													 "au problème que vous rencontrez." )

	priority = models.SmallIntegerField( _(u"De quel manière ce bug vous affecte t'il ?"), 
										 choices=PRIORITY_CHOICES,
										 help_text="Sélectionnez la valeur correspondant au problème "
														"que vous rencontrez." )

	likelihood = models.SmallIntegerField( _(u"Dans quelle proportions ce bug ce manifeste t'il ?"), 
										   choices=LIKELIHOOD_CHOICES,
										   help_text="Sélectionnez la valeur correspondant au problème "
															"que vous rencontrez." )

	active = models.BooleanField(_(u"Actif"), 
								 default=True, 
								 help_text="Le ticket est <i>actif</i> tant qu'il n'a pas été corrigé "
												"ou jugé incorrigible." )

	component = models.ForeignKey ( "bugs.Component", 
								  verbose_name= _(u"Composant"), 
								  related_name="ticket_component",
								  help_text="Le composant concerné par ce ticket."  )

	creator = models.ForeignKey ( "auth.User", 
								  verbose_name= _(u"Créateur"), 
								  related_name="ticket_creator" )

	reviewer = models.ForeignKey ( "auth.User", 
								   verbose_name= _(u"Affectation"), 
								   related_name="ticket_reviewer", 
								   null=True, 
								   blank=True,
								   help_text="L'utilisateur prenant en charge ce ticket." )

	planified_to_milestone = models.ForeignKey ( "bugs.Milestone", 
														 verbose_name= _(u"Planification"), 
														 related_name="ticket_planified_to_milestone", 
														 null=True, 
														 blank=True,
														 help_text="Étape pour laquelle la résolution de "
																		 "ce ticket est planifiée." )

	closed_in_milestone = models.ForeignKey ( "bugs.Milestone", 
														verbose_name= _(u"Étape de fin"), 
														related_name="ticket_closed_in_milestone", 
														null=True, 
														blank=True,
														help_text="Étape à laquelle le ticket a été fermé." )

	creation_date = models.DateTimeField ( _(u"Date de création"), 
										   auto_now_add=True )

	update_date = models.DateTimeField ( _(u"Date de modification"), 
										 auto_now=True )

	allow_comments = models.BooleanField(_(u"Commentable"),  default=True )

	def pain_as_int (self):
		return int(self.pain)

	def block_milestone (self):
		return self.pain >= MileStone.active_milestone().max_pain_level

	def is_affected (self):
		return self.reviewer is not None

	def is_done(self):
		return self.active is False

	def save(self, **kwargs):
		self.pain = self.type * self.likelihood * self.priority * 100.0 / MAX_POSSIBLE_PAIN_SCORE
		super(Ticket, self).save(**kwargs)
	
	def comments_count(self):
		if self.allow_comments :
			return Comment.objects.filter(object_pk=self.id,).count()
		else :
			return _(u"None")
	comments_count.short_description = _(u"Commentaires")

	@models.permalink
	def get_absolute_url(self):
		return ( 'ticket_detail', (),  {'num':self.id} )

	def __unicode__(self): 
		return u'%s' % self.name 

	class Meta: 
		ordering = ('-pain',) 
		verbose_name = _(u'Ticket') 
		verbose_name_plural = _(u'Tickets')
