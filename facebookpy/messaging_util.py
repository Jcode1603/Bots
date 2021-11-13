from datetime import datetime
import sqlite3

from socialcommons.time_util import sleep
from .util import update_activity
from .util import click_element
from .util import emergency_exit
from .util import load_user_id
from .util import explicit_wait
from .util import find_user_id
from .util import get_username_from_id
from .util import is_page_available
from .util import reload_webpage
from .util import web_address_navigator
from .util import click_visibly
from .unfriend_util import verify_username_by_id
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from socialcommons.print_log_writer import log_friended_pool
# from socialcommons.print_log_writer import log_record_all_friended
from .database_engine import get_database
from socialcommons.quota_supervisor import quota_supervisor
from .settings import Settings
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import ElementNotVisibleException



def get_message_status(browser, track, username, person, person_id, logger,
                         logfolder):
    """ Verify if you are friending the user in the loaded page """
    if track == "profile":
        if isinstance(person, str):
            ig_homepage = "https://web.facebook.com/"
        elif isinstance(person, int):
            ig_homepage = "https://web.facebook.com/profile.php?id="
        web_address_navigator( browser, ig_homepage + str(person), logger)

    message_button_XP = ("//div[@id='fbTimelineHeadline']/div/div/div/div/button[@type='button'][text()='Message']")
    failure_msg = "--> Unable to detect the message button of '{}'!"
    user_inaccessible_msg = (
        "Couldn't access the profile page of '{}'!\t~might have changed the"
        " username".format(person))

    # check if the page is available
    valid_page = is_page_available(browser, logger, Settings)
    if not valid_page:
        logger.warning(user_inaccessible_msg)
        person_new = verify_username_by_id(browser, username, person, person if isinstance(person, int) else None,
                                           logger,
                                           logfolder)
        if person_new:
            web_address_navigator( browser, ig_homepage + str(person_new), logger)
            valid_page = is_page_available(browser, logger, Settings)
            if not valid_page:
                logger.error(failure_msg.format(person_new.encode("utf-8")))
                return "UNAVAILABLE", None

        else:
            logger.error(failure_msg.format(person.encode("utf-8")))
            return "UNAVAILABLE", None

    # wait until the message button is located and visible, then get it
    message_button = explicit_wait(browser, "VOEL", [message_button_XP, "XPath"], logger, 7, False)
    if not message_button:
        browser.execute_script("location.reload()")
        update_activity()

        message_button = explicit_wait(browser, "VOEL",
                                      [message_button_XP, "XPath"], logger, 14,
                                      False)
        if not message_button:
            # cannot find the any of the expected buttons
            logger.error(failure_msg.format(person.encode("utf-8")))
            return None, None

    # get friend status
    #messaging_status = message_button.text
    return message_button, message_button_XP

def open_message(browser, track, username, person, person_id, logger, logfolder, message, from_group=False):
    if from_group:
        web_address_navigator(browser, person, logger)
    else:
        if isinstance(person, str):
            user_link = "https://web.facebook.com/{}/".format(person)
        elif isinstance(person, int):
            user_link = "https://web.facebook.com/profile.php?id={}/".format(person)
        web_address_navigator( browser, user_link, logger)

    attempt = 0

    while attempt < 1:
        try:
            attempt += 1
            #message_button, message_button_XP = get_message_status(browser, track, username, person, person_id, logger, logfolder)
            message_action_button = browser.find_element_by_xpath("//div[contains(@class,'oajrlxb2 g5ia77u1 qu0x051f esr5mh6w e9989ue4 r7d6kgcz rq0escxv nhd2j8a9 pq6dq46d p7hjln8o kvgmc6g5 cxmmr5t8 oygrvhab hcukyx3x jb3vyjys rz4wbd8a qt6c0cv9 a8nywdso i1ao9s8h esuyzwwr f1sip0of lzcic4wl n00je7tq arfg74bv qs9ysxi8 k77z8yql l9j0dhe7 abiwlrkh p8dawk7l cbu4d94t taijpn5t k4urcfbm')][@aria-label='Message'][@role='button']")
            click_visibly(browser, Settings, message_action_button)
            sleep(4)
            #if message_button:
            """if message_action_button.is_displayed():
                #click_element(browser, Settings, message_action_button)
                #click_visibly(browser, Settings, message_action_button)
                sleep(2)
                break"""
            print('entering message')
            (ActionChains(browser)
            .send_keys(message)
            .send_keys(Keys.ENTER)
            .perform())

            # update server calls for both 'click' and 'send_keys' actions
            for i in range(2):
                update_activity()

            sleep(3)

        except (ElementNotVisibleException, NoSuchElementException) as exc:
            # prob confirm dialog didn't pop up
            if isinstance(exc, ElementNotVisibleException):
                break

            elif isinstance(exc, NoSuchElementException):
                sleep(1)
                pass