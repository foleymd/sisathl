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


class Nrdpaec7(Pda):
# ************************************************************************************************
# Python class Nrdpaec7 generated using information on the fields in
# pda NRDPAEC7 in library NRATH (TEST).
# Created by Sara Denise Gore on Fri Mar 04 12:40:35 CST 2016.
# ************************************************************************************************
    SEND_LENGTH = 59
    RECV_LENGTH = 370
    DEFAULT_SERVER_NAME = 'NR-ATH-SPD'
    DEFAULT_SUBPROGRAM = 'NRNPAEC7'

    class Send:
        subprogram_to_call = NaturalAlpha(offset=0, length=8)
        webtoken = NaturalAlpha(offset=8, length=36)
        fall_ccyys = NaturalAlpha(offset=44, length=5)
        year_pk = NaturalAlpha(offset=49, length=10)

    class Recv:
        server_error_data = NaturalAlpha(offset=0, length=100)
        return_code = NaturalAlpha(offset=100, length=4)
        return_msg = NaturalAlpha(offset=104, length=200)
        fall_ccyys = NaturalAlpha(offset=304, length=5)
        year_pk = NaturalAlpha(offset=309, length=10)
        job_nbr = NaturalAlpha(offset=319, length=5, dims=(Dim(10, 5),))
        last_send_field = NaturalAlpha(offset=369, length=1)