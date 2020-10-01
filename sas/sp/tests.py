from datetime import (date, timedelta)
from django.test import TestCase

from sisathl.sas.sp.functions.sp_functions import *
from sisathl.sas.sp.models import *
from sisathl.sas.utils.utils import *


class CcyysAdminTests(TestCase):
    
    def test_saving_and_retrieving_ccyys(self):
     
        first_ccyys = CcyysAdmin(ccyys=20149)
        first_ccyys.save()

        second_ccyys = CcyysAdmin(ccyys=20152)
        second_ccyys.save()

        saved_ccyyss = CcyysAdmin.objects.all()
        self.assertEqual(saved_ccyyss.count(), 2)

        first_saved_ccyys = saved_ccyyss[0]
        second_saved_ccyys = saved_ccyyss[1]
        self.assertEqual(first_saved_ccyys.ccyys, 20149)
        self.assertEqual(second_saved_ccyys.ccyys, 20152)
        
    def test_is_open(self):
        
        ccyys = CcyysAdmin(ccyys=20139)
        ccyys.athletics_open_date = date(1888, 8, 24)
        ccyys.athletics_close_date = date.today() + timedelta(3,0)  # plus 3 days
        ccyys.dean_open_date = date.today()
        ccyys.dean_close_date = date.today() + timedelta(3,0)  # plus 3 days
        ccyys.reg_open_date = date(1888, 8, 24)
        ccyys.reg_close_date = date(1888, 8, 25)
        ccyys.save()
        
        self.assertTrue(ccyys.is_open(User.ATHLETICS))
        self.assertTrue(ccyys.is_open(User.DEAN))
        self.assertFalse(ccyys.is_open(User.REGISTRAR))

    def test_display_ccyys(self):
        ccyys = CcyysAdmin(ccyys=20199)
        ccyys.athletics_open_date = date(1888, 8, 24)
        ccyys.athletics_close_date = date.today() + timedelta(3,0)  # plus 3 days
        ccyys.dean_open_date = date.today()
        ccyys.dean_close_date = date.today() + timedelta(3,0)  # plus 3 days
        ccyys.reg_open_date = date(1888, 8, 24)
        ccyys.reg_close_date = date(1888, 8, 25)
        ccyys.save()

        self.assertEqual(ccyys.display_ccyys, 'Fall 2019')


class AthleteTests(TestCase):
    
    def test_saving_and_retrieving_athlete(self):
        first_athlete = Athlete(uin='1234567890123456', 
                                ncaa_id='1234567890',
                                sri=123456789,
                                eid='drdre',
                                name='Dr Dre')
        first_athlete.save()

        second_athlete = Athlete(uin='9999999999999999',
                                 ncaa_id='9999999999',
                                 sri='999999999',
                                 eid="tupac",
                                 name="Tupac Shakur")
        second_athlete.save()

        saved_athletes = Athlete.objects.all()
        self.assertEqual(saved_athletes.count(), 2)

        first_saved_athlete = saved_athletes[0]
        second_saved_athlete = saved_athletes[1]
        self.assertEqual(first_saved_athlete.eid, 'drdre')
        self.assertEqual(second_saved_athlete.eid, 'tupac')

    def test_for_correct_info(self):
        speede = Athlete(eid='speede',
                         sri='99999999')
        speede.save()
        self.assertEqual(speede.uin, '39F199F6FC17F27F')
        self.assertEqual(speede.name, "SPEED'E, TESTER RECORD JR")
        

class AthleteCcyysTests(TestCase):
    
    fixtures = ['entire_db.json']

    def test_storing_and_retrieving_athleteccyys(self):
        athlete_1 = Athlete.objects.get(eid="taa688")
        athlete_2 = Athlete.objects.get(eid="bia99")
        
        first_ccyys = AthleteCcyys(athlete=athlete_1, 
                                   ccyys=20139,
                                   num_ft_semesters=5)
        first_ccyys.save()
        
        second_ccyys = AthleteCcyys(athlete=athlete_2,
                                    ccyys=20142,
                                    num_ft_semesters=6)
        second_ccyys.save()
        first_saved_ccyys = AthleteCcyys.objects.get(athlete=athlete_1, ccyys=20139)
        second_saved_ccyys = AthleteCcyys.objects.get(athlete=athlete_2, ccyys=20142)
        self.assertEqual(first_saved_ccyys.num_ft_semesters, 5)
        self.assertEqual(second_saved_ccyys.num_ft_semesters, 6)
        
    def test_squads(self):
        athlete_1 = AthleteCcyys.objects.get(athlete__eid="taa688", ccyys=20159)
        athlete_2 = AthleteCcyys.objects.get(athlete__eid="bia99", ccyys=20159)
        
        self.assertEqual(athlete_1.squads[0][0], "WGO")
        self.assertEqual(athlete_2.squads[0][0], "WTE")
        self.assertEqual(athlete_1.squads[0][1], "Women's Golf")
        self.assertEqual(athlete_2.squads[0][1], "Women's Tennis")
        
    def test_display_ccyys(self):
        athlete_1 = AthleteCcyys.objects.get(athlete__eid="bia99", ccyys=20159)
        self.assertEqual(athlete_1.display_ccyys, 'Fall 2015')


