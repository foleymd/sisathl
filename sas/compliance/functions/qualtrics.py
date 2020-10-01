import requests
import logging
from copy import deepcopy

from django.conf import settings
from django.contrib import messages


class QualtricsRequest(object):
    """Class that encapsulates call to Qualtrics API.
    https://survey.qualtrics.com/WRAPI/ControlPanel/docs.php"""

    def __init__(self):
        self.params = settings.QUALTRICS_PARAMS
        self.url_base = "https://survey.qualtrics.com/WRAPI/ControlPanel/api.php"

    def make_request(self, params, method='GET'):
        """Makes the actual HTTP request to Qualtrics."""
        if method == 'POST':
            r = requests.post(self.url_base, data=params)
        else:
            r = requests.get(self.url_base, params=params)
        print r.json()
        if r.status_code != 200:
            # TODO: some error handling
            print 'got an error!'
            return False

        return r.json()

    def create_panel(self, panel_name):
        """Creates a panel in Qualtrics with the given name
        and returns the new panel's ID."""
        params = deepcopy(self.params)
        params['Request'] = 'createPanel'
        params['Name'] = panel_name
        response = self.make_request(params)
        panel_id = response['Result']['PanelID']
        return panel_id

    def delete_panel(self, panel_id):
        """Deletes panel via Qualtrics API."""
        params = deepcopy(self.params)
        params['Request'] = 'deletePanel'
        params['PanelID'] = panel_id
        response = self.make_request(params)
        return response

    def get_panel(self, panel_id):
        """Returns users in panel via Qualtrics API."""
        params = deepcopy(self.params)
        params['Request'] = 'getPanel'
        params['PanelID'] = panel_id
        response = self.make_request(params)
        return response

    def add_recipient(self, panel_id, student_dict):
        """Expects a student dict that contains:
        FirstName, LastName, Email, ExternalDataRef ('<eid>@utexas.edu'),
        First Time ('Yes', 'No'), Over 18 ('Yes', 'No'),
        Walk-on ('Yes', 'No'), Status, Sport1, Sport2, Sport3.
        Other key/values are ignored. Returns new recipient ID."""

        params = deepcopy(self.params)
        params['Request'] = 'addRecipient'
        params['PanelID'] = panel_id
        params['FirstName'] = student_dict.get('FirstName', '')
        params['LastName'] = student_dict.get('LastName', '')
        params['Email'] = student_dict.get('Email', '')
        params['ED[LocalAddress1]'] = student_dict.get('Local Address Line 1', '')
        params['ED[LocalAddress2]'] = student_dict.get('Local Address Line 2', '')
        params['ED[LocalAddress3]'] = student_dict.get('Local Address Line 3', '')
        params['ED[PermAddress1]'] = student_dict.get('Perm Address Line 1', '')
        params['ED[PermAddress2]'] = student_dict.get('Perm Address Line 2', '')
        params['ED[PermAddress3]'] = student_dict.get('Perm Address Line 3', '')
        params['ED[Phone]'] = student_dict.get('Phone', '')
        params['ED[CellPhone]'] = student_dict.get('Cell Phone', '')
        params['ED[AltPhone]'] = student_dict.get('Alt Phone', '')
        params['ExternalDataRef'] = student_dict.get('ExternalDataRef', '')
        params['ED[FirstTime]'] = student_dict.get('First Time', '')
        params['ED[Over18]'] = student_dict.get('Over 18', '')
        params['ED[Walk-on]'] = student_dict.get('Walk-on', '')
        params['ED[Status]'] = student_dict.get('Status', '')
        params['ED[SquadPosition]'] = student_dict.get('Position', '')
        params['ED[Sport1]'] = student_dict.get('Sport1', '')
        params['ED[Sport2]'] = student_dict.get('Sport2', '')
        params['ED[Sport3]'] = student_dict.get('Sport3', '')
        response = self.make_request(params, method='POST')
        return response['Result']['RecipientID']

    def get_survey_data(self, survey_id):
        """Returns name of survey from Qualtrics API."""
        params = deepcopy(self.params)
        params['Request'] = 'getSurveyName'
        params['SurveyID'] = survey_id
        response = self.make_request(params)
        return response

    def get_survey_name(self, survey_id):
        """Gets all survey data for a given ID then returns
        the name."""
        survey_data = self.get_survey_data(survey_id)
        return survey_data['Result']['SurveyName']

    @staticmethod
    def get_survey_link(survey_id):
        """Builds URL used to take a survey."""
        survey_url_base = 'https://utexas.qualtrics.com/SE/?SID='
        survey_url = '{0}{1}'.format(survey_url_base, survey_id)
        return survey_url

    def get_recipient(self, recipient_id):
        """Returns recipient data from Qualtrics API."""
        params = deepcopy(self.params)
        params['Request'] = 'getRecipient'
        params['RecipientID'] = recipient_id
        print 'getting recipient'
        response = self.make_request(params)
        return response
