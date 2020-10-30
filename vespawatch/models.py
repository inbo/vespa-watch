import os
from datetime import datetime, date

import dateparser
import requests
import logging
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField
from django.contrib.gis.db import models
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.files.base import ContentFile
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.db.models import Q
from django.template import defaultfilters
from django.urls import reverse
from django.utils import timezone
from django.utils.timezone import is_naive, make_aware, now
from django.utils.translation import ugettext_lazy as _
from django_cleanup.signals import cleanup_pre_delete, cleanup_post_delete
from imagekit.models import ImageSpecField
from markdownx.models import MarkdownxField
from pilkit.processors import SmartResize
from pyinaturalist.rest_api import create_observations, add_photo_to_observation

from vespawatch.utils import make_unique_filename

INAT_VV_TAXONS_IDS = (119019, 560197) # At iNaturalist, those taxon IDS represents Vespa velutina and subspecies

logger = logging.getLogger(__name__)


def get_taxon_from_inat_taxon_id(inaturalist_taxon_id):
    """ Raises Taxon.DoesNotExists().

    Raises Taxon.MultipleObjectsReturned() if several matches, which shouldn't happen."""
    return Taxon.objects.get(inaturalist_pull_taxon_ids__contains=[inaturalist_taxon_id])


class Taxon(models.Model):
    name = models.CharField(verbose_name=_("Scientific name"), max_length=100)

    vernacular_name = models.CharField(verbose_name=_("Vernacular name"), max_length=100, blank=True)

    inaturalist_push_taxon_id = models.BigIntegerField(null=True, blank=True,
                                                       help_text="When pushing an observation to iNaturalist, we'll "
                                                                 "use this taxon_id")
    inaturalist_pull_taxon_ids = ArrayField(models.BigIntegerField(), blank=True, null=True,
                                            help_text="When pulling observations from iNaturalist, reconcile according "
                                                      "to those IDs.")

    # Don't use @staticmethod, Django can't serialize this and this is painful to debug.
    def get_file_path(filename):
        """
        This function is no longer used, but we have to keep it to avoid breaking our migrations
        (in particular, this function is used in 0001_initial.py)
        """
        return os.path.join('taxon_identification_pictures/', make_unique_filename(filename))

    @property
    def inat_pictures_link(self):
        return f'https://www.inaturalist.org/taxa/{self.inaturalist_push_taxon_id}/browse_photos?quality_grade=research'

    def __str__(self):
        return self.name

    def to_json(self):
        identification_picture_indiv_url = None
        if self.identification_picture_individual:
            identification_picture_indiv_url = self.identification_picture_individual.url

        identification_picture_nest_url = None
        if self.identification_picture_nest:
            identification_picture_nest_url = self.identification_picture_nest.url

        return {
            'id': self.pk,
            'name': self.name,
            'identification_priority': self.identification_priority,
            'identification_picture_individual_url': identification_picture_indiv_url,
            'identification_picture_nest_url': identification_picture_nest_url
        }

    class Meta:
        verbose_name_plural = "taxa"