class AthleteCcyysSportTests(TestCase):

    fixtures = ['entire_db.json']

    def setUp(self):
        athlete_1 = Athlete.objects.get(eid="taa688")
        athlete_2 = Athlete.objects.get(eid="bka359")
        athlete_ccyys_1 = AthleteCcyys.objects.create(ccyys=20139, athlete=athlete_1, num_ft_semesters=5)
        athlete_ccyys_2 = AthleteCcyys.objects.create(ccyys=20139, athlete=athlete_2, num_ft_semesters=5)

    def test_saving_and_retrieving_sports(self):
        athlete_ccyys_1 = AthleteCcyys.objects.get(ccyys=20139, athlete__eid="taa688")
        athlete_ccyys_2 = AthleteCcyys.objects.get(ccyys=20139, athlete__eid="bka359")

        first_sport = AthleteCcyysSport(athlete_ccyys=athlete_ccyys_1,
                                        sport="WU2")
        first_sport.save()

        first_sport = AthleteCcyysSport(athlete_ccyys=athlete_ccyys_2,
                                        sport="123",
                                        sport_description="Boop?")
        first_sport.save()

        first_saved_sport = AthleteCcyysSport.objects.get(athlete_ccyys=athlete_ccyys_1)
        second_saved_sport = AthleteCcyysSport.objects.get(athlete_ccyys=athlete_ccyys_2)

        self.assertEqual(first_saved_sport.sport, 'WU2')
        self.assertEqual(second_saved_sport.sport, '123')
        self.assertEqual(first_saved_sport.sport_description, "Women's Diving")
        self.assertEqual(second_saved_sport.sport_description, 'Boop?')


