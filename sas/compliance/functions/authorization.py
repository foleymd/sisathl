from utbroker.errors import UTBrokerError

from sisathl.sas.utils.constants import TIMEOUT

from sisathl.sas.compliance.functions.compliance_functions import render_error_page

from utbroker.pda import Pda
from utbroker.fields import Dim, NaturalAlpha, NaturalNumeric, NaturalLogical
try:
    from utbroker.fields import FieldGroup, FieldGroupArray
except ImportError:
    # Backwards compatibility for utbroker library versions <1.0 that don't
    # define group fields.
    class Fake:
        def __init__(self, *args, **kwargs): pass
    FieldGroup = FieldGroupArray = Fake


COMPLIANCE_LVL = 'compliance_lvl'
COMPLIANCE_STUDENT = 'SATHL'
COMPLIANCE_ADMIN = 'ADMIN'


class Nrdpaec8(Pda):
    # ************************************************************************************************
    # Python class Nrdpaec8 generated using information on the fields in
    # pda NRDPAEC8 in library NRATH (TEST).
    # Created by Sara Denise Gore on Tue May 24 15:11:09 CDT 2016.
    # ************************************************************************************************
    SEND_LENGTH = 44
    RECV_LENGTH = 345
    DEFAULT_SERVER_NAME = 'NR-ATH-SPD'
    DEFAULT_SUBPROGRAM = 'NRNPAEC8'

    class Send:
        subprogram_to_call = NaturalAlpha(offset=0, length=8)
        webtoken = NaturalAlpha(offset=8, length=36)

    class Recv:
        server_error_data = NaturalAlpha(offset=0, length=100)
        return_code = NaturalAlpha(offset=100, length=4)
        return_msg = NaturalAlpha(offset=104, length=200)
        security_lvl = NaturalAlpha(offset=304, length=8)
        md5_hash = NaturalAlpha(offset=312, length=32)
        last_send_field = NaturalAlpha(offset=344, length=1)


def authorization(view_func):
    def _wrapped_view_func(request, *args, **kwargs):

        _ERROR_MSG = 'You are not authorized to view this site.'

        def _remove_session_data(request):
            try:
                del request.session[COMPLIANCE_LVL]
            except KeyError:  # already gone for some reason
                pass

        def _reject_user(request):
            _remove_session_data(request)
            return render_error_page(request, _ERROR_MSG)

        def _is_authorized(request):
            """Make a broker call to check auths."""
            nrdpaec8 = Nrdpaec8()
            nrdpaec8.send.webtoken = request.META['HTTP_TOKEN']
            try:
                nrdpaec8.call_broker_once(service=request.META['HTTP_SERVICE'])
            except (AttributeError, UTBrokerError):
                return None
            print nrdpaec8.recv.return_msg
            print nrdpaec8.recv.security_lvl
            request.session[COMPLIANCE_LVL] = nrdpaec8.recv.security_lvl
            request.session.set_expiry(TIMEOUT)

            return True

        # check if session data showing authorization exists. If not
        # check auths and make decision.
        if not request.session.get(COMPLIANCE_LVL):
            if not _is_authorized(request):
                return _reject_user(request)

        return view_func(request, *args, **kwargs)

    return _wrapped_view_func
