import datetime

from django.contrib import messages
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

from sisathl.sas.sp.models import User
from sisathl.sas.utils.utils import render_sp_error_page
from sisathl.sas.utils.constants import *

USER_TYPE = 'user_type'
USER_COLLEGE = 'user_college'
IS_ADMIN = 'is_admin'
USER_NAME = 'user_name'
USER_EID = "user_eid"

def authorization(view_func):

    def _wrapped_view_func(request, *args, **kwargs):
        
        _ERROR_MSG = 'You are not authorized to view this site. Please contact Athletic Student Services.'
        
        def _remove_session_data(request):
            try:
                del request.session[USER_TYPE]
            except KeyError:  # already gone for some reason
                pass
            try:
                del request.session[USER_COLLEGE]
            except KeyError:  # already gone for some reason
                pass
            try:
                del request.session[IS_ADMIN]
            except KeyError:  # already gone for some reason
                pass
        
        def _reject_user(request):
            _remove_session_data(request)
            return render_sp_error_page(request, _ERROR_MSG)
        
        def _is_authorized(request):
        
            # get user info
            uin = request.META['HTTP_UIN']
            
            # does user exist?
            try:
                user = User.objects.get(uin=uin)
            except User.DoesNotExist:
                return False
            
            # are they marked as active?
            if not user.active:
                return False
                
            return True
        
        def _add_user_info_to_session(request):
            try:
                user = User.objects.get(uin=request.META['HTTP_UIN'])
            except User.DoesNotExist:
                return _reject_user(request)
            request.session[USER_TYPE] = user.type
            try:
                user_college = user.school.code
            except AttributeError:
                user_college = False
            request.session[USER_COLLEGE] = user_college
            request.session[IS_ADMIN] = user.is_admin()
            request.session[USER_NAME] = user.name
            request.session[USER_EID] = user.eid
            request.session.set_expiry(TIMEOUT)
        
        # check if session data showing authorization exists. If not
        # check auths and make decision.
       
        if not request.session.get(USER_TYPE):
            if _is_authorized(request):
                _add_user_info_to_session(request)
            else: 
                return _reject_user(request)

        return view_func(request, *args, **kwargs)
        
    return _wrapped_view_func