class AthleteCcyysAdminTests(TestCase):

    fixtures = ['entire_db.json']
    
    def setUp(self):

        # get an athlete_ccyys to link form to
        athlete_ccyys_1 = AthleteCcyys.objects.get(ccyys=20159, athlete__eid="taa688")
        athlete_ccyys_2 = AthleteCcyys.objects.get(ccyys=20159, athlete__eid="bka359")
            
        first_form = AthleteCcyysAdmin(athlete_ccyys=athlete_ccyys_1,
                                       created_by="sg27674",
                                       routed_to_dean_by=None,
                                       approved_by_dean=None,
                                       routed_to_reg_by=None,
                                       approved_by_reg=None,
                                       total_countable_degree_hours=0)
        first_form.save()

        second_form = AthleteCcyysAdmin(athlete_ccyys=athlete_ccyys_2,
                                        created_by="swevans",
                                        routed_to_dean_by="sg27674",
                                        approved_by_dean=None,
                                        routed_to_reg_by=None,
                                        approved_by_reg=None,
                                        total_countable_degree_hours=0
                                        )
        second_form.save()

    def test_saving_and_retrieving_forms(self):
        athlete_ccyys_1 = AthleteCcyys.objects.get(ccyys=20159, athlete__eid="taa688")
        athlete_ccyys_2 = AthleteCcyys.objects.get(ccyys=20159, athlete__eid="bka359")
        
        saved_form_1 = AthleteCcyysAdmin.objects.filter(athlete_ccyys=athlete_ccyys_1)
        
        form_found = False
        for form in saved_form_1:
            if form.created_by == 'sg27674':
                form_found = True
                self.assertTrue(form.active)
        self.assertTrue(form_found)
                
        saved_form_2 = AthleteCcyysAdmin.objects.filter(athlete_ccyys=athlete_ccyys_2)

        form_found = False
        for form in saved_form_2:
            if form.created_by == 'swevans' and form.routed_to_dean_by == 'sg27674':
                form_found = True
                self.assertTrue(form.active)
        self.assertTrue(form_found)

    def test_form_status(self):
        athlete_ccyys_1 = AthleteCcyys.objects.get(ccyys=20159, athlete__eid="taa688")
        athlete_ccyys_2 = AthleteCcyys.objects.get(ccyys=20159, athlete__eid="bka359")
        
        query_1 = AthleteCcyysAdmin.objects.filter(athlete_ccyys=athlete_ccyys_1, created_by='sg27674')
        saved_form_1 = query_1[0]
        query_2 = AthleteCcyysAdmin.objects.filter(athlete_ccyys=athlete_ccyys_2, created_by='swevans')
        saved_form_2 = query_2[0]
        
        self.assertEqual(saved_form_1.status, AthleteCcyysAdmin.CREATED)
        self.assertEqual(saved_form_2.status, AthleteCcyysAdmin.ROUTED_TO_DEAN)
        
        saved_form_1.routed_to_dean_by = 'speede'
        saved_form_1.save()
        self.assertEqual(saved_form_1.status, AthleteCcyysAdmin.ROUTED_TO_DEAN)
        
        saved_form_2.approved_by_dean = 'speede'
        saved_form_2.save()
        self.assertEqual(saved_form_2.status, AthleteCcyysAdmin.APPROVED_BY_DEAN)

    def test_users_turn(self):
        athlete_ccyys_1 = AthleteCcyys.objects.get(ccyys=20159, athlete__eid="taa688")
        athlete_ccyys_2 = AthleteCcyys.objects.get(ccyys=20159, athlete__eid="bka359")
        saved_form_1 = AthleteCcyysAdmin.objects.filter(athlete_ccyys=athlete_ccyys_1)[0]
        saved_form_2 = AthleteCcyysAdmin.objects.filter(athlete_ccyys=athlete_ccyys_2)[0]
        saved_form_1.approved_by_reg = None
        saved_form_1.routed_to_reg_by = None
        saved_form_1.created_by = 'sg27674'
        saved_form_1.save()
        saved_form_2.routed_to_dean_by = 'sg27674'
        saved_form_2.created_by = 'sg27674'
        saved_form_2.save()

        user = User.objects.get(eid="sg27674")
        user.type = User.ATHLETICS
        user.school = None
        user.save()
        self.assertTrue(saved_form_1.users_turn(user))
        self.assertFalse(saved_form_2.users_turn(user))
        user.type = User.DEAN
        user.school = School.objects.get(code="2")
        user.save()
        saved_form_1.routed_to_dean_by = 'sg27674'
        saved_form_1.created_by = 'sg27674'
        saved_form_1.save()
        saved_form_2.routed_to_dean_by = 'sg27674'
        saved_form_2.save()
        self.assertFalse(saved_form_1.users_turn(user))
        self.assertTrue(saved_form_2.users_turn(user))

        saved_form_2.active = False
        self.assertFalse(saved_form_2.users_turn(user))

    def test_signature_info(self):
        athlete_ccyys_1 = AthleteCcyys.objects.get(ccyys=20159, athlete__eid="taa688")
        athlete_ccyys_2 = AthleteCcyys.objects.get(ccyys=20159, athlete__eid="bka359")
        saved_form_1 = AthleteCcyysAdmin.objects.filter(athlete_ccyys=athlete_ccyys_1)[0]
        saved_form_2 = AthleteCcyysAdmin.objects.filter(athlete_ccyys=athlete_ccyys_2)[0]
        saved_form_1.routed_to_dean_by = None
        saved_form_1.created_by = 'sg27674'
        saved_form_1.save()
        saved_form_2.routed_to_dean_by = 'sg27674'
        saved_form_2.created_by = 'mdf594'
        saved_form_2.save()
        saved_form_1_sigs = saved_form_1.signature_info
        saved_form_2_sigs = saved_form_2.signature_info

        self.assertTrue('created_by' in saved_form_1_sigs)
        self.assertTrue('approved_by_reg' in saved_form_2_sigs)
        self.assertEqual(saved_form_1_sigs['created_by'], 'Sara D Gore')
        self.assertEqual(saved_form_2_sigs['created_by'], 'Marjorie D Foley')

    def test_advance_routing(self):
        athlete_ccyys1 = AthleteCcyys.objects.get(ccyys=20159, athlete__eid="jf28849")
        athlete_ccyys2 = AthleteCcyys.objects.get(ccyys=20159, athlete__eid="maa5764")
        form_1 = AthleteCcyysAdmin(athlete_ccyys=athlete_ccyys1)
        form_1.total_countable_degree_hours = 0
        form_2 = AthleteCcyysAdmin(athlete_ccyys=athlete_ccyys2)
        form_2.total_countable_degree_hours = 0
        form_1.routed_to_dean_by = "sg27674"
        form_1.save()
        form_2.routed_to_dean_by = 'sg27674'
        form_2.approved_by_dean = 'mdf594'
        form_2.save()

        # test advance_recipient
        self.assertEqual(form_1.advance_recipient, 'Athletic Student Services')
        self.assertEqual(form_2.advance_recipient, 'Registrar Staff')

        # test that the comments are uneditable before routing and editable after
        form_type = ContentType.objects.get_for_model(form_1)
        user = User.objects.get(eid='sg27674')
        comments = Comments.objects.create(form_type=form_type,
                                           form_id=form_1.id,
                                           comments="Blah",
                                           user=user)
        self.assertTrue(comments.editable)

        # test advance_routing
        form_1.advance_routing(user)
        user_2 = User.objects.get(eid='mdf594')
        form_2.advance_routing(user_2)
        self.assertEqual(form_1.approved_by_dean, user.eid)
        self.assertEqual(form_2.routed_to_reg_by, user_2.eid)
        comments = Comments.objects.filter(form_type=form_type,
                                           form_id=form_1.id,)[0]
        self.assertFalse(comments.editable)

    def test_return_form(self):
        athlete_ccyys1 = AthleteCcyys.objects.get(ccyys=20159, athlete__eid="saa2962")
        athlete_ccyys2 = AthleteCcyys.objects.get(ccyys=20159, athlete__eid="cnc965")
        form_1 = AthleteCcyysAdmin.objects.get(athlete_ccyys=athlete_ccyys1)
        form_2 = AthleteCcyysAdmin.objects.get(athlete_ccyys=athlete_ccyys2)
        form_1.total_countable_degree_hours = 0
        form_2.total_countable_degree_hours = 0
        form_1.created_by = "mdf594"
        form_1.routed_to_dean_by = "sg27674"
        form_1.save()
        form_2.created_by = "mdf594"
        form_2.routed_to_dean_by = "sg27674"
        form_2.approved_by_dean = 'mdf594'
        form_2.save()

        # test return_recipient
        self.assertEqual(form_1.return_recipient, 'Athletic Student Services')
        self.assertEqual(form_2.return_recipient, 'College')

        # test that the comments are uneditable before routing and editable after
        form_type = ContentType.objects.get_for_model(form_1)
        user = User.objects.get(eid='sg27674')
        comments = Comments.objects.create(form_type=form_type,
                                           form_id=form_1.id,
                                           comments="Blah",
                                           user=user)
        self.assertTrue(comments.editable)

        # test return_form
        form_1.return_form(comments, 'SPD')
        form_2.return_form(comments, 'SPD')
        self.assertEqual(form_1.created_by, 'mdf594')
        self.assertEqual(form_1.routed_to_dean_by, None)
        self.assertEqual(form_2.routed_to_dean_by, 'sg27674')
        self.assertEqual(form_2.approved_by_dean, None)
        comments = Comments.objects.filter(form_type=form_type,
                                           form_id=form_1.id,)[0]
        self.assertFalse(comments.editable)

    def test_total_possible_countable_degree_hours(self):
        athlete_ccyys_1 = AthleteCcyys.objects.get(ccyys=20159, athlete__eid="taa688")
        athlete_ccyys_2 = AthleteCcyys.objects.get(ccyys=20159, athlete__eid="bka359")
        
        form_1 = AthleteCcyysAdmin.objects.filter(athlete_ccyys=athlete_ccyys_1)[0]
        major_1 = AthleteMajor.objects.get(athlete_ccyys_admin=form_1)
        current_total = form_1.total_possible_countable_degree_hours
        course_1 = Course.objects.create(major=major_1,
                                         course_category='FOO',
                                         course_number='123',
                                         unique='12345',
                                         credit_hours=3,
                                         countable='Y',
                                         min_grade_required='D',
                                         pass_fail_accepted='Y',
                                         grade='A')
        course_1.save()
        self.assertEqual(form_1.total_possible_countable_degree_hours, (current_total + 3))
        
        form_2 = AthleteCcyysAdmin.objects.filter(athlete_ccyys=athlete_ccyys_2)[0]
        major_2 = AthleteMajor.objects.get(athlete_ccyys_admin=form_2)
        current_total = form_2.total_possible_countable_degree_hours
        course_2 = Course.objects.create(major=major_2,
                                         course_category='FOO',
                                         course_number='123',
                                         unique='12345',
                                         credit_hours=3,
                                         countable='N',  # this
                                         min_grade_required='D',
                                         pass_fail_accepted='Y',
                                         grade='A')
        course_2.save()
        self.assertEqual(form_2.total_possible_countable_degree_hours, (current_total + 3))

    def test_total_projected_degree_hours(self):
        athlete_ccyys_1 = AthleteCcyys.objects.get(ccyys=20159, athlete__eid="taa688")
        athlete_ccyys_2 = AthleteCcyys.objects.get(ccyys=20159, athlete__eid="bka359")

        form_1 = AthleteCcyysAdmin.objects.filter(athlete_ccyys=athlete_ccyys_1)[0]
        major_1 = AthleteMajor.objects.get(athlete_ccyys_admin=form_1)
        current_total = form_1.total_projected_degree_hours
        course_1 = Course.objects.create(major=major_1,
                                         course_category='FOO',
                                         course_number='123',
                                         unique='12345',
                                         credit_hours=3,
                                         countable='Y',
                                         min_grade_required='D',
                                         pass_fail_accepted='Y',
                                         grade='A')
        course_1.save()
        self.assertEqual(form_1.total_projected_degree_hours, (current_total + 3))

        form_2 = AthleteCcyysAdmin.objects.filter(athlete_ccyys=athlete_ccyys_2)[0]
        major_2 = AthleteMajor.objects.get(athlete_ccyys_admin=form_2)
        current_total = form_2.total_projected_degree_hours
        course_2 = Course.objects.create(major=major_2,
                                         course_category='FOO',
                                         course_number='123',
                                         unique='12345',
                                         credit_hours=3,
                                         countable='N',  # this
                                         min_grade_required='D',
                                         pass_fail_accepted='Y',
                                         grade='A')
        course_2.save()
        self.assertEqual(form_2.total_projected_degree_hours, current_total)


