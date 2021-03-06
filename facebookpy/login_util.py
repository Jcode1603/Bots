"""Module only used for the login part of the script"""
# import built-in & third-party modules
import time
import pickle
from selenium.webdriver.common.action_chains import ActionChains

# import FacebookPy modules
from socialcommons.time_util import sleep
from .util import update_activity
from .util import web_address_navigator
from .util import reload_webpage
from .util import click_element
from .util import check_authorization
from .settings import Settings

# import exceptions
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import WebDriverException


def bypass_suspicious_login(browser, bypass_with_mobile):
    """Bypass suspicious loggin attempt verification. This should be only
    enabled
    when there isn't available cookie for the username, otherwise it will and
    shows "Unable to locate email or phone button" message, folollowed by
    CRITICAL - Wrong login data!"""
    # close sign up Facebook modal if available
    try:
        close_button = browser.find_element_by_xpath("[text()='Close']")

        (ActionChains(browser)
         .move_to_element(close_button)
         .click()
         .perform())

        # update server calls
        update_activity()

    except NoSuchElementException:
        pass

    try:
        # click on "This was me" button if challenge page was called
        this_was_me_button = browser.find_element_by_xpath(
            "//button[@name='choice'][text()='This Was Me']")

        (ActionChains(browser)
         .move_to_element(this_was_me_button)
         .click()
         .perform())

        # update server calls
        update_activity()

    except NoSuchElementException:
        # no verification needed
        pass

    try:
        choice = browser.find_element_by_xpath(
            "//label[@for='choice_1']").text

    except NoSuchElementException:
        try:
            choice = browser.find_element_by_xpath(
                "//label[@class='_q0nt5']").text

        except Exception:
            try:
                choice = browser.find_element_by_xpath(
                    "//label[@class='_q0nt5 _a7z3k']").text

            except Exception:
                print("Unable to locate email or phone button, maybe "
                      "bypass_suspicious_login=True isn't needed anymore.")
                return False

    if bypass_with_mobile:
        choice = browser.find_element_by_xpath(
            "//label[@for='choice_0']").text

        mobile_button = browser.find_element_by_xpath(
            "//label[@for='choice_0']")

        (ActionChains(browser)
         .move_to_element(mobile_button)
         .click()
         .perform())

        sleep(5)

    send_security_code_button = browser.find_element_by_xpath(
        "//button[text()='Send Security Code']")

    (ActionChains(browser)
     .move_to_element(send_security_code_button)
     .click()
     .perform())

    # update server calls
    update_activity()

    print('Facebook detected an unusual login attempt')
    print('A security code was sent to your {}'.format(choice))
    security_code = input('Type the security code here: ')

    security_code_field = browser.find_element_by_xpath((
        "//input[@id='security_code']"))

    (ActionChains(browser)
     .move_to_element(security_code_field)
     .click()
     .send_keys(security_code)
     .perform())

    # update server calls for both 'click' and 'send_keys' actions
    for i in range(2):
        update_activity()

    submit_security_code_button = browser.find_element_by_xpath(
        "//button[text()='Submit']")

    (ActionChains(browser)
     .move_to_element(submit_security_code_button)
     .click()
     .perform())

    # update server calls
    update_activity()

    try:
        sleep(5)
        # locate wrong security code message
        wrong_login = browser.find_element_by_xpath((
            "//p[text()='Please check the code we sent you and try "
            "again.']"))

        if wrong_login is not None:
            print(('Wrong security code! Please check the code Facebook'
                   'sent you and try again.'))

    except NoSuchElementException:
        # correct security code
        pass

