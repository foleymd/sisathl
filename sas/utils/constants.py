import datetime

# This is the year the system was built. It's not possible to have forms older
# than 2015, so this should be used as the oldest possible year in drop downs
# and such.
SYSTEM_START_YEAR = 2015

# This provides a list of years to use in search drop downs. It starts from the
# beginning of the system to 5 years from today.
YEARS = [year for year in xrange(SYSTEM_START_YEAR - 5, datetime.date.today().year + 5)]
YEAR_CHOICES = [(str(year), str(year)) for year in xrange(SYSTEM_START_YEAR - 5,
                                         datetime.date.today().year + 5)]

CATALOG_YEARS = (('', '--'),
                 ('2000', '2000'),
                 ('2001', '2001'),
                 ('2002', '2002'),
                 ('2003', '2003'),
                 ('2004', '2004'),
                 ('2005', '2005'),
                 ('2006', '2006'),
                 ('2007', '2007'),
                 ('2008', '2008'),
                 ('2009', '2009'),
                 ('2010', '2010'),
                 ('2011', '2011'),
                 ('2012', '2012'),
                 ('2013', '2013'),
                 ('2014', '2014'),
                 ('2015', '2015'),
                 ('2016', '2016'),
                 ('2017', '2017'),
                 ('2018', '2018'),
                 ('2019', '2019'),
                 ('2020', '2020'),
                 ('2021', '2021'),
                 ('2022', '2022'),
                 ('2023', '2023'),
                 ('2024', '2024'),
                 ('2025', '2025'),
                 ('2026', '2026'),
                 ('2027', '2027'),
                 ('2028', '2028'),
                 ('2029', '2029'),
                 ('2030', '2030'),
                )

    
AUTH_ERROR_MSG = 'An error has occurred. If you believe you should ' \
                'have access to this page, please contact Athletic Student Services.'
                
CURRENT_CCYYS = 'current_ccyys'
CURRENT_YEAR = 'current_ccyy'
CURRENT_SEMESTER = 'current_s'
TIMEOUT = 1800  # seconds
DEFAULT_PAGINATION_AMT = 50
SPRING = '2'
FALL = '9'
SUMMER = '6'
VALID_SEMESTERS = [SPRING, SUMMER, FALL]
SEMESTER_CHOICES = ((SPRING, 'Spring'),
                    (SUMMER, 'Summer'),
                    (FALL, 'Fall'))

# possible reasons a comment might be required
RETURNING_FORM = 'RF'
ADVANCING_FORM = 'AF'
SAVING_PERCENT = 'SP'
FORM_ACTIONS = [RETURNING_FORM, ADVANCING_FORM, SAVING_PERCENT]