class PercentDegreeTests(TestCase):

    fixtures = ['entire_db.json']

    def setUp(self):

        # get an major to link form to
        athlete_ccyys_1 = AthleteCcyys.objects.get(ccyys=20159, athlete__eid="taa688")
        athlete_ccyys_2 = AthleteCcyys.objects.get(ccyys=20159, athlete__eid="bka359")
        athlete_ccyys_admin_1 = AthleteCcyysAdmin.objects.get(athlete_ccyys=athlete_ccyys_1)
        athlete_ccyys_admin_2 = AthleteCcyysAdmin.objects.get(athlete_ccyys=athlete_ccyys_2)
        major_1 = AthleteMajor.objects.get(athlete_ccyys_admin=athlete_ccyys_admin_1)
        major_2 = AthleteMajor.objects.get(athlete_ccyys_admin=athlete_ccyys_admin_2)

        first_form = PercentDegree(major=major_1,
                                   created_by="sg27674",
                                   routed_to_dean_by=None,
                                   approved_by_dean=None,
                                   routed_to_reg_by=None,
                                   approved_by_reg=None)
        first_form.save()

        second_form = PercentDegree(major=major_2,
                                    created_by="swevans",
                                    routed_to_dean_by="sg27674",
                                    approved_by_dean=None,
                                    routed_to_reg_by=None,
                                    approved_by_reg=None,
                                    )
        second_form.save()

    def test_form_status(self):
        athlete_ccyys_admin_1 = AthleteCcyysAdmin.objects.get(athlete_ccyys__ccyys=20159,
                                                              athlete_ccyys__athlete__eid="taa688")
        athlete_ccyys_admin_2 = AthleteCcyysAdmin.objects.get(athlete_ccyys__ccyys=20159,
                                                              athlete_ccyys__athlete__eid="bka359")
        major_1 = AthleteMajor.objects.get(athlete_ccyys_admin=athlete_ccyys_admin_1)
        major_2 = AthleteMajor.objects.get(athlete_ccyys_admin=athlete_ccyys_admin_2)
        saved_form_1 = PercentDegree.objects.filter(major=major_1)[0]
        saved_form_2 = PercentDegree.objects.filter(major=major_2)[0]

        saved_form_1.created_by = 'sg27674'
        saved_form_1.routed_to_dean_by = None
        saved_form_1.approved_by_dean = None
        saved_form_1.routed_to_reg_by = None
        saved_form_1.approved_by_reg = None
        saved_form_1.save()
        saved_form_2.created_by = 'sg27674'
        saved_form_2.routed_to_dean_by = 'sg27674'
        saved_form_2.approved_by_dean = None
        saved_form_2.routed_to_reg_by = None
        saved_form_2.approved_by_reg = None
        saved_form_2.save()

        self.assertEqual(saved_form_1.status, PercentDegree.CREATED)
        self.assertEqual(saved_form_2.status, PercentDegree.ROUTED_TO_DEAN)

        saved_form_1.routed_to_dean_by = 'speede'
        saved_form_1.save()
        self.assertEqual(saved_form_1.status, PercentDegree.ROUTED_TO_DEAN)

        saved_form_2.approved_by_dean = 'speede'
        saved_form_2.save()
        self.assertEqual(saved_form_2.status, PercentDegree.APPROVED_BY_DEAN)

    def test_users_turn(self):
        athlete_ccyys_admin_1 = AthleteCcyysAdmin.objects.get(athlete_ccyys__ccyys=20159,
                                                              athlete_ccyys__athlete__eid="taa688")
        athlete_ccyys_admin_2 = AthleteCcyysAdmin.objects.get(athlete_ccyys__ccyys=20159,
                                                              athlete_ccyys__athlete__eid="bka359")
        major_1 = AthleteMajor.objects.get(athlete_ccyys_admin=athlete_ccyys_admin_1)
        major_2 = AthleteMajor.objects.get(athlete_ccyys_admin=athlete_ccyys_admin_2)
        saved_form_1 = PercentDegree.objects.filter(major=major_1)[0]
        saved_form_2 = PercentDegree.objects.filter(major=major_2)[0]
        saved_form_1.created_by = 'sg27674'
        saved_form_1.routed_to_dean_by = None
        saved_form_1.approved_by_dean = None
        saved_form_1.routed_to_reg_by = None
        saved_form_1.approved_by_reg = None
        saved_form_1.save()
        saved_form_2.created_by = 'sg27674'
        saved_form_2.routed_to_dean_by = 'sg27674'
        saved_form_2.approved_by_dean = None
        saved_form_2.routed_to_reg_by = None
        saved_form_2.approved_by_reg = None
        saved_form_2.save()

        user = User.objects.get(eid="sg27674")
        user.type = User.ATHLETICS
        user.save()
        self.assertTrue(saved_form_1.users_turn(user))
        self.assertFalse(saved_form_2.users_turn(user))
        user.type = User.DEAN
        user.school = School.objects.get(code="2")
        user.save()
        saved_form_1.routed_to_dean_by = 'sg27674'
        saved_form_1.created_by = 'sg27674'
        saved_form_1.save()
        saved_form_2.routed_to_dean_by = 'sg27674'
        saved_form_2.save()
        self.assertFalse(saved_form_1.users_turn(user))
        self.assertTrue(saved_form_2.users_turn(user))

        saved_form_2.active = False
        self.assertFalse(saved_form_2.users_turn(user))

    def test_signature_info(self):
        athlete_ccyys_admin_1 = AthleteCcyysAdmin.objects.get(athlete_ccyys__ccyys=20159,
                                                              athlete_ccyys__athlete__eid="taa688")
        athlete_ccyys_admin_2 = AthleteCcyysAdmin.objects.get(athlete_ccyys__ccyys=20159,
                                                              athlete_ccyys__athlete__eid="bka359")
        major_1 = AthleteMajor.objects.get(athlete_ccyys_admin=athlete_ccyys_admin_1)
        major_2 = AthleteMajor.objects.get(athlete_ccyys_admin=athlete_ccyys_admin_2)
        saved_form_1 = PercentDegree.objects.filter(major=major_1)[0]
        saved_form_2 = PercentDegree.objects.filter(major=major_2)[0]
        saved_form_1.routed_to_dean_by = None
        saved_form_1.created_by = 'sg27674'
        saved_form_1.save()
        saved_form_2.routed_to_dean_by = 'sg27674'
        saved_form_2.created_by = 'mdf594'
        saved_form_2.save()
        saved_form_1_sigs = saved_form_1.signature_info
        saved_form_2_sigs = saved_form_2.signature_info

        self.assertTrue('created_by' in saved_form_1_sigs)
        self.assertTrue('approved_by_reg' in saved_form_2_sigs)
        self.assertEqual(saved_form_1_sigs['created_by'], 'Sara D Gore')
        self.assertEqual(saved_form_2_sigs['created_by'], 'Marjorie D Foley')

    def test_advance_routing(self):
        athlete_ccyys_admin_1 = AthleteCcyysAdmin.objects.get(athlete_ccyys__ccyys=20159,
                                                              athlete_ccyys__athlete__eid="rwc767")
        athlete_ccyys_admin_2 = AthleteCcyysAdmin.objects.get(athlete_ccyys__ccyys=20159,
                                                              athlete_ccyys__athlete__eid="eey79")
        major_1 = AthleteMajor.objects.get(athlete_ccyys_admin=athlete_ccyys_admin_1)
        major_2 = AthleteMajor.objects.get(athlete_ccyys_admin=athlete_ccyys_admin_2)
        form_1 = PercentDegree.objects.get(major=major_1)
        form_2 = PercentDegree.objects.get(major=major_2)
        form_1.routed_to_dean_by = "sg27674"
        form_1.save()
        form_2.routed_to_dean_by = 'sg27674'
        form_2.approved_by_dean = 'mdf594'
        form_2.save()
        # test advance_recipient
        self.assertEqual(form_1.advance_recipient, 'Athletic Student Services')
        self.assertEqual(form_2.advance_recipient, 'Registrar Staff')

        # test that the comments are uneditable before routing and editable after
        form_type = ContentType.objects.get_for_model(form_1)
        user = User.objects.get(eid='sg27674')
        comments = Comments.objects.create(form_type=form_type,
                                           form_id=form_1.id,
                                           comments="Blah",
                                           user=user)
        self.assertTrue(comments.editable)

        # test advance_routing
        form_1.advance_routing(user)
        user_2 = User.objects.get(eid='mdf594')
        form_2.advance_routing(user_2)
        self.assertEqual(form_1.approved_by_dean, user.eid)
        self.assertEqual(form_2.routed_to_reg_by, user_2.eid)
        comments = Comments.objects.filter(form_type=form_type,
                                           form_id=form_1.id,)[0]
        self.assertFalse(comments.editable)

    def test_return_form(self):
        athlete_ccyys_admin_1 = AthleteCcyysAdmin.objects.get(athlete_ccyys__ccyys=20159,
                                                              athlete_ccyys__athlete__eid="ejw788")
        athlete_ccyys_admin_2 = AthleteCcyysAdmin.objects.get(athlete_ccyys__ccyys=20159,
                                                              athlete_ccyys__athlete__eid="pu548")
        major_1 = AthleteMajor.objects.get(athlete_ccyys_admin=athlete_ccyys_admin_1)
        major_2 = AthleteMajor.objects.get(athlete_ccyys_admin=athlete_ccyys_admin_2)
        form_1 = PercentDegree.objects.get(major=major_1)
        form_2 = PercentDegree.objects.get(major=major_2)
        form_1.created_by = "mdf594"
        form_1.routed_to_dean_by = "sg27674"
        form_1.approved_by_dean = ""
        form_1.routed_to_reg_by = ""
        form_1.approved_by_reg = ""
        form_1.save()
        form_2.created_by = "mdf594"
        form_2.routed_to_dean_by = "sg27674"
        form_2.approved_by_dean = 'mdf594'
        form_2.routed_to_reg_by = ""
        form_2.approved_by_reg = ""
        form_2.save()
        # test return_recipient
        self.assertEqual(form_1.return_recipient, 'Athletic Student Services')
        self.assertEqual(form_2.return_recipient, 'College')

        # test that the comments are uneditable before routing and editable after
        form_type = ContentType.objects.get_for_model(form_1)
        user = User.objects.get(eid='sg27674')
        comments = Comments.objects.create(form_type=form_type,
                                           form_id=form_1.id,
                                           comments="Blah",
                                           user=user)
        self.assertTrue(comments.editable)

        # test return_form
        form_1.return_form(comments, 'PERCENT_DEGREE')
        form_2.return_form(comments, 'PERCENT_DEGREE')
        self.assertEqual(form_1.created_by, 'mdf594')
        self.assertEqual(form_1.routed_to_dean_by, None)
        self.assertEqual(form_2.routed_to_dean_by, 'sg27674')
        self.assertEqual(form_2.approved_by_dean, None)
        comments = Comments.objects.filter(form_type=form_type,
                                           form_id=form_1.id,)[0]
        self.assertFalse(comments.editable)


