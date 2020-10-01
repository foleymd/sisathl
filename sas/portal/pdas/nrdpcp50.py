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


class Nrdpcp50(Pda):
# ************************************************************************************************
# Python class Nrdpcp50 generated using information on the fields in
# pda NRDPCP50 in library NRATH (TEST).
# Created by Brian E Ruh on Fri May 11 16:49:22 CDT 2012.
# ************************************************************************************************
    SEND_LENGTH = 67
    RECV_LENGTH = 665
    DEFAULT_SERVER_NAME = 'NR-ATH-COMP'
    DEFAULT_SUBPROGRAM = 'NRNPCP50'

    class Send:
        subprogram_to_call = NaturalAlpha(offset=0, length=8)
        webtoken = NaturalAlpha(offset=8, length=36)
        input_eid = NaturalAlpha(offset=44, length=8)
        ip_address = NaturalAlpha(offset=52, length=15)
			
    class Recv:
        server_error_data = NaturalAlpha(offset=0, length=100)
        return_code = NaturalAlpha(offset=100, length=4)
        return_msg = NaturalAlpha(offset=104, length=200)
        security_level = NaturalAlpha(offset=304, length=5)
        ut_eid = NaturalAlpha(offset=309, length=8)
        ncaa_id = NaturalAlpha(offset=317, length=10)
        acs_hash = NaturalAlpha(offset=327, length=32)
        med_hash = NaturalAlpha(offset=359, length=40)
        timestamp = NaturalAlpha(offset=399, length=14)
        debug_string = NaturalAlpha(offset=413, length=250)
        debug_sw = NaturalAlpha(offset=663, length=1)
        last_send_field = NaturalAlpha(offset=664, length=1)
