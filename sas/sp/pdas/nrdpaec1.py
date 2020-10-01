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


class Nrdpaec1(Pda):
# ************************************************************************************************
# Python class Nrdpaec1 generated using information on the fields in
# pda NRDPAEC1 in library NRATH (QUAL).
# Created by Marjorie D Foley on Mon Feb 09 16:50:49 CST 2015.
# ************************************************************************************************
    SEND_LENGTH = 50
    RECV_LENGTH = 461
    DEFAULT_SERVER_NAME = 'NR-ATH-SPD'
    DEFAULT_SUBPROGRAM = 'NRNPAEC1'

    class Send:
        subprogram_to_call = NaturalAlpha(offset=0, length=8)
        webtoken = NaturalAlpha(offset=8, length=36)
        input_data = FieldGroup(fields=["destination_data"])
        destination_data = NaturalAlpha(offset=44, length=6)
        user_logon = NaturalAlpha(offset=44, length=5)
        number_of_copies = NaturalAlpha(offset=49, length=1)
            
    class Recv:
        server_error_data = NaturalAlpha(offset=0, length=100)
        return_code = NaturalAlpha(offset=100, length=4)
        return_msg = NaturalAlpha(offset=104, length=200)
        job_info = FieldGroup(fields=["job_names", "job_numbers", "destination_data"])
        job_names = NaturalAlpha(offset=304, length=8, dims=(Dim(10, 8),))
        job_numbers = NaturalAlpha(offset=384, length=7, dims=(Dim(10, 7),))
        destination_data = NaturalAlpha(offset=454, length=6)
        user_logon = NaturalAlpha(offset=454, length=5)
        number_of_copies = NaturalAlpha(offset=459, length=1)
        last_send_field = NaturalAlpha(offset=460, length=1)