class AthleteMajorTests(TestCase):

    fixtures = ['entire_db.json']

    def test_saving_and_retrieving_majors(self):
        athlete_ccyys_admin_1 = AthleteCcyysAdmin.objects.filter(
            athlete_ccyys__athlete__eid="veb388",
            athlete_ccyys__ccyys=20159)[0]
        athlete_ccyys_admin_2 = AthleteCcyysAdmin.objects.filter(
            athlete_ccyys__athlete__eid="acb3746",
            athlete_ccyys__ccyys=20159)[0]
        school = School.objects.get(code='E')
        major_1 = AthleteMajor(
            athlete_ccyys_admin=athlete_ccyys_admin_1,
            major_code='00100',
            major_name='PACE',
            minor='Football Tactics',
            catalog_begin='20159',
            catalog_end='20162',
            school=school)
        major_1.save('sg27674')
        major_2 = AthleteMajor(
            athlete_ccyys_admin=athlete_ccyys_admin_2,
            major_code='65914',
            major_name='Tea Parties',
            minor='Amy Schumer',
            catalog_begin='20159',
            catalog_end='20162',
            school=school)
        major_2.save('sg27674')

    def test_percent_degree(self):
        athlete_ccyys_admin_1 = AthleteCcyysAdmin.objects.filter(
            athlete_ccyys__athlete__eid="veb388",
            athlete_ccyys__ccyys=20159)[0]
        major_1 = AthleteMajor.objects.filter(
            athlete_ccyys_admin=athlete_ccyys_admin_1)[0]
        try:
            pd = major_1.percent_degree
            self.assertTrue(True)
        except:
            self.assertTrue(False)

    def test_catalog_calc(self):
        athlete_ccyys_admin_1 = AthleteCcyysAdmin.objects.filter(
            athlete_ccyys__athlete__eid="veb388",
            athlete_ccyys__ccyys=20159)[0]
        major_1 = AthleteMajor.objects.filter(
            athlete_ccyys_admin=athlete_ccyys_admin_1)[0]
        major_1.catalog_begin = 2010
        major_1.catalog_end = 9999
        # should save end as 2012
        major_1.save('sg27674')
        self.assertEqual(major_1.catalog_end, 2012)


