import datetime
import logging

from django.db import models

from sisathl.sas.utils.utils import get_academic_year_range


class Year(models.Model):
    """Main table representing one year of the compliance forms."""
    fall_ccyys = models.IntegerField()
    panel_id = models.CharField(max_length=50, null=True, blank=True)
    panel_name = models.CharField(max_length=75, null=True, blank=True)

    @property
    def academic_year_display(self):
        """Returns the academic year it represents formatted for display."""

        return unicode(get_academic_year_range(self.fall_ccyys))

    def __unicode__(self):
        return unicode(self.academic_year_display)


class Survey(models.Model):
    """Stores the surrvey IDs asscoiated with a year."""
    year = models.ForeignKey('Year')
    survey_id = models.CharField(max_length=50)

    class Meta:
        unique_together = ['year', 'survey_id']

    def __unicode__(self):
        return unicode("Survey ID {0}".format(self.survey_id))
