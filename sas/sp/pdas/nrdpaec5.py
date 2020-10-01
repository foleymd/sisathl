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


class Nrdpaec5(Pda):
# ************************************************************************************************
# Python class Nrdpaec5 generated using information on the fields in
# pda NRDPAEC5 in library NRATH (TEST).
# Created by Marjorie D Foley on Fri Apr 24 17:47:54 CDT 2015.
# ************************************************************************************************
    SEND_LENGTH = 49
    RECV_LENGTH = 313
    DEFAULT_SERVER_NAME = 'NR-ATH-SPD'
    DEFAULT_SUBPROGRAM = 'NRNPAEC5'

    class Send:
        subprogram_to_call = NaturalAlpha(offset=0, length=8)
        webtoken = NaturalAlpha(offset=8, length=36)
        ccyys = NaturalAlpha(offset=44, length=5)
            
    class Recv:
        server_error_data = NaturalAlpha(offset=0, length=100)
        return_code = NaturalAlpha(offset=100, length=4)
        return_msg = NaturalAlpha(offset=104, length=200)
        last_day = NaturalNumeric(offset=304, int_digits=8, dec_digits=0)
        last_send_field = NaturalAlpha(offset=312, length=1)