class LogTests(TestCase):

    fixtures = ['entire_db.json']

    def test_saving_and_retrieving_logs(self):
        athlete_ccyys_1 = AthleteCcyys.objects.get(ccyys=20159, athlete__eid="taa688")
        athlete_ccyys_admin_1 = AthleteCcyysAdmin.objects.get(athlete_ccyys=athlete_ccyys_1)
        log = SpdFormLog(updater='sg27674',
                         spd_form=athlete_ccyys_admin_1)
        log.save()
        student_eid = athlete_ccyys_admin_1.athlete_ccyys.athlete.eid
        ccyys = athlete_ccyys_admin_1.athlete_ccyys.ccyys
        self.assertEqual(log.student.eid, student_eid)
        self.assertEqual(log.ccyys, ccyys)

        log_2 = SpdFormLog(updater='sg27674',
                         spd_form=athlete_ccyys_admin_1)
        log_2.save()
        self.assertEqual(log_2.previous_record, log)

    def test_form_saving(self):
        athlete_ccyys_1 = AthleteCcyys.objects.get(ccyys=20159, athlete__eid="knh752")
        athlete_ccyys_admin_1 = AthleteCcyysAdmin.objects.get(athlete_ccyys=athlete_ccyys_1)
        log_1 = SpdFormLog.objects.filter(spd_form=athlete_ccyys_admin_1)[0]
        major_1 = AthleteMajor.objects.get(athlete_ccyys_admin=athlete_ccyys_admin_1)
        major_1.catalog_begin = 2005
        major_1.save('sg27674')
        log_2 = SpdFormLog.objects.filter(spd_form=athlete_ccyys_admin_1)[0]
        self.assertNotEqual(log_1, log_2)
        self.assertEqual(log_2.catalog_begin, '2005')


