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


class Nrdpaec2(Pda):
# ************************************************************************************************
# Python class Nrdpaec2 generated using information on the fields in
# pda NRDPAEC2 in library NRATH (QUAL).
# Created by Marjorie D Foley on Thu May 28 16:32:11 CDT 2015.
# ************************************************************************************************
    SEND_LENGTH = 58
    RECV_LENGTH = 579
    DEFAULT_SERVER_NAME = 'NR-ATH-SPD'
    DEFAULT_SUBPROGRAM = 'NRNPAEC2'

    class Send:
        subprogram_to_call = NaturalAlpha(offset=0, length=8)
        webtoken = NaturalAlpha(offset=8, length=36)
        sri = NaturalNumeric(offset=44, int_digits=9, dec_digits=0)
        ccyys = NaturalNumeric(offset=53, int_digits=5, dec_digits=0)
            
    class Recv:
        server_error_data = NaturalAlpha(offset=0, length=100)
        return_code = NaturalAlpha(offset=100, length=4)
        return_msg = NaturalAlpha(offset=104, length=200)
        college_code = NaturalAlpha(offset=304, length=1)
        college_name = NaturalAlpha(offset=305, length=16)
        major_code = NaturalAlpha(offset=321, length=5)
        major_name = NaturalAlpha(offset=326, length=16)
        catalog_begin = NaturalAlpha(offset=342, length=4)
        catalog_end = NaturalAlpha(offset=346, length=4)
        college_code_2 = NaturalAlpha(offset=350, length=1)
        college_name_2 = NaturalAlpha(offset=351, length=16)
        major_code_2 = NaturalAlpha(offset=367, length=5)
        major_name_2 = NaturalAlpha(offset=372, length=16)
        catalog_begin_2 = NaturalAlpha(offset=388, length=4)
        catalog_end_2 = NaturalAlpha(offset=392, length=4)
        classes = FieldGroupArray(fields=["unique", "dept_abbr", "course_number", "hours_credit", "course_type"], dimensions=[10])
        unique = NaturalAlpha(offset=396, length=5, dims=(Dim(10, 18),))
        dept_abbr = NaturalAlpha(offset=401, length=3, dims=(Dim(10, 18),))
        course_number = NaturalAlpha(offset=404, length=6, dims=(Dim(10, 18),))
        hours_credit = NaturalNumeric(offset=410, int_digits=1, dec_digits=0, dims=(Dim(10, 18),))
        course_type = NaturalAlpha(offset=411, length=3, dims=(Dim(10, 18),))
        number_classes_returned = NaturalAlpha(offset=576, length=2)
        last_send_field = NaturalAlpha(offset=578, length=1)