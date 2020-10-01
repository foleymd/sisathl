"""
Access and query The University's TED database.

Originally authored by Gary Wilson Jr. while in the ECE Department, and since
adapted to make use of the python-simpleldap library that was factored out of
the original work.
"""

from getpass import getpass
import ldap
from ldap.filter import filter_format
from simpleldap import Connection, LDAPItem


class TEDLDAPItem(LDAPItem):
    """
    An extension of LDAPItem with methods specific to TED.
    """

    def is_active(self):
        """
        Return True if object has 'Active' inetUserStatus.
        Indicates whether the person is permitted to logon using their UT EID.
        """
        return self.first('inetUserStatus') == 'Active'

    def has_affiliation(self, value):
        """
        Return True if object has the passed value in the eduPersonAffiliation
        attribute.
        """
        return value in self['eduPersonAffiliation']

    def has_entitlement(self, code):
        """
        Return True if object has the given entitlement code.
        """
        return code in self['utexasEduPersonEntitlementCode']

    def in_depts(self, depts, attr='utexasEduPersonOrgUnitName'):
        """
        Return True if object is in any of the given departments, using the
        utexasEduPersonOrgUnitName attribute to determine membership.

        If depts is empty, then return True.

        attr is the attribute to use to determine department membership.  The
        default is 'utexasEduPersonOrgUnitName', but when looking up a student
        you'll likely want to use 'utexasEduPersonMajorDept'.
        """
        if not depts:
            return True
        for dept in depts:
            if dept in self[attr]:
                return True
        return False

    def is_faculty(self, depts=[]):
        """
        Return True if object has 'faculty' in the eduPersonAffiliation
        attribute.  Accepts an optional list of department names passed as
        depts, that will also check that the object has one of those
        department names in the utexasEduPersonOrgUnitName attribute.
        """
        return self.has_affiliation('faculty') and self.in_depts(depts)

    def is_staff(self, depts=[]):
        """
        Return True if object has 'staff' in the eduPersonAffiliation
        attribute.  Accepts an optional list of department names passed as
        depts, that will also check that the object has one of those
        department names in the utexasEduPersonOrgUnitName attribute.
        """
        return self.has_affiliation('staff') and self.in_depts(depts)

    def is_student(self, depts=[]):
        """
        Return True if object has 'student' in the eduPersonAffiliation
        attribute.  Accepts an optional list of department names passed as
        depts, that if passed will also check that the object is a major of
        one of those departments.
        """
        return self.has_affiliation('student') \
                    and self.in_depts(depts, attr='utexasEduPersonMajorDept')

    def is_member(self):
        """
        Return True if object has 'member' in the eduPersonAffiliation
        attribute.
        """
        return self.has_affiliation('member')

    def is_affiliate(self):
        """
        Return True if object has 'affiliate' in the eduPersonAffiliation
        attribute.
        """
        return self.has_affiliation('affiliate')

    def has_signature_authority(self):
        """
        Return True if object's EID has electronic signature authority
        (SIG entitlement).
        """
        return self.has_entitlement("SIG")

    def is_developer(self):
        """
        Return True if the object has the developer (DEV) entitlement.
        """
        return self.has_entitlement("DEV")