class UserTests(TestCase):

    fixtures = ['school_majors.json']

    def test_saving_and_retrieving_users(self):
        """This also tests that the TED connection is working
        because on save it should get the user's email address and name."""
        first_user = User(eid="sg27674")
        first_user.type = User.ATHLETICS
        first_user.save()

        second_user = User(eid="magoo")
        second_user.name = "Mr. Magoo"
        second_user.uin = "987654321123456"
        second_user.type = User.REGISTRAR
        second_user.save()

        saved_users = User.objects.all()
        self.assertEqual(saved_users.count(), 2)

        first_saved_user = saved_users[0]
        second_saved_user = saved_users[1]
        self.assertEqual(first_saved_user.name, "Sara Denise Gore")
        self.assertEqual(second_saved_user.name, 'Mr. Magoo')
        self.assertEqual(first_saved_user.email, 'sgore@austin.utexas.edu')
        self.assertTrue(first_saved_user.active)
        self.assertTrue(second_saved_user.active)
        
    def test_admin_status(self):
        first_user = User(eid="barney")
        first_user.name = "Barney"
        first_user.uin = "9999999999999999"
        first_user.type = User.ATHLETICS
        first_user.save()

        second_user = User(eid="meatloaf")
        second_user.name = "Robert Paulsen"
        second_user.uin = "0000000000000000"
        second_user.type = User.DEAN
        second_user.school = School.objects.get(code='E')
        second_user.save()
        
        self.assertTrue(first_user.is_admin())
        self.assertFalse(second_user.is_admin())

    def test_invalid_person(self):
        first_user = User(eid="invalid")
        first_user.name = "Barney"
        first_user.uin = "9999999999999999"
        first_user.type = User.ATHLETICS
        try:
            first_user.save()  # expect it to fail.
            self.assertTrue(False)
        except:
            self.assertTrue(True)


class CourseTests(TestCase):

    fixtures = ['entire_db.json']

    def test_saving_and_retrieving_courses(self):
        athlete_ccyys_admin_1 = AthleteCcyysAdmin.objects.filter(
            athlete_ccyys__athlete__eid="veb388",
            athlete_ccyys__ccyys=20159)[0]
        id = athlete_ccyys_admin_1.id
        major_1 = AthleteMajor.objects.get(athlete_ccyys_admin=athlete_ccyys_admin_1)

        previous_total_countable_hours = athlete_ccyys_admin_1.total_countable_degree_hours
        course_1 = Course.objects.create(major=major_1,
                                         course_category='FOO',
                                         course_number='123',
                                         unique='12345',
                                         credit_hours=3,
                                         countable='Y',
                                         min_grade_required='D',
                                         pass_fail_accepted='Y',
                                         grade='A')
        athlete_ccyys_admin_1 = AthleteCcyysAdmin.objects.get(id=id)
        self.assertNotEqual(previous_total_countable_hours,
                            athlete_ccyys_admin_1.total_countable_degree_hours)
        self.assertEqual(previous_total_countable_hours,
                         (athlete_ccyys_admin_1.total_countable_degree_hours -
                          3))