class IdentificationCard(models.Model):
    represented_taxon = models.ForeignKey(Taxon, on_delete=models.PROTECT)
    represents_nest = models.BooleanField()

    # Don't use @staticmethod, Django can't serialize this and this is painful to debug.
    def get_file_path(filename):
        return os.path.join('pictures/identification_cards/', make_unique_filename(filename))

    identification_picture = models.ImageField(verbose_name=_("Photo for identification"), upload_to=get_file_path, blank=True, null=True)

    order = models.IntegerField(verbose_name=_("Order"), unique=True)  # The order in which the cards are shown

    description = MarkdownxField(verbose_name=_("Description"), blank=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        card_type = 'nest' if self.represents_nest else 'individual'
        return f'Card for {self.represented_taxon.name} ({card_type})'


class InatCreatedObservationsManager(models.Manager):
    """The queryset only contains observations that originates from iNaturalist (NOT Vespa-Watch)"""
    def get_queryset(self):
        return super().get_queryset().filter(originates_in_vespawatch=False)


class VespawatchCreatedObservationsManager(models.Manager):
    """The queryset only contains observations that originates from Vespa-Watch"""
    def get_queryset(self):
        return super().get_queryset().filter(originates_in_vespawatch=True)


class VespawatchNewlyCreatedObservationsManager(models.Manager):
    """The queryset contains only observations that were created in vespawatch and have no iNaturalist id yet"""
    def get_queryset(self):
        return super().get_queryset().filter(originates_in_vespawatch=True, inaturalist_id__isnull=True)


class TaxonMatchError(Exception):
    """Unable to match this (iNaturalist) taxon id to our Taxon table"""

class ParseDateError(Exception):
    """Cannot parse this date"""

def inat_data_confirms_vv(inaturalist_data):
    """Takes a bunch of data coming from inaturalist and returns a value according to the community ID:

        - True if community agrees to Vespa Velutina
        - False if community says it's NOT V. V.
        - None if no community agreement
    """
    if 'community_taxon_id' in inaturalist_data:
        if inaturalist_data['community_taxon_id'] is None:
            return None
        else:
            taxon_id = int(inaturalist_data['community_taxon_id'])
            return taxon_id in INAT_VV_TAXONS_IDS
    else:
        # no data
        return None


def create_observation_from_inat_data(inaturalist_data):
    """Creates an observation in our local database according to the data from iNaturalist API.

    :returns: the observation (instance of Nest or Individual) created.

    Raises:
        TaxonMatchError
    """
    observation_time = dateparser.parse(inaturalist_data['observed_on_string'],
                                        settings={'TIMEZONE': inaturalist_data['observed_time_zone']})
    if observation_time is None:
        # Sometimes, dateparser doesn't understand the string but we have the bits and pieces in
        # inaturalist_data['observed_on_details']
        details = inaturalist_data['observed_on_details']
        observation_time = datetime(year=details['year'],
                                    month=details['month'],
                                    day=details['day'],
                                    hour=details['hour'])  # in the observed cases, we had nothing more precise than the
                                                           # hour

    # Sometimes, the time is naive (even when specifying it to dateparser), because (for the detected cases, at least)
    # The time is 00:00:00. In that case we make it aware to avoid Django warnings (in the local time zone since all
    # observations occur in Belgium
    if is_naive(observation_time):
        # Some dates (apparently)
        observation_time = make_aware(observation_time)

    if observation_time:
        # Reconcile the taxon
        try:
            taxon = get_taxon_from_inat_taxon_id(inaturalist_data['taxon']['id'])
        except Taxon.DoesNotExist:
            raise TaxonMatchError

        inat_vv_confirmed = inat_data_confirms_vv(inaturalist_data)

        # Check if it has the vespawatch_evidence observation field value and if it's set to "nest"
        if 'ofvs' in inaturalist_data:
            is_nest_ofv = next((item for item in inaturalist_data['ofvs'] if item["field_id"] == settings.VESPAWATCH_EVIDENCE_OBS_FIELD_ID), None)
        else:
            is_nest_ofv = None
        if is_nest_ofv and is_nest_ofv['value'] == "nest":
            created = Nest.objects.create(
                inat_vv_confirmed=inat_vv_confirmed,
                originates_in_vespawatch=False,
                inaturalist_id=inaturalist_data['id'],
                taxon=taxon,
                latitude=inaturalist_data['geojson']['coordinates'][1],
                longitude=inaturalist_data['geojson']['coordinates'][0],
                observation_time=observation_time)  # TODO: What to do with iNat observations without (parsable) time?
        else:  # Default is specimen
            created = Individual.objects.create(
                inat_vv_confirmed=inat_vv_confirmed,
                originates_in_vespawatch=False,
                inaturalist_id=inaturalist_data['id'],
                taxon=taxon,
                latitude=inaturalist_data['geojson']['coordinates'][1],
                longitude=inaturalist_data['geojson']['coordinates'][0],
                observation_time=observation_time)  # TODO: What to do with iNat observations without (parsable) time?

        for photo in inaturalist_data['photos']:
            created.assign_picture_from_url(photo['url'])

        return created
    else:
        raise ParseDateError


def get_local_obs_matching_inat_id(inat_id):
    """Returns a Nest or an Individual, raise ObjectDoesNotExist if nothing is found."""
    models_to_search = [Nest, Individual]
    for model in models_to_search:
        try:
            return model.objects.get(inaturalist_id=inat_id)
        except model.DoesNotExist:
            pass

    raise ObjectDoesNotExist


def no_future(value):
    today = date.today()
    if value.date() > today:
        raise ValidationError(_('Observation date cannot be in the future.'))


class AbstractObservation(models.Model):
    originates_in_vespawatch = models.BooleanField(default=True, help_text="The observation was first created in VespaWatch, not iNaturalist")
    taxon = models.ForeignKey(Taxon, on_delete=models.PROTECT, blank=True, null=True)
    observation_time = models.DateTimeField(verbose_name=_("Observation date"), validators=[no_future])
    comments = models.TextField(verbose_name=_("Comments"), blank=True, help_text=_("Comments are public: use them to describe your observation and help verification."))

    latitude = models.FloatField(validators=[MinValueValidator(-90), MaxValueValidator(90)], verbose_name=_("Latitude"))
    longitude = models.FloatField(validators=[MinValueValidator(-180), MaxValueValidator(180)], verbose_name=_("Longitude"))

    inaturalist_id = models.BigIntegerField(verbose_name=_("iNaturalist ID"), blank=True, null=True)
    inaturalist_species = models.CharField(verbose_name=_("iNaturalist species"), max_length=100, blank=True, null=True)  # TODO: check if this is still in use or useful
    inat_vv_confirmed = models.BooleanField(blank=True, null=True)  # The community ID of iNaturalist says it's Vespa Velutina

    # Observer info
    observer_name = models.CharField(verbose_name=_("Name"), max_length=255, blank=True, null=True)
    observer_email = models.EmailField(verbose_name=_("Email address"), blank=True, null=True)
    observer_phone = models.CharField(verbose_name=_("Telephone number"), max_length=20, blank=True, null=True)

    created_at = models.DateTimeField(default=timezone.now)

    # Managers
    objects = models.Manager()  # The default manager.
    from_inat_objects = InatCreatedObservationsManager()
    from_vespawatch_objects = VespawatchCreatedObservationsManager()
    new_vespawatch_objects = VespawatchNewlyCreatedObservationsManager()

    class Meta:
        abstract = True
        # We got some duplicates and don't exactly know why, this is an attempt to block them without being too
        # aggresive and introduce bugs (hence the limited number of fields).
        unique_together = ['taxon', 'observation_time', 'latitude', 'longitude', 'comments', 'inaturalist_id']

    @property
    def vernacular_names_in_all_languages(self):
        """Returns a dict such as: {'en': XXXX, 'nl': YYYY}"""
        vn = {}
        for lang in settings.LANGUAGES:
            code = lang[0]
            vn[code] = getattr(self.taxon, f'vernacular_name_{code}')
        return vn

    @property
    def display_vernacular_name(self):
        if self.taxon:
            return _(self.taxon.vernacular_name)
        else:
            return ''

    @property
    def display_scientific_name(self):
        if self.taxon:
            return self.taxon.name
        else:
            return self.inaturalist_species or _('Unknown')

    @property
    def can_be_edited_in_admin(self):
        if self.originates_in_vespawatch:
            if self.exists_in_inaturalist:
                return False
            else:
                return True
        else:  # Comes from iNaturalist: we can never delete
            return False


    @property
    def can_be_edited_or_deleted(self):
        """Return True if this observation can be edited in Vespa-Watch (admin, ...)"""
        return self.originates_in_vespawatch  # We can't edit obs that comes from iNaturalist (they're never pushed).

    @property
    def taxon_can_be_locally_changed(self):
        if self.originates_in_vespawatch and self.exists_in_inaturalist:
            return False  # Because we rely on community: info is always pulled and never pushed

        return True

    @property
    def exists_in_inaturalist(self):
        return self.inaturalist_id is not None

    @property
    def inaturalist_obs_url(self):
        if self.exists_in_inaturalist:
            return f'https://www.inaturalist.org/observations/{self.inaturalist_id}'

        return None

    def has_warnings(self):
        return len(self.warnings.all()) > 0
    has_warnings.boolean = True

    def _params_for_inat(self):
        """(Create/update): Common ground for the pushed data to iNaturalist.

        taxon_id is not part of it because we rely on iNaturalist to correct the identification, if necessary.
        All the rest is pushed.
        """

        vespawatch_evidence_value = 'nest' if self.__class__ == Nest else 'individual'

        ofv = [{'observation_field_id': settings.VESPAWATCH_ID_OBS_FIELD_ID, 'value': self.pk},
               {'observation_field_id': settings.VESPAWATCH_EVIDENCE_OBS_FIELD_ID, 'value': vespawatch_evidence_value}]

        if vespawatch_evidence_value == 'individual' and self.behaviour:
            ofv.append({'observation_field_id': settings.VESPAWATCH_BEHAVIOUR_OBS_FIELD_ID, 'value': self.get_behaviour_display()})  # TODO: get_behaviour_display(): what will happen to push if we translate the values for the UI

        return {'observed_on_string': self.observation_time.isoformat(),
                'time_zone': 'Brussels',
                'description': self.comments,
                'latitude': self.latitude,
                'longitude': self.longitude,

                'observation_field_values_attributes':
                    [{'observation_field_id': settings.VESPAWATCH_ID_OBS_FIELD_ID, 'value': self.pk},
                    {'observation_field_id': settings.VESPAWATCH_EVIDENCE_OBS_FIELD_ID, 'value': vespawatch_evidence_value}]
                }

    def flag_warning(self, text):
        if text in [x.text for x in self.warnings.all()]:
            return  # warning already set
        if self.__class__.__name__ == 'Nest':
            warning = NestObservationWarning(text=text, datetime=now(),
                                             observation=self)
            warning.save()
        elif self.__class__.__name__ == 'Individual':
            warning = IndividualObservationWarning(text=text, datetime=now(),
                                                   observation=self)
            warning.save()

    def flag_based_on_inat_data(self, inat_observation_data):
        """
        The observation was no longer found on iNaturalist with our general filters.
        Check why, and flag this observation
        """
        # Project is vespawatch?
        if not settings.VESPAWATCH_PROJECT_ID in inat_observation_data['project_ids']:
            self.flag_warning('not in vespawatch project')

        # Taxon known in VW?
        returned_taxon_id = ''
        if 'community_taxon_id' in inat_observation_data and inat_observation_data['community_taxon_id']:
            returned_taxon_id = inat_observation_data['community_taxon_id']
        elif 'taxon' in inat_observation_data:
            if 'id' in inat_observation_data['taxon']:
                returned_taxon_id = inat_observation_data['taxon']['id']
        if returned_taxon_id not in [y for x in Taxon.objects.all() for y in x.inaturalist_pull_taxon_ids]:
            self.flag_warning('unknown taxon')

    def update_from_inat_data(self, inat_observation_data):
        # Check the vespawatch_evidence
        # ------
        # If the observation is a nest but the vespawatch evidence is not nest => flag the nest
        if 'ofvs' in inat_observation_data:
            vw_evidence_list = [x['value'] for x in inat_observation_data['ofvs'] if x['field_id'] == settings.VESPAWATCH_EVIDENCE_OBS_FIELD_ID]
            if len(vw_evidence_list) > 0:
                vw_evidence = vw_evidence_list[0]

                if self.__class__.__name__ == 'Nest':
                    if vw_evidence != 'nest':
                        self.flag_warning('individual at inaturalist')
                # If the observation is an individual but the vespawatch evidence is a nest and the observation originates in vespawatch => delete the individual and create a nest
                elif self.__class__.__name__ == 'Individual':
                    if vw_evidence == 'nest':
                        if self.originates_in_vespawatch:
                            self.flag_warning('nest at inaturalist')
                        else:
                            create_observation_from_inat_data(inat_observation_data)
                            self.delete()
                            return

        # Update taxon data and set inat_vv_confirmed (use inat_data_confirms_vv() )
        self.inat_vv_confirmed = inat_data_confirms_vv(inat_observation_data)

        # Update photos
        # -------------
        # When we pull again and the API returns additional images, those are not added. This is done
        # because we insert a UUID in the filename when we pull it. The result of that is that we cannot
        # compare that image with the image url that we retrieve from iNaturalist. So to prevent adding
        # the same image again and again with subsequent pulls, we only add images when the observation
        # has none.
        if len(self.pictures.all()) == 0:
            for photo in inat_observation_data['photos']:
                self.assign_picture_from_url(photo['url'])

        # Update location
        self.latitude = inat_observation_data['geojson']['coordinates'][1]
        self.longitude = inat_observation_data['geojson']['coordinates'][0]

        # Update time
        # -------------
        observation_time = dateparser.parse(inat_observation_data['observed_on_string'],
                                            settings={'TIMEZONE': inat_observation_data['observed_time_zone']})
        if observation_time is None:
            # Sometimes, dateparser doesn't understand the string but we have the bits and pieces in
            # inaturalist_data['observed_on_details']
            details = inat_observation_data['observed_on_details']
            observation_time = datetime(year=details['year'],
                                        month=details['month'],
                                        day=details['day'],
                                        hour=details[
                                            'hour'])  # in the observed cases, we had nothing more precise than the hour

        # Sometimes, the time is naive (even when specifying it to dateparser), because (for the detected cases, at least)
        # The time is 00:00:00. In that case we make it aware to avoid Django warnings (in the local time zone since all
        # observations occur in Belgium
        if is_naive(observation_time):
            # Some dates (apparently)
            observation_time = make_aware(observation_time)

        self.observation_time = observation_time

        self.comments = inat_observation_data['description'] or ''


        # Update taxon
        # -------------
        try:
            self.inaturalist_species = ''
            taxon = get_taxon_from_inat_taxon_id(inat_observation_data['taxon']['id'])
            self.taxon = taxon
        except Taxon.DoesNotExist:
            self.taxon = None
            self.inaturalist_species = inat_observation_data['taxon']['name'] if 'name' in inat_observation_data['taxon'] else ''

        self.save()

    def create_at_inaturalist(self, access_token, user_agent):
        """Creates a new observation at iNaturalist for this observation

        It will update the current object so self.inaturalist_id is properly set.
        On the other side, it will also set the vespawatch_id observation field so the observation can be found from
        the iNaturalist record.

        :param access_token: as returned by pyinaturalist.rest_api.get_access_token(
        """

        params_only_for_create = {'taxon_id': self.taxon.inaturalist_push_taxon_id}  # TODO: with the new sync, does it still makes sense to separate the create/update parameters?

        params = {
            'observation': {**params_only_for_create, **self._params_for_inat()}
        }

        r = create_observations(params=params, access_token=access_token, user_agent=user_agent)
        self.inaturalist_id = r[0]['id']
        self.save()
        self.push_attached_pictures_at_inaturalist(access_token=access_token, user_agent=user_agent)

    def get_photo_filename(self, photo_url):
        # TODO: Find a cleaner solution to this
        # It seems the iNaturalist only returns small thumbnails such as
        # 'https://static.inaturalist.org/photos/1960816/square.jpg?1444437211'
        # We can circumvent the issue by hacking the URL...
        photo_url = photo_url.replace('square.jpg', 'large.jpg')
        photo_url = photo_url.replace('square.jpeg', 'large.jpeg')
        photo_filename = photo_url[photo_url.rfind("/")+1:].split('?',1)[0]
        return photo_filename

    def assign_picture_from_url(self, photo_url):
        photo_filename = self.get_photo_filename(photo_url)
        if photo_filename not in [x.image.name for x in self.pictures.all()]:
            if self.__class__ == Nest:
                photo_obj = NestPicture()
            else:
                photo_obj = IndividualPicture()

            photo_content = ContentFile(requests.get(photo_url).content)

            photo_obj.observation = self
            photo_obj.image.save(photo_filename, photo_content)
            photo_obj.save()

    def push_attached_pictures_at_inaturalist(self, access_token, user_agent):
        if self.inaturalist_id:
            for picture in self.pictures.all():
                add_photo_to_observation(observation_id=self.inaturalist_id,
                                         file_object=picture.image.read(),
                                         access_token=access_token,
                                         user_agent=user_agent)

    def get_taxon_name(self):
        if self.taxon:
            return self.taxon.name
        else:
            return ''

    @property
    def formatted_observation_date(self):
        # We need to be aware of the timezone, hence the defaultfilter trick
        return defaultfilters.date(self.observation_time, 'Y-m-d')

    @property
    def observation_time_iso(self):
        return self.observation_time.isoformat()

    def save(self, *args, **kwargs):
        # Let's make sure model.clean() is called on each save(), for validation
        self.full_clean()

        return super(AbstractObservation, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.originates_in_vespawatch and self.exists_in_inaturalist:
            InatObsToDelete.objects.create(inaturalist_id=self.inaturalist_id)

        return super(AbstractObservation, self).delete(*args, **kwargs)


class Nest(AbstractObservation):
    duplicate_of = models.ForeignKey('self', on_delete=models.PROTECT, blank=True, null=True)

    LESS_THAN_25_CM = 'LESS_25_CM'
    MORE_THAN_25_CM = 'MORE_25_CM'
    SIZE_CHOICES = (
        (LESS_THAN_25_CM, _("Less than 25cm")),
        (MORE_THAN_25_CM, _("More than 25cm"))
    )
    size = models.CharField(verbose_name=_("Nest size"), max_length=50, choices=SIZE_CHOICES, blank=True)

    BELOW_4_METER = 'BELOW_4_M'
    ABOVE_4_METER = 'BELOW_4_M'
    HEIGHT_CHOICES = (
        (BELOW_4_METER, _("Below 4 meters")),
        (ABOVE_4_METER, _("Above 4 meters"))
    )
    height = models.CharField(verbose_name=_("Nest height"), max_length=50, choices=HEIGHT_CHOICES, blank=True)  # Will be set to required in the form, but can be empty for iNaturalist observations
    expert_vv_confirmed = models.BooleanField(verbose_name=_('Confirmed by expert'), blank=True, null=True)
    municipality = models.CharField(max_length=255, verbose_name=_('Municipality'), blank=True, null=True)

    def get_absolute_url(self):
        return reverse('vespawatch:nest-detail', kwargs={'pk': self.pk})

    def editable_by_user(self, user):
        if not user:
            return False
        if not self.controlled:
            return True
        if self.managementaction.user.pk is not user.pk and not user.is_staff:
            return False
        return True

    @property
    def controlled(self):
        return hasattr(self, 'managementaction')

    @property
    def subject(self):
        return 'nest'

    def as_dict(self, request_user=None, include_pictures=True):
        d = {
            'id': self.pk,
            'key': f'nest-{self.pk}',  # Handy when you need a unique key in a batch of Observations (nests and individuals)
            'display_scientific_name': self.display_scientific_name,
            'display_vernacular_name': self.display_vernacular_name,
            'editable': self.editable_by_user(request_user),  # the management action of this nest is only editable by the user who created it, or by an admin (=staff) user
            'subject': self.subject,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'inaturalist_id': self.inaturalist_id,
            'inaturalist_url': self.inaturalist_obs_url,
            'inat_vv_confirmed': self.inat_vv_confirmed,
            'observation_time': self.observation_time.timestamp() * 1000,
            'municipality': self.municipality,
            'comments': self.comments,
            'action': self.managementaction.get_outcome_display() if self.controlled else '',
            'actionCode': self.managementaction.outcome if self.controlled else '',
            'actionId': self.managementaction.pk if self.controlled else '',
            'actionFinished': self.controlled,
            'originates_in_vespawatch': self.  originates_in_vespawatch,
            'detailsUrl': reverse('vespawatch:nest-detail', kwargs={'pk': self.pk}),
        }
        if include_pictures:
            d['images'] = [x.image.url for x in self.pictures.all()]
            d['thumbnails'] = [x.thumbnail.url for x in self.pictures.all()]
        return d

    def __str__(self):
        return f'Nest of {self.get_taxon_name()}, {self.formatted_observation_date}'


class Individual(AbstractObservation):
    HUNTING = 'HU'
    FLOWER = 'FL'
    OTHER = 'OT'
    NEAR_WOOD = 'WO'
    NEAR_WATER = 'WA'
    FLYING = 'FG'
    CAPTURED = 'CA'
    DEAD = 'DE'

    BEHAVIOUR_CHOICES = (
        (HUNTING, _('Hunting at beehive')),
        (FLOWER, _('Drinking nectar on flower')),
        (NEAR_WOOD, _('Near wood source')),
        (NEAR_WATER, _('Near water source')),
        (FLYING, _('Flying')),
        (CAPTURED, _('Captured')),
        (DEAD, _('Dead')),
        (OTHER, _('Other'))
    )

    # Fields
    individual_count = models.IntegerField(verbose_name=_("Individual count"), blank=True, null=True)
    behaviour = models.CharField(verbose_name=_("Behaviour"), max_length=2, choices=BEHAVIOUR_CHOICES, blank=True, null=True)

    def get_absolute_url(self):
        return reverse('vespawatch:individual-detail', kwargs={'pk': self.pk})

    @property
    def subject(self):
        return 'individual'

    def as_dict(self):
        return {
            'id': self.pk,
            'key': f'individual-{self.pk}',  # Handy when you need a unique key in a batch of Observations (nests and individuals)
            'display_scientific_name': self.display_scientific_name,
            'display_vernacular_name': self.display_vernacular_name,
            'subject': self.subject,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'inaturalist_id': self.inaturalist_id,
            'inaturalist_url': self.inaturalist_obs_url,
            'inat_vv_confirmed': self.inat_vv_confirmed,
            'observation_time': self.observation_time.timestamp() * 1000,
            'comments': self.comments,
            'images': [x.image.url for x in self.pictures.all()],
            'thumbnails': [x.thumbnail.url for x in self.pictures.all()]
        }

    def __str__(self):
        return f'Individual of {self.get_taxon_name()}, {self.formatted_observation_date}'


class IndividualPicture(models.Model):
    def get_file_path(instance, filename):
        return os.path.join('pictures/individuals/', make_unique_filename(filename))

    observation = models.ForeignKey(Individual, on_delete=models.CASCADE, related_name='pictures', blank=True, null=True)
    datetime = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(verbose_name=_("Photo"), upload_to=get_file_path)
    thumbnail = ImageSpecField(source='image',
                               processors=[SmartResize(600, 300)],
                               format='JPEG',
                               options={'quality': 90})

    def to_dict(self):
        return {'url': self.image.url, 'name': self.image.name}


class NestPicture(models.Model):
    def get_file_path(instance, filename):
        return os.path.join('pictures/nests/', make_unique_filename(filename))

    observation = models.ForeignKey(Nest, on_delete=models.CASCADE, related_name='pictures', blank=True, null=True)
    datetime = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(verbose_name=_("Photo"), upload_to=get_file_path)
    thumbnail = ImageSpecField(source='image',
                               processors=[SmartResize(600, 300)],
                               format='JPEG',
                               options={'quality': 90})

    def to_dict(self):
        return {'url': self.image.url, 'name': self.image.name}


class ObservationWarningBase(models.Model):
    text = models.CharField(max_length=255)
    datetime = models.DateTimeField()

    class Meta:
        abstract = True


class IndividualObservationWarning(ObservationWarningBase):
    observation = models.ForeignKey(Individual, on_delete=models.CASCADE, related_name='warnings')


class NestObservationWarning(ObservationWarningBase):
    observation = models.ForeignKey(Nest, on_delete=models.CASCADE, related_name='warnings')


class ManagementAction(models.Model):
    PERMAS_D_PROF = 'PP'
    PERMAS_D_CLASSIC = 'PC'
    REMOVAL_COMPLETE = 'FD'  # previously "full destruction": possible cleanup: create a data migration so FD -> RC?
    REMOVAL_PARTIAL = 'PD'   # previously "partial destruction": possible cleanup: create a data migration so PD -> RP?
    NOT_TREATED = 'ND'  # previously "nothing done": : possible cleanup: create a data migration so ND -> NT?
    UNKNOWN = 'UK'

    OUTCOME_CHOICE = (
        (PERMAS_D_PROF, _('Professional permas-D treatment')),
        (PERMAS_D_CLASSIC, _('Classic permas-D treatment')),
        (REMOVAL_COMPLETE, _('Complete manual removal')),
        (REMOVAL_PARTIAL, _('Partial manual removal')),
        (NOT_TREATED, _('Not treated')),
        (UNKNOWN, _('Unknown')),
    )

    nest = models.OneToOneField(Nest, on_delete=models.CASCADE, primary_key=True)
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    outcome = models.CharField(verbose_name=_("Outcome"), max_length=2, choices=OUTCOME_CHOICE)
    action_time = models.DateTimeField(verbose_name=_("Date and time"))
    person_name = models.CharField(verbose_name=_("Reported by"), max_length=255, blank=True)
    duration = models.DurationField(verbose_name=_("Duration (in minutes)"), null=True, blank=True)
    number_of_persons = models.IntegerField(verbose_name=_("Number of persons"), null=True)
    comments = models.TextField(verbose_name=_("Comments"), blank=True)

    @property
    def duration_in_seconds(self):
        try:
            return self.duration.total_seconds()  # Positive val, but also 0!
        except AttributeError:
            return '' # NULL

    def __str__(self):
        return f'{self.action_time.strftime("%Y-%m-%d")} {self.get_outcome_display()}'


class InatObsToDelete(models.Model):
    """This model is used to store iNaturalist IDs for deleted observation, so they can be also deleted @inat on the
    subsequent push operation"""
    inaturalist_id = models.BigIntegerField()

    def __str__(self):
        return str(self.inaturalist_id)


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    organization = models.CharField(verbose_name=_('Organization / business'), max_length=255, null=True, blank=True)
    description = models.TextField(verbose_name=_('Description'), blank=True, help_text=_('Describe the activities of your organization / business.'))

    alphanumeric = RegexValidator(r'^[0-9]*$', _('Only numbers are allowed.'))

    phone = models.CharField(verbose_name=_("Telephone number"), max_length=20, blank=True, null=True,
                             validators=[alphanumeric])
    email_notification = models.BooleanField(verbose_name=_('Get email notifications for new nests'), default=True)

    def __str__(self):
        return str(self.user)


def get_observations(include_individuals=True, include_nests=True, limit=None):
    obs = []

    if include_individuals:
        obs = obs + list(Individual.objects.select_related('taxon').prefetch_related('pictures').all().order_by('-observation_time')[:limit])
    if include_nests:
        obs = obs + list(Nest.objects.select_related('taxon').prefetch_related('pictures').all().order_by('-observation_time')[:limit])

    obs.sort(key=lambda x: x.observation_time, reverse=True)

    obs = obs[:limit]

    return obs


def get_individuals(limit=None, vv_only=True, flanders_only=False):
    qs = Individual.objects.all()
    if vv_only:
        qs = qs.filter(taxon__inaturalist_push_taxon_id__in=INAT_VV_TAXONS_IDS)
    if flanders_only:
        qs = qs.filter(longitude__gte=2.53, longitude__lte=5.94, latitude__gte=50.67, latitude__lte=51.51)
    obs = list(qs.select_related('taxon').prefetch_related('pictures').all())
    obs.sort(key=lambda x: x.observation_time, reverse=True)
    obs = obs[:limit]
    return obs


def get_nests(limit=None, vv_only=True, confirmed_only=False, flanders_only=False):
    qs = Nest.objects.all()
    if confirmed_only:
        # When you request confirmed_only=True, this can either be iNaturalist confirmed OR expert confirmed
        qs = qs.filter(Q(inat_vv_confirmed=True) | Q(expert_vv_confirmed=True))
    if vv_only:
        qs = qs.filter(taxon__inaturalist_push_taxon_id__in=INAT_VV_TAXONS_IDS)
    if flanders_only:
        qs = qs.filter(longitude__gte=2.53, longitude__lte=5.94, latitude__gte=50.67, latitude__lte=51.51)
    obs = list(qs.select_related('taxon').prefetch_related('pictures').all())
    obs.sort(key=lambda x: x.observation_time, reverse=True)
    obs = obs[:limit]
    return obs


def get_local_observation_with_inaturalist_id(inaturalist_id):
    # Returns None if not found
    for obs in get_observations():
        if obs.inaturalist_id == inaturalist_id:
            return obs

    return None


def get_missing_at_inat_observations(pulled_inat_ids):
    """
    Get all observations that exist in our database with an iNaturalist ID but that were not returned by the
    iNaturalist pull.
    """
    missing_indiv = Individual.objects.all().filter(inaturalist_id__isnull=False).exclude(inaturalist_id__in=pulled_inat_ids)
    missing_nests = Nest.objects.all().filter(inaturalist_id__isnull=False).exclude(inaturalist_id__in=pulled_inat_ids)
    return list(missing_indiv) + list(missing_nests)


# The following functions signals are only there for debugging purposes
# (I want to see ERRORs in log file for easy checks)
# This should be removed (or at the very least limited to a INFO log level) once issues are solved
def cleanup_log_predelete(**kwargs):
    logger.error(f'Cleanup: predelete {kwargs["file"]} (not an actual error)')


def cleanup_log_postdelete(**kwargs):
    logger.error(f'Cleanup: postdelete {kwargs["file"]} (not an actual error)')


cleanup_pre_delete.connect(cleanup_log_predelete)
cleanup_post_delete.connect(cleanup_log_postdelete)