class TEDConnection(Connection):
    """
    A connection to TED, the uTexas Enterprise Directory.
    """

    # Default attributes to return for searches.
    attributes = [
        'cn',
        'givenName',
        'sn',
        'inetUserStatus',
        'utexasEduPersonEid',
        'utexasEduPersonUin',
        'utexasEduPersonIsoNumber',
        'utexasEduPersonOrgUnitName',
        'utexasEduPersonPubAffiliation',
        'eduPersonAffiliation',
        'utexasEduPersonPrimaryTitle',
        'utexasEduPersonHighestDegree',
        'utexasEduPersonCourseNumber',
        'utexasEduPersonOrgUnitName',
        'utexasEduPersonMajorDept',
        'mail',
        'utexasEduPersonEntitlementCode',
    ]

    result_item_class = TEDLDAPItem

    def __init__(self, dn=None, eid=None, password='', service=True,
                 hostname="entdir.utexas.edu", **kwargs):
        """
        A connection to the TED server.

        Typically, ``eid`` and ``password`` are given, and represent the user
        to bind as.  By default, ``eid`` is considered to be a Service EID.
        To use a person EID, set ``service`` to ``False``.  Alternatively, you
        may pass a fully-qualified distinguished name as ``dn``, which,
        if given, will be the exact dn string used to bind.  If you pass no
        dn or password, both default to empty string (anonymous bind).

        If host is not given, it defaults to 'entdir.utexas.edu'.
        If encryption is not given, it defaults to 'ssl'.
        """
        dn = self._get_dn(dn, eid, service)
        if 'encryption' not in kwargs:
            kwargs['encryption'] = 'ssl'
        super(TEDConnection, self).__init__(hostname, dn=dn, password=password,
                                            **kwargs)

    def _get_dn(self, dn=None, eid=None, service=None):
        """
        Helper function to return a dn based the passed values.  If neither dn
        nor eid is given, then return '' (anonymous).
        """
        if dn:
            return dn
        if eid:
            if service:
                return "uid=%s,ou=services,dc=entdir,dc=utexas,dc=edu" % eid
            else:
                return "uid=%s,ou=people,dc=entdir,dc=utexas,dc=edu" % eid
        # Anonymous.
        return ''

    def _get_by_attr(self, attr, value, **kwargs):
        filter_str = filter_format("(%s=%s)", [attr, value])
        return self.get(filter_str, **kwargs)

    def get_by_eid(self, eid, *args, **kwargs):
        return self._get_by_attr("utexasEduPersonEid", eid, *args, **kwargs)

    def get_by_uin(self, uin, *args, **kwargs):
        return self._get_by_attr("utexasEduPersonUin", uin, *args, **kwargs)

    def get_by_iso(self, iso, *args, **kwargs):
        return self._get_by_attr("utexasEduPersonIsoNumber", iso,
                                 *args, **kwargs)

    def search(self, filter, **kwargs):
        if 'attrs' not in kwargs:
            kwargs['attrs'] = self.attributes
        return super(TEDConnection, self).search(filter, **kwargs)

    def _search_by_attr(self, attr, value, **kwargs):
        filter_str = filter_format("(%s=%s)", [attr, value])
        return self.search(filter_str, **kwargs)

    def search_by_eid(self, eid, *args, **kwargs):
        return self._search_by_attr("utexasEduPersonEid", eid, *args, **kwargs)

    def search_by_uin(self, uin, *args, **kwargs):
        return self._search_by_attr("utexasEduPersonUin", uin, *args, **kwargs)

    def search_by_iso(self, iso, *args, **kwargs):
        return self._search_by_attr("utexasEduPersonIsoNumber", iso,
                                    *args, **kwargs)

    def search_by_name(self, fullname, *args, **kwargs):
        """
        Search for fullname in TED cn field.

        ``fullname`` is handled like so:

        * If only a single name is given, e.g. "last", the query finds objects
          with an exact match of the cn or objects with a matching last name
          (cn " last").
        * If two names are given, e.g. "first last", the query finds objects
          with a matching first name (cn beginning with "first ") and last
          name.
        * If three or more names are given, e.g. "first middle1 middle2 last",
          the query finds objects with a matching first and last name that also
          contain the middle names (cn containing " middle1 middle2 ").

        Note, querying for common names will likely result in the server
        returning a size limit exceeded error; thus, when at all possible, you
        should really only be querying by EID, UIN, or ISO.
        """
        names = fullname.split()
        if len(names) < 1:
            filter_str = '(cn=)'
        elif len(names) == 1:
            filter_str = filter_format("(|(cn=%s)(cn=* %s))", [names[0]] * 2)
        elif len(names) == 2:
            filter_str = filter_format("(&(cn=%s *)(cn=* %s))", names)
        else:
            middle_names = " ".join(names[1:-1])
            filter_str = filter_format("(&(cn=%s *)(cn=* %s *)(cn=* %s))",
                                       [names[0], middle_names, names[-1]])
        return self.search(filter_str, *args, **kwargs)


class InteractiveTEDConnection(TEDConnection):
    """Prompts for EID and password."""

    def __init__(self, **kwargs):
        if 'eid' not in kwargs:
            kwargs['eid'] = raw_input('Enter EID: ')
        if 'password' not in kwargs:
            kwargs['password'] = getpass("%s's password: " % kwargs['eid'])
        super(InteractiveTEDConnection, self).__init__(**kwargs)