class GradesTest(TestCase):
    """Tests to insure that the various grades structures
    can meet our needs and audit correctly."""
    
    # can be used to audit valid grades
    def test_valid_grades(self):
        self.assertTrue('A' in GRADES)
        self.assertTrue('CR' in GRADES)
    
    # if it's not cr/nc, it can compare to the min/final grade
    def test_letter_grade_eval(self):
        self.assertTrue(evaluate_for_countable_hrs(A_MINUS, False, A))
        self.assertFalse(evaluate_for_countable_hrs(A, False, A_MINUS))
    
    # if it's NC, you should never have countable hours
    def test_nc_grade_eval(self):
        self.assertFalse(evaluate_for_countable_hrs(CREDIT, 'Y', NO_CREDIT))
        self.assertFalse(evaluate_for_countable_hrs(A, False, NO_CREDIT))
    
    # if it's CR, it counts if P/F true is correct.
    def test_cr_grade_eval(self):
        self.assertFalse(evaluate_for_countable_hrs(A_MINUS, False, CREDIT))
        self.assertFalse(evaluate_for_countable_hrs(CREDIT, False, CREDIT))
        self.assertTrue(evaluate_for_countable_hrs(A_MINUS, 'Y', CREDIT))
        self.assertTrue(evaluate_for_countable_hrs(CREDIT, 'Y', CREDIT))

    # if min value is CR, it counts if it's D- or higher
    def test_min_is_cr(self):
        self.assertFalse(evaluate_for_countable_hrs(CREDIT, 'Y', NO_CREDIT))
        self.assertFalse(evaluate_for_countable_hrs(CREDIT, 'Y', F))
        self.assertFalse(evaluate_for_countable_hrs(CREDIT, 'Y', Q_DROP))
        self.assertTrue(evaluate_for_countable_hrs(CREDIT, 'Y', CREDIT))
        self.assertTrue(evaluate_for_countable_hrs(CREDIT, 'Y', D_MINUS))
    
    # testing that this format can work  
    # in the format needed for Django choices
    def test_letter_choices(self):
        letter_choices = [(grade, grade) for grade in LETTER_GRADES] 
        self.assertTrue(('A-', 'A-') in letter_choices)


class InboxTest(TestCase):
    """Tests for the pieces of the inbox view."""

    fixtures = ['entire_db.json']

    def test_csv_download(self):
        student_majors = AthleteMajor.objects.filter(athlete_ccyys_admin__athlete_ccyys__ccyys=20159)
        response = inbox_download(student_majors)
        # need a better test here....
        self.assertEqual(response.status_code, 200)

    def test_search_by_sport(self):
        student_majors_eids = search_by_sport_code('WSB').values_list('athlete_ccyys_admin__athlete_ccyys__athlete__eid', flat=True)
        self.assertTrue('smc3833' in student_majors_eids)
        self.assertFalse('aa67279' in student_majors_eids)

        # test rowing
        student_majors_eids = search_by_sport_code('WRO').values_list('athlete_ccyys_admin__athlete_ccyys__athlete__eid', flat=True)
        self.assertTrue('saa2962' in student_majors_eids)

        # test track
        student_majors_eids = search_by_sport_code('MTK').values_list('athlete_ccyys_admin__athlete_ccyys__athlete__eid', flat=True)
        self.assertTrue('cca624' in student_majors_eids)
        self.assertTrue('jbt765' in student_majors_eids)

        # test error
        student_majors_eids = search_by_sport_code('').values_list('athlete_ccyys_admin__athlete_ccyys__athlete__eid', flat=True)
        self.assertFalse('smc3833' in student_majors_eids)
        self.assertFalse('aa67279' in student_majors_eids)

    def test_sorting(self):
        student_majors = search_by_sport_code('WSB')

        sort_A_semester = sort_student_majors(student_majors, 'ccyys', ASCENDING)
        self.assertEqual(sort_A_semester[0][0].athlete_ccyys_admin.athlete_ccyys.ccyys, 20159)
        sort_D_semester = sort_student_majors(student_majors, 'ccyys', DESCENDING)
        self.assertEqual(sort_D_semester[0][0].athlete_ccyys_admin.athlete_ccyys.ccyys, 20162)

        sort_A_athlete = sort_student_majors(student_majors, 'athlete', ASCENDING)
        self.assertEqual(sort_A_athlete[0][0].athlete_ccyys_admin.athlete_ccyys.athlete.name, 'CEO, STEPHANIE M')
        sort_D_athlete = sort_student_majors(student_majors, 'athlete', DESCENDING)
        self.assertEqual(sort_D_athlete[0][0].athlete_ccyys_admin.athlete_ccyys.athlete.name, 'WRIGHT, ERICA')

        sort_A_eid = sort_student_majors(student_majors, 'eid', ASCENDING)
        self.assertEqual(sort_A_eid[0][0].athlete_ccyys_admin.athlete_ccyys.athlete.eid, 'dlt2288')
        sort_D_eid = sort_student_majors(student_majors, 'eid', DESCENDING)
        self.assertEqual(sort_D_eid[0][0].athlete_ccyys_admin.athlete_ccyys.athlete.eid, 'trd627')

        sort_A_school = sort_student_majors(student_majors, 'school', ASCENDING)
        self.assertEqual(sort_A_school[0][0].school.code, '2')
        sort_D_school = sort_student_majors(student_majors, 'school', DESCENDING)
        self.assertEqual(sort_D_school[0][0].school.code, 'E')

        sort_A_minor = sort_student_majors(student_majors, 'minor', ASCENDING)
        self.assertEqual(sort_A_minor[0][0].minor, "")
        sort_D_minor = sort_student_majors(student_majors, 'minor', DESCENDING)
        self.assertEqual(sort_D_minor[0][0].minor, "")
        
        sort_A_major = sort_student_majors(student_majors, 'major', ASCENDING)
        self.assertEqual(sort_A_major[0][0].major_code, '00800')
        sort_D_major = sort_student_majors(student_majors, 'major', DESCENDING)
        self.assertEqual(sort_D_major[0][0].major_code, '00100')
        
        sort_A_catalog = sort_student_majors(student_majors, 'catalog_begin', ASCENDING)
        self.assertEqual(sort_A_catalog[0][0].catalog_begin, '2012')
        sort_D_catalog = sort_student_majors(student_majors, 'catalog_begin', DESCENDING)
        self.assertEqual(sort_D_catalog[0][0].catalog_begin, '2014')


