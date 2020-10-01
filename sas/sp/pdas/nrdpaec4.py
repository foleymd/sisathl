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


class Nrdpaec4(Pda):
# ************************************************************************************************
# Python class Nrdpaec4 generated using information on the fields in
# pda NRDPAEC4 in library NRATH (QUAL).
# Created by Marjorie D Foley on Wed Apr 01 11:30:43 CDT 2015.
# ************************************************************************************************
    SEND_LENGTH = 44
    RECV_LENGTH = 315
    DEFAULT_SERVER_NAME = 'NR-ATH-SPD'
    DEFAULT_SUBPROGRAM = 'NRNPAEC4'

    class Send:
        subprogram_to_call = NaturalAlpha(offset=0, length=8)
        webtoken = NaturalAlpha(offset=8, length=36)
            
    class Recv:
        server_error_data = NaturalAlpha(offset=0, length=100)
        return_code = NaturalAlpha(offset=100, length=4)
        return_msg = NaturalAlpha(offset=104, length=200)
        current_ccyys = NaturalNumeric(offset=304, int_digits=5, dec_digits=0)
        current_ccyy = NaturalNumeric(offset=304, int_digits=4, dec_digits=0)
        current_s = NaturalNumeric(offset=308, int_digits=1, dec_digits=0)
        previous_ccyys = NaturalNumeric(offset=309, int_digits=5, dec_digits=0)
        previous_ccyy = NaturalNumeric(offset=309, int_digits=4, dec_digits=0)
        previous_s = NaturalNumeric(offset=313, int_digits=1, dec_digits=0)
        last_send_field = NaturalAlpha(offset=314, length=1)