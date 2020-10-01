from django.test import TestCase

from sisathl.sas.compliance.functions.qualtrics import QualtricsRequest


class QualtricsTests(TestCase):

    def setUp(self):
        panel_name = 'testing_panel'
        self.q = QualtricsRequest()
        self.panel_id = self.q.create_panel(panel_name)

        self.all_test_student = {'FirstName': 'FooFoo',
                                'LastName': 'Cocopops',
                                'Email': 'beep@boop.com',
                                'ExternalDataRef': 'speede@utexas.edu',
                                'First Time': 'No',
                                'Over 18': 'Yes',
                                'Walk-on': 'No',
                                'Status': 'Continuing',
                                'Sport1': 'MFB',
                                'Sport2': '',
                                'Sport3': ''}
        self.all_test_student_id = self.q.add_recipient(self.panel_id, self.all_test_student)

    def tearDown(self):
        self.q.delete_panel(self.panel_id)

    def test_create_and_delete_panel(self):
        panel_name = 'xxx'
        q = QualtricsRequest()
        panel_id = q.create_panel(panel_name)
        self.assertTrue(panel_id)

        try:
            panel = q.get_panel(panel_id)
            self.assertTrue(True)  # it worked!
        except:
            self.assertTrue(False)

        q.delete_panel(panel_id)

        try:
            panel = q.get_panel(panel_id)
            self.assertTrue(False)
        except:
            self.assertTrue(True)

    def test_adding_recipients(self):
        test_student = {'FirstName': 'MOBOLAJI',
                    'LastName': 'ADEOKUN',
                    'Email': 'fake@fak.com',
                    'ExternalDataRef': 'speede@utexas.edu',
                    'First Time': 'No',
                    'Over 18': 'Yes',
                    'Walk-on': 'No',
                    'Status': 'Continuing',
                    'Sport1': 'WTI',
                    'Sport2': 'WTO',
                    'Sport3': ''}

        self.q.add_recipient(self.panel_id, test_student)
        panel = self.q.get_panel(self.panel_id)
        # make a list of just the eids (well, the ExternalDataReference) so that we
        # have a concise list of who is already in the panel
        panel_eids = [student['ExternalDataReference'] for student in panel if student.get('ExternalDataReference', False)]
        self.assertTrue(test_student['ExternalDataRef'] in panel_eids)

    def test_getting_recipient(self):
        try:
            recipient = self.q.get_recipient(self.all_test_student_id)
            print recipient
            self.assertTrue(True)  # it worked!
        except:
            self.assertTrue(False)


    #TODO: write test for getting survey name

