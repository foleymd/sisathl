FERPA Check  Implementation Guide

Contents
1. Introduction	
2. Installation	
3. Customization	
    3a. BASE_TEMPLATE	
    3b. UTDirect settings	
        3b1. USE_UTDIRECT	
        3b2. UTDEFAULTS_IMPORT_PATH	
        3b3. UTDEFAULTS_VARIABLE_NAME	
    3c. FERPA_TESTING	
    3d. SYSTEM_NAME	
    3e. WARNING_DAYS
    3f. GRACE_DATE_MMDDYYYY	
    3g. Contact Fields	
        3g1. CONTACT_NAME	
        3g2. CONTACT_NUMBER	
        3g3. CONTACT_EMAIL	
4. Testing	

1. Introduction
The compliance check is designed to programmatically determine whether the user has taken either of the FERPA compliance courses (CW 504 or RG 214) within the last two years. The check will then return one of four possible results and display information to the user based on that result: 

•	P (pass) – No problems! The user is in compliance. On the web, we will set a cookie by default so that we don’t have to keep performing this check. 
•	W (warn) – The user is currently in compliance, but the end of the user’s compliance is approaching. The default is to start displaying this countdown message 45 days prior to expiration. Also, by default we will set a cookie (on the web) and display a warning message screen. 
•	G (grace) – The user’s compliance has expired, but they have been given a grace period until a certain date. By default there is no grace date. However, if one is supplied then the default behavior is to set a server-side web cookie and display a grace message screen. 
•	B (block) – The user’s compliance has expired. The user must get back into compliance before they can proceed. By default no web cookie will be set and a block message screen will be displayed. 

The check also has a number of default settings that can be customized by adding variables to your settings.py or environmental settings. To see the variable options, please refer to the ‘Customization’ section of this document. If you wish to use default values for all optional fields, you will not need to fill any input variables.

2. Installation

    1.	Use svn:externals to add the required files to your project. Detailed instructions can be found at this address:            
            https://wikis.utexas.edu/display/python/Using+external+libraries+with+SVN+externals
    
        In the Property Content box, enter:
            extra/ferpa https://utforge.its.utexas.edu/repos/ferpa_check/trunk
            
    2.	 In your extra folder, create a blank file called __init__.py

    3.	In your settings.py, add a line to TEMPLATE_DIRS pointing to the new ferpa directory:
            TEMPLATE_DIRS = (
            # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
                # Always use forward slashes, even on Windows.
                # Don't forget to use absolute paths, not relative paths.
                os.path.join(CURRENT_DIR, 'templates'),
                os.path.join(CURRENT_DIR, 'extra/ferpa'),
                )
                
    4.	In the views.py in which you wish to use the decorator, add an import statement:
            from group.project.extra.ferpa.ut_ferpa_decorator import FERPACheck

        group and project should be replaced with your actual group and project names.

    5.	Above each view function that requires a check, add this line:
            @FERPACheck
            
        For example:
            
            @FERPACheck
            def my_view(request):
                Blah blah blah

3. Customization
There are many ways the compliance check can be customized, from adjusting the number of warning days to creating your own custom messages based on the information returned from the check. Since there are so many different ways it can be customized, this document will simply explain the variables involved. The comments in ut_ferpa_decorator can also be used as a guide.

These should be set in your settings.py or, where appropriate , in your environment specific settings.

    3a. BASE_TEMPLATE
    The template that you want the error template, ferpa_error.html, to inherit from. You need to have a template of some variety. If 
    one is not provided, it attempts to guess what a likely template name is.

    3b. UTDirect settings
    If you want the error/warning page to render in UTDirect, you need to set the following settings:

        3b1. USE_UTDIRECT
        Set to True to use render error/warning page in UTDirect

        3b2. UTDEFAULTS_IMPORT_PATH
        The qualified path to where your UTD_DEFAULTS dictionary lives. For instance, if it is in a module called ‘constants’ in an app called ‘common’, your path would be the string ‘your_group.your_project.common.constants’

        3b3. UTDEFAULTS_VARIABLE_NAME
        The name of the UTD_DEFAULTS dictionary. It might be UTD_DEFAULTS or defaults or something else.

    3c. FERPA_TESTING
    Only use this in your local settings! Set to True to have it render with mock data. This is useful if you are testing the rendering of ferpa_error.html. 

    3d. SYSTEM_NAME
    The name of the system the compliance check is being implemented in. By default, this is incorporated into the warning, grace, and block messages. If nothing is supplied, defaults to “this system.” (ex. “Access to this system is blocked due to your expired FERPA compliance module training.”)  

    If you want to customize warning days or grace period, a unique SYSTEM_NAME is required.

    3e. WARNING_DAYS
    This is the number of days before the expiration of FERPA compliance that the system will begin warning the user. The input value must be a two digit number. If no value is sent, this defaults to 45 days. If something is input that is not a two digit number, the default value will be used.

    If you want to customize warning days or grace period, a unique SYSTEM_NAME is required.

    3f. GRACE_DATE_MMDDYYYY
    This is the date by which a user will be blocked if their compliance has expired. (ex. “Your FERPA compliance module training has expired. On 12/25/2010 users accessing EASI with expired FERPA compliance modules will be blocked from access.”) If no value is sent, the default is to not have a grace date. If an invalid date is input, no grace date will be used. If the input date is greater than a year from today’s date, the grace date will default to a year from today. 

    If you want to customize warning days or grace period, a unique SYSTEM_NAME is required.

    3g. Contact Fields
    By default these fields are shown to the user when there is a display screen for a warning, a grace, or a block. They tell the user who to contact if there are any questions. If you want to override the default values, you must move information to all three fields or you will get an error and compliance will not be checked. 

        3g1. CONTACT_NAME
        3g2. CONTACT_NUMBER
        3g3. CONTACT_EMAIL

4. Testing
When installing, you will probably want to test locally that the rendered error page matches the look of your site. Here are some tips to help with testing.

    1.	In your local settings, override the PYPE_SERVICE variable, setting it to ‘QUAL’. FERPA compliance data does not exist in the TEST environment.
    2.	In your local settings, create a variable called FERPA_TESTING and set it to True. This will force the page to render the ferpa_error.py using fake data. This does NOT make a broker call. It does not use your local variables either. The information it is showing is the default values if you had ‘warning’ enabled.
    3.	Check your cookies in your browser to make sure you do not currently have a ferpa cookie set. If you do, use the browser tools to delete the relevant cookies.  
