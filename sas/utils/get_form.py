from django.core.exceptions import ObjectDoesNotExist

from sisathl.sas.sp.models import (AthleteCcyysAdmin,
                                         PercentDegree,
                                         AthleteCcyys,
                                         )


def get_form(form_type_name, form_id):
    """Given a form type and id, return the form object that it
    corresponds to."""
    
    if form_type_name == AthleteCcyysAdmin.SPD:
        try:
            form = AthleteCcyysAdmin.objects.get(id=form_id)
        except AthleteCcyysAdmin.DoesNotExist:
            raise ObjectDoesNotExist
    elif form_type_name == PercentDegree.PERCENT:
        try:
            form = PercentDegree.objects.get(id=form_id)
        except PercentDegree.DoesNotExist:
            raise ObjectDoesNotExist
    else: 
        raise ObjectDoesNotExist
    return form


def get_form_ccyys(form_type_name, form_id):
    """Given a form type and id, returns the ccyys associated
        with the form."""

    if form_type_name == AthleteCcyysAdmin.SPD:
        try:
            form = AthleteCcyysAdmin.objects.get(id=form_id)
            ccyys = form.athlete_ccyys.ccyys
        except AthleteCcyysAdmin.DoesNotExist:
            raise ObjectDoesNotExist
    elif form_type_name == PercentDegree.PERCENT:
        try:
            form = PercentDegree.objects.get(id=form_id)
            athlete_ccyys = AthleteCcyys.objects.get(
                pk=form.major.athlete_ccyys_admin.athlete_ccyys.id)
            ccyys = athlete_ccyys.ccyys
        except PercentDegree.DoesNotExist:
            raise ObjectDoesNotExist
    else:
        raise ObjectDoesNotExist
    return ccyys