def login_user(browser,
               username,
               userid,
               password,
               logger,
               logfolder,
               switch_language=True,
               bypass_suspicious_attempt=False,
               bypass_with_mobile=False):
    """Logins the user with the given username and password"""
    assert username, 'Username not provided'
    assert password, 'Password not provided'

    print(username, password)
    ig_homepage = "https://web.facebook.com"
    browser.get(ig_homepage)
    #web_address_navigator( browser, ig_homepage, logger)
    cookie_loaded = False

    # try to load cookie from username
    try:
        for cookie in pickle.load(open('{0}{1}_cookie.pkl'
                                       .format(logfolder, username), 'rb')):
            browser.add_cookie(cookie)
            cookie_loaded = True
    except (WebDriverException, OSError, IOError):
        print("Cookie file not found, creating cookie...")

    # include time.sleep(1) to prevent getting stuck on google.com
    time.sleep(4)

    # changes facebook website language to english to use english xpaths
    if switch_language:
        links = browser.find_elements_by_xpath('//*[@id="pageFooter"]/ul/li')
        for link in links:
            if link.get_attribute('title') == "English (UK)":
                click_element(browser, Settings, link)

    #web_address_navigator( browser, ig_homepage, logger)
    browser.get(ig_homepage)
    time.sleep(5)
    reload_webpage(browser, Settings)
    print("got here ok")

    # cookie has been LOADED, so the user SHOULD be logged in
    # check if the user IS logged in
    """login_state = check_authorization(browser,
                                    "https://web.facebook.com/",
                                    username,
                                    userid,
                                    "activity counts",
                                    logger,
                                    logfolder,
                                    True)
    print('check_authorization:', login_state)"""

    # if user is still not logged in, then there is an issue with the cookie
    # so go create a new cookie..
    if cookie_loaded:
        print("Issue with cookie for user {}. Creating "
              "new cookie...".format(username))

    # # Check if the first div is 'Create an Account' or 'Log In'
    # login_elem = browser.find_element_by_xpath(
    #     '//*[@id="email"]'
    #     )

    # if login_elem is not None:
    #     try:
    #         (ActionChains(browser)
    #          .move_to_element(login_elem)
    #          .click()
    #          .perform())
    #     except MoveTargetOutOfBoundsException:
    #         login_elem.click()

    #     # update server calls
    #     update_activity(Settings)

    # Enter username and password and logs the user in
    # Sometimes the element name isn't 'Username' and 'Password'
    # (valid for placeholder too)

    # wait until it navigates to the login page
    # login_page_title = "Login"
    # explicit_wait(browser, "TC", login_page_title, logger)
    print("inputing login")
    time.sleep(7)

    # wait until the 'username' input element is located and visible
    input_username_XP = '//*[@id="email"]'
    # explicit_wait(browser, "VOEL", [input_username_XP, "XPath"], logger)
    try:
        input_username = browser.find_element_by_xpath(input_username_XP)
    except NoSuchElementException:
        pass
    try:
        print('moving to input_username')
        print('entering input_username')
        (ActionChains(browser)
        .move_to_element(input_username)
        .click()
        .send_keys(username)
        .perform())
    except:
        pass

    # update server calls for both 'click' and 'send_keys' actions
    for i in range(2):
        update_activity()

    sleep(1)

    time.sleep(3)

    #  password
    try:
        input_password = browser.find_elements_by_xpath('//*[@id="pass"]')
    except NoSuchElementException:
        pass

    if not isinstance(password, str):
        password = str(password)
    try:
        print('entering input_password')
        (ActionChains(browser)
        .move_to_element(input_password[0])
        .click().perform())
        time.sleep(3)
        (ActionChains(browser).send_keys(password)
        .perform())
    except:
        pass

    # update server calls for both 'click' and 'send_keys' actions
    for i in range(2):
        update_activity()

    sleep(1)

    print('submitting login_button')
    try:
        login_button = browser.find_element_by_xpath('//*[@type="submit"]')
    except NoSuchElementException:
        pass

    try:
        (ActionChains(browser)
        .move_to_element(login_button)
        .click()
        .perform())
    except:
        print('user already logged in')
        pass

    # update server calls
    update_activity()

    sleep(3)

    # dismiss_get_app_offer(browser, logger)
    # dismiss_notification_offer(browser, logger)

    if bypass_suspicious_attempt is True:
        bypass_suspicious_login(browser, bypass_with_mobile)

    # wait until page fully load
    # explicit_wait(browser, "PFL", [], logger, 5)

    # Check if user is logged-in (If there's two 'nav' elements)
    nav = browser.find_elements_by_xpath('//div[@role="navigation"]')
    if len(nav) == 2:
        # create cookie for username
        print('logged in')
        pickle.dump(browser.get_cookies(), open(
            '{0}{1}_cookie.pkl'.format(logfolder, username), 'wb'))
        return True
    else:
        return False

