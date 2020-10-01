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


class Nrdpaec6(Pda):
# ************************************************************************************************
# Python class Nrdpaec6 generated using information on the fields in
# pda NRDPAEC6 in library NRATH (TEST).
# Created by Marjorie D Foley on Tue Sep 08 16:45:15 CDT 2015.
# ************************************************************************************************
    SEND_LENGTH = 57
    RECV_LENGTH = 411
    DEFAULT_SERVER_NAME = 'NR-ATH-SPD'
    DEFAULT_SUBPROGRAM = 'NRNPAEC6'

    class Send:
        subprogram_to_call = NaturalAlpha(offset=0, length=8)
        webtoken = NaturalAlpha(offset=8, length=36)
        eid = NaturalAlpha(offset=44, length=8)
        ccyys = NaturalNumeric(offset=52, int_digits=5, dec_digits=0)
            
    class Recv:
        server_error_data = NaturalAlpha(offset=0, length=100)
        return_code = NaturalAlpha(offset=100, length=4)
        return_msg = NaturalAlpha(offset=104, length=200)
        uin = NaturalAlpha(offset=304, length=16)
        eid = NaturalAlpha(offset=320, length=16)
        ncaa_id = NaturalAlpha(offset=336, length=10)
        sri = NaturalNumeric(offset=346, int_digits=9, dec_digits=0)
        name = NaturalAlpha(offset=355, length=25)
        ccyys = NaturalNumeric(offset=380, int_digits=5, dec_digits=0)
        num_ft_semesters = NaturalNumeric(offset=385, int_digits=2, dec_digits=0)
        sport_1 = NaturalAlpha(offset=387, length=3)
        sport_2 = NaturalAlpha(offset=390, length=3)
        sport_3 = NaturalAlpha(offset=393, length=3)
        college_code = NaturalAlpha(offset=396, length=1)
        major_code = NaturalAlpha(offset=397, length=5)
        catalog_begin = NaturalAlpha(offset=402, length=4)
        catalog_end = NaturalAlpha(offset=406, length=4)
        last_send_field = NaturalAlpha(offset=410, length=1)
