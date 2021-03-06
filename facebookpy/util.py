""" Common utilities """
import time
import datetime
from math import ceil
import random
import re
import regex
import signal
import os
from .settings import Settings
from .xpath import read_xpath
import sys
from platform import system
from platform import python_version
from subprocess import call
import csv
import sqlite3
import json
from contextlib import contextmanager
import emoji
from emoji.unicode_codes import UNICODE_EMOJI
from argparse import ArgumentParser
import pickle

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By

from socialcommons.time_util import sleep
from socialcommons.time_util import sleep_actual
from .database_engine import get_database
from .quota_supervisor import quota_supervisor

from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import WebDriverException
from selenium.common.exceptions import TimeoutException


def is_private_profile(Settings, browser, logger, following=True):
    is_private = None
    try:
        is_private = browser.execute_script(
            "return window._sharedData.entry_data."
            "ProfilePage[0].graphql.user.is_private")

    except WebDriverException:
        try:
            browser.execute_script("location.reload()")
            update_activity()

            is_private = browser.execute_script(
                "return window._sharedData.entry_data."
                "ProfilePage[0].graphql.user.is_private")

        except WebDriverException:
            return None

    # double check with xpath that should work only when we not follwoing a
    # user
    if is_private is True and not following:
        logger.info("Is private account you're not following.")
        body_elem = browser.find_element_by_tag_name('body')
        is_private = body_elem.find_element_by_xpath(
            '//h2[@class="_kcrwx"]')

    return is_private


def validate_userid(browser,
                    base_url,
                    userid,
                    own_userid,
                    own_username,
                    ignore_users,
                    blacklist,
                    potency_ratio,
                    delimit_by_numbers,
                    max_followers,
                    max_following,
                    min_followers,
                    min_following,
                    min_posts,
                    max_posts,
                    skip_private,
                    skip_private_percentage,
                    skip_no_profile_pic,
                    skip_no_profile_pic_percentage,
                    skip_business,
                    skip_business_percentage,
                    skip_business_categories,
                    dont_skip_business_categories,
                    logger,
                    logfolder, Settings):
    """Check if we can interact with the user"""
    if userid == own_userid:
        inap_msg = "---> Username '{}' is yours!\t~skipping user\n".format(
            own_userid)
        return False, inap_msg

    if userid in ignore_users:
        inap_msg = "---> '{}' is in the `ignore_users` list\t~skipping " \
                   "user\n".format(userid)
        return False, inap_msg

    blacklist_file = "{}blacklist.csv".format(logfolder)
    blacklist_file_exists = os.path.isfile(blacklist_file)
    if blacklist_file_exists:
        with open("{}blacklist.csv".format(logfolder), 'rt') as f:
            reader = csv.reader(f, delimiter=',')
            for row in reader:
                for field in row:
                    if field == userid:
                        logger.info(
                            'Username in BlackList: {} '.format(userid))
                        return False, "---> {} is in blacklist  ~skipping " \
                                      "user\n".format(userid)

    """Checks the potential of target user by relationship status in order
    to delimit actions within the desired boundary"""
    if potency_ratio or delimit_by_numbers and (
            max_followers or max_following or min_followers or min_following):

        relationship_ratio = None
        reverse_relationship = False

        # get followers & following counts
        followers_count, following_count, friend_count = get_relationship_counts(browser,
                                                                   base_url,
                                                                   userid,
                                                                   userid,
                                                                   logger, Settings)

        if potency_ratio and potency_ratio < 0:
            potency_ratio *= -1
            reverse_relationship = True

        if followers_count and following_count:
            relationship_ratio = (
                float(followers_count) / float(following_count)
                if not reverse_relationship
                else float(following_count) / float(followers_count))

        logger.info(
            "User: '{}'  |> followers: {}  |> following: {} |> friends  |> relationship "
            "ratio: {}"
            .format(userid,
                    followers_count if followers_count else 'unknown',
                    following_count if following_count else 'unknown',
                    friend_count if friend_count else 'unknown',
                    truncate_float(relationship_ratio,
                                   2) if relationship_ratio else 'unknown'))

        if followers_count or following_count:
            if potency_ratio and not delimit_by_numbers:
                if relationship_ratio and relationship_ratio < potency_ratio:
                    inap_msg = (
                        "'{}' is not a {} with the relationship ratio of {}  "
                        "~skipping user\n"
                        .format(userid,
                                "potential user" if not reverse_relationship
                                else "massive follower",
                                truncate_float(relationship_ratio, 2)))
                    return False, inap_msg

            elif delimit_by_numbers:
                if followers_count:
                    if max_followers:
                        if followers_count > max_followers:
                            inap_msg = (
                                "User '{}'s followers count exceeds maximum "
                                "limit  ~skipping user\n"
                                .format(userid))
                            return False, inap_msg

                    if min_followers:
                        if followers_count < min_followers:
                            inap_msg = (
                                "User '{}'s followers count is less than "
                                "minimum limit  ~skipping user\n"
                                .format(userid))
                            return False, inap_msg

                if following_count:
                    if max_following:
                        if following_count > max_following:
                            inap_msg = (
                                "User '{}'s following count exceeds maximum "
                                "limit  ~skipping user\n"
                                .format(userid))
                            return False, inap_msg

                    if min_following:
                        if following_count < min_following:
                            inap_msg = (
                                "User '{}'s following count is less than "
                                "minimum limit  ~skipping user\n"
                                .format(userid))
                            return False, inap_msg

                if potency_ratio:
                    if relationship_ratio and relationship_ratio < \
                            potency_ratio:
                        inap_msg = (
                            "'{}' is not a {} with the relationship ratio of "
                            "{}  ~skipping user\n"
                            .format(userid,
                                    "potential user" if not
                                    reverse_relationship else "massive "
                                                              "follower",
                                    truncate_float(relationship_ratio, 2)))
                        return False, inap_msg

    # TODO All graphql logics have to be reimplemented
    # ie POST, Profile pic, business related logics have to be rewitten
    # if min_posts or max_posts or skip_private or skip_no_profile_pic or \
    #         skip_business:
    #     user_link = "https://www.facebook.com/{}/".format(userid)
    #     web_address_navigator(browser, user_link)

    # if min_posts or max_posts:
    #     # if you are interested in relationship number of posts boundaries
    #     try:
    #         number_of_posts = getUserData(
    #             "graphql.user.edge_owner_to_timeline_media.count", browser)
    #     except WebDriverException:
    #         logger.error("~cannot get number of posts for userid")
    #         inap_msg = "---> Sorry, couldn't check for number of posts of " \
    #                    "userid\n"
    #         return False, inap_msg
    #     if max_posts:
    #         if number_of_posts > max_posts:
    #             inap_msg = (
    #                 "Number of posts ({}) of '{}' exceeds the maximum limit "
    #                 "given {}\n"
    #                 .format(number_of_posts, userid, max_posts))
    #             return False, inap_msg
    #     if min_posts:
    #         if number_of_posts < min_posts:
    #             inap_msg = (
    #                 "Number of posts ({}) of '{}' is less than the minimum "
    #                 "limit given {}\n"
    #                 .format(number_of_posts, userid, min_posts))
    #             return False, inap_msg

    """Skip users"""
    # skip no profile pic
    # if skip_no_profile_pic:
    #     try:
    #         profile_pic = getUserData("graphql.user.profile_pic_url", browser)
    #     except WebDriverException:
    #         logger.error("~cannot get the post profile pic url")
    #         return False, "---> Sorry, couldn't get if user profile pic url\n"
    #     if (profile_pic in default_profile_pic_facebook or str(
    #             profile_pic).find(
    #             "11906329_960233084022564_1448528159_a.jpg") > 0) and (
    #             random.randint(0, 100) <= skip_no_profile_pic_percentage):
    #         return False, "{} has default facebook profile picture\n".format(
    #             userid)

    # skip business
    # if skip_business:
    #     # if is business account skip under conditions
    #     try:
    #         is_business_account = getUserData(
    #             "graphql.user.is_business_account", browser)
    #     except WebDriverException:
    #         logger.error("~cannot get if user has business account active")
    #         return False, "---> Sorry, couldn't get if user has business " \
    #                       "account active\n"

    #     if is_business_account:
    #         try:
    #             category = getUserData("graphql.user.business_category_name",
    #                                    browser)
    #         except WebDriverException:
    #             logger.error("~cannot get category name for user")
    #             return False, "---> Sorry, couldn't get category name for " \
    #                           "user\n"

    #         if len(skip_business_categories) == 0:
    #             # skip if not in dont_include
    #             if category not in dont_skip_business_categories:
    #                 if len(dont_skip_business_categories) == 0 and (
    #                         random.randint(0,
    #                                        100) <= skip_business_percentage):
    #                     return False, "'{}' has a business account\n".format(
    #                         userid)
    #                 else:
    #                     return False, ("'{}' has a business account in the "
    #                                    "undesired category of '{}'\n"
    #                                    .format(userid, category))
    #         else:
    #             if category in skip_business_categories:
    #                 return False, ("'{}' has a business account in the "
    #                                "undesired category of '{}'\n"
    #                                .format(userid, category))

    # if everything is ok
    return True, "Valid user"


# def getUserData(Settings,
#                 query,
#                 browser,
#                 basequery="return window._sharedData.entry_data.ProfilePage["
#                           "0]."):
#     try:
#         data = browser.execute_script(
#             basequery + query)
#         return data
#     except WebDriverException:
#         browser.execute_script("location.reload()")
#         update_activity(Settings)

#         data = browser.execute_script(
#             basequery + query)
#         return data


def update_activity(action="server_calls"):
    """ Record every Facebook server call (page load, content load, likes,
        comments, follows, unfollow). """
    # check action availability
    quota_supervisor("server_calls")

    # get a DB and start a connection
    db, id = get_database(Settings)
    conn = sqlite3.connect(db)

    with conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        # collect today data
        cur.execute(
            "SELECT * FROM recordActivity WHERE profile_id=:var AND "
            "STRFTIME('%Y-%m-%d %H', created) == STRFTIME('%Y-%m-%d "
            "%H', 'now', 'localtime')",
            {"var": id},
        )
        data = cur.fetchone()

        if data is None:
            # create a new record for the new day
            cur.execute(
                "INSERT INTO recordActivity VALUES "
                "(?, 0, 0, 0, 0, 0, 0, 1, STRFTIME('%Y-%m-%d %H:%M:%S', "
                "'now', 'localtime'))",
                (id,),
            )

        else:
            # sqlite3.Row' object does not support item assignment -> so,
            # convert it into a new dict
            data = dict(data)
            print(data)

            # update
            data[action] += 1
            quota_supervisor(action, update=True)

            if action != "server_calls":
                # always update server calls
                data["server_calls"] += 1
                quota_supervisor("server_calls", update=True)

            sql = ("UPDATE recordActivity set likes = ?, comments = ?, "
                   "follows = ?, unfollows = ?, friendeds = ?, unfriendeds = ?, server_calls = ?, "
                   "created = STRFTIME('%Y-%m-%d %H:%M:%S', 'now', "
                   "'localtime') "
                   "WHERE  profile_id=? AND STRFTIME('%Y-%m-%d %H', created) "
                   "== "
                   "STRFTIME('%Y-%m-%d %H', 'now', 'localtime')")

            cur.execute(sql, (data['likes'], data['comments'], data['follows'],
                              data['unfollows'], data['friendeds'],
                              data['unfriendeds'], data['server_calls'], id))

        # commit the latest changes
        conn.commit()


def add_user_to_blacklist(username, campaign, action, logger, logfolder):
    file_exists = os.path.isfile('{}blacklist.csv'.format(logfolder))
    fieldnames = ['date', 'username', 'campaign', 'action']
    today = datetime.date.today().strftime('%m/%d/%y')

    try:
        with open('{}blacklist.csv'.format(logfolder), 'a+') as blacklist:
            writer = csv.DictWriter(blacklist, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            writer.writerow({
                'date': today,
                'username': username,
                'campaign': campaign,
                'action': action
            })
    except Exception as err:
        logger.error('blacklist dictWrite error {}'.format(err))

    logger.info('--> {} added to blacklist for {} campaign (action: {})'
                .format(username, campaign, action))


# def get_active_users(browser, username, userid, posts, boundary, logger, Selectors):
#     """Returns a list with usernames who liked the latest n posts"""

#     user_link = 'https://www.facebook.com/{}/'.format(userid)

#     # check URL of the webpage, if it already is user's profile page,
#     # then do not navigate to it again
#     web_address_navigator(browser, user_link)

#     try:
#         total_posts = browser.execute_script(
#             "return window._sharedData.entry_data."
#             "ProfilePage[0].graphql.user.edge_owner_to_timeline_media.count")

#     except WebDriverException:
#         try:
#             topCount_elements = browser.find_elements_by_xpath(
#                 "//span[contains(@class,'g47SY')]")

#             if topCount_elements:  # prevent an empty string scenario
#                 total_posts = format_number(topCount_elements[0].text)

#             else:
#                 logger.info(
#                     "Failed to get posts count on your profile!  ~empty "
#                     "string")
#                 total_posts = None

#         except NoSuchElementException:
#             logger.info("Failed to get posts count on your profile!")
#             total_posts = None

#     # if posts > total user posts, assume total posts
#     posts = posts if total_posts is None else total_posts if posts > \
#                                                              total_posts \
#         else posts

#     # click latest post
#     try:
#         latest_posts = browser.find_elements_by_xpath(
#             "//div[contains(@class, '_9AhH0')]")
#         # avoid no posts
#         if latest_posts:
#             latest_post = latest_posts[0]
#             click_element(browser, Settings, latest_post)

#     except (NoSuchElementException, WebDriverException):
#         logger.warning(
#             "Failed to click on the latest post to grab active likers!\n")
#         return []

#     active_users = []
#     sc_rolled = 0
#     start_time = time.time()
#     too_many_requests = 0  # helps to prevent misbehaviours when requests
#     # list of active users repeatedly within less than 10 min of breaks

#     message = (
#         "~collecting the entire usernames from posts without a boundary!\n"
#         if boundary is None else
#         "~collecting only the visible usernames from posts without scrolling "
#         "at the boundary of zero..\n" if boundary == 0 else
#         "~collecting the usernames from posts with the boundary of {}"
#         "\n".format(
#             boundary))
#     # posts argument is the number of posts to collect usernames
#     logger.info(
#         "Getting active users who liked the latest {} posts:\n  {}".format(
#             posts, message))

#     for count in range(1, posts + 1):
#         try:
#             sleep_actual(2)
#             try:
#                 likers_count = browser.execute_script(
#                     "return window._sharedData.entry_data."
#                     "PostPage["
#                     "0].graphql.shortcode_media.edge_media_preview_like.count")
#             except WebDriverException:
#                 try:
#                     likers_count = (browser.find_element_by_xpath(
#                         "//button[contains(@class, '_8A5w5')]/span").text)
#                     if likers_count:  # prevent an empty string scenarios
#                         likers_count = format_number(likers_count)
#                     else:
#                         logger.info(
#                             "Failed to get likers count on your post {}  "
#                             "~empty string".format(
#                                 count))
#                         likers_count = None
#                 except NoSuchElementException:
#                     logger.info(
#                         "Failed to get likers count on your post {}".format(
#                             count))
#                     likers_count = None
#             try:
#                 likes_button = browser.find_elements_by_xpath(
#                     "//button[contains(@class, '_8A5w5')]")[1]
#                 click_element(browser, Settings, likes_button)
#                 sleep_actual(5)
#             except (IndexError, NoSuchElementException):
#                 # Video have no likes button / no posts in page
#                 continue

#             # get a reference to the 'Likes' dialog box
#             dialog = browser.find_element_by_xpath(
#                 Selectors.likes_dialog_body_xpath)

#             scroll_it = True
#             try_again = 0
#             start_time = time.time()
#             user_list = []

#             if likers_count:
#                 amount = (
#                     likers_count if boundary is None
#                     else None if boundary == 0
#                     else (
#                         boundary if boundary < likers_count
#                         else likers_count
#                     )
#                 )
#             else:
#                 amount = None

#             while scroll_it is not False and boundary != 0:
#                 scroll_it = browser.execute_script('''
#                     var div = arguments[0];
#                     if (div.offsetHeight + div.scrollTop < div.scrollHeight) {
#                         div.scrollTop = div.scrollHeight;
#                         return true;}
#                     else {
#                         return false;}
#                     ''', dialog)

#                 if scroll_it is True:
#                     update_activity(Settings)

#                 if sc_rolled > 91 or too_many_requests > 1:  # old value 100
#                     print('\n')
#                     logger.info(
#                         "Too Many Requests sent! ~will sleep some :>\n")
#                     sleep_actual(600)
#                     sc_rolled = 0
#                     too_many_requests = 0 if too_many_requests >= 1 else \
#                         too_many_requests

#                 else:
#                     sleep_actual(1.2)  # old value 5.6
#                     sc_rolled += 1

#                 """ Old method 1 """
#                 # tmp_list = browser.find_elements_by_xpath(
#                 #     "//a[contains(@class, 'FPmhX')]")

#                 user_list = get_users_from_dialog(user_list, dialog)
#                 # print("len(user_list): {}".format(len(user_list)))

#                 # write & update records at Progress Tracker
#                 if amount:
#                     progress_tracker(len(user_list), amount, start_time, None)

#                 if boundary is not None:
#                     if len(user_list) >= boundary:
#                         break

#                 if (scroll_it is False and
#                         likers_count and
#                         likers_count - 1 > len(user_list)):

#                     if ((boundary is not None
#                          and likers_count - 1 > boundary)
#                             or boundary is None):

#                         if try_again <= 1:  # can increase the amount of tries
#                             print('\n')
#                             logger.info(
#                                 "Cor! Failed to get the desired amount of "
#                                 "usernames but trying again.."
#                                 "\t|> post:{}  |> attempt: {}\n"
#                                 .format(posts, try_again + 1))
#                             try_again += 1
#                             too_many_requests += 1
#                             scroll_it = True
#                             nap_it = 4 if try_again == 0 else 7
#                             sleep_actual(nap_it)

#             print('\n')
#             user_list = get_users_from_dialog(user_list, dialog)

#             logger.info("Post {}  |  Likers: found {}, catched {}\n\n".format(
#                 count, likers_count, len(user_list)))

#         except NoSuchElementException as exc:
#             logger.error("Ku-ku! There is an error searching active users"
#                          "~\t{}\n\n".format(str(exc).encode("utf-8")))

#             """ Old method 2 """
#             # try:
#             #     tmp_list = browser.find_elements_by_xpath(
#             #         "//div[contains(@class, '_1xe_U')]/a")

#             #     if len(tmp_list) > 0:
#             #         logger.info(
#             #             "Post {}  |  Likers: found {}, catched {}".format(
#             #                 count, len(tmp_list), len(tmp_list)))

#             # except NoSuchElementException:
#             #     print("Ku-ku")

#         for user in user_list:
#             active_users.append(user)

#         sleep_actual(1)

#         # if not reached posts(parameter) value, continue
#         if count + 1 != posts + 1 and count != 0:
#             try:
#                 # click close button
#                 close_dialog_box(browser)

#                 # click next button
#                 next_button = browser.find_element_by_xpath(
#                     "//a[contains(@class, 'HBoOv')]"
#                     "[text()='Next']")
#                 click_element(browser, Settings, next_button)

#             except Exception:
#                 logger.error('Unable to go to next profile post')

#     real_time = time.time()
#     diff_in_minutes = int((real_time - start_time) / 60)
#     diff_in_seconds = int((real_time - start_time) % 60)

#     # delete duplicated users
#     active_users = list(set(active_users))

#     logger.info(
#         "Gathered total of {} unique active followers from the latest {} "
#         "posts in {} minutes and {} seconds".format(len(active_users),
#                                                     posts,
#                                                     diff_in_minutes,
#                                                     diff_in_seconds))

#     return active_users


def delete_line_from_file(filepath, userToDelete, logger):
    """ Remove user's record from the followed pool file after unfollowing """
    if not os.path.isfile(filepath):
        # in case of there is no any followed pool file yet
        return 0

    try:
        file_path_old = filepath + ".old"
        file_path_Temp = filepath + ".temp"

        with open(filepath, "r") as f:
            lines = f.readlines()

        with open(file_path_Temp, "w") as f:
            for line in lines:
                entries = line.split(" ~ ")
                sz = len(entries)
                if sz == 1:
                    user = entries[0][:-2]
                elif sz == 2:
                    user = entries[1][:-2]
                else:
                    user = entries[1]

                if user == userToDelete:
                    slash_in_filepath = '/' if '/' in filepath else '\\'
                    filename = filepath.split(slash_in_filepath)[-1]
                    logger.info("\tRemoved '{}' from {} file".format(
                        line.split(',\n')[0], filename))

                else:
                    f.write(line)

        # File leftovers that should not exist, but if so remove it
        while os.path.isfile(file_path_old):
            try:
                os.remove(file_path_old)

            except OSError as e:
                logger.error("Can't remove file_path_old {}".format(str(e)))
                sleep(5)

        # rename original file to _old
        os.rename(filepath, file_path_old)

        # rename new temp file to filepath
        while os.path.isfile(file_path_Temp):
            try:
                os.rename(file_path_Temp, filepath)

            except OSError as e:
                logger.error(
                    "Can't rename file_path_Temp to filepath {}".format(
                        str(e)))
                sleep(5)

        # remove old and temp file
        os.remove(file_path_old)

    except BaseException as e:
        logger.error("delete_line_from_file error {}\n{}".format(
            str(e).encode("utf-8")))


def scroll_bottom(browser, element, range_int):
    # put a limit to the scrolling
    if range_int > 50:
        range_int = 50

    for i in range(int(range_int / 2)):
        browser.execute_script(
            "arguments[0].scrollTop = arguments[0].scrollHeight", element)
        # update server calls
        update_activity()
        sleep(1)

    return


def click_element(browser, Settings, element, tryNum=0):
    """
    There are three (maybe more) different ways to "click" an element/button.
    1. element.click()
    2. element.send_keys("\n")
    3. browser.execute_script("document.getElementsByClassName('" +
    element.get_attribute("class") + "')[0].click()")

    I'm guessing all three have their advantages/disadvantages
    Before committing over this code, you MUST justify your change
    and potentially adding an 'if' statement that applies to your
    specific case. See the following issue for more details
    https://github.com/socialbotspy/FacebookPy/issues/1232

    explaination of the following recursive function:
      we will attempt to click the element given, if an error is thrown
      we know something is wrong (element not in view, element doesn't
      exist, ...). on each attempt try and move the screen around in
      various ways. if all else fails, programmically click the button
      using `execute_script` in the browser.
      """

    try:
        # use Selenium's built in click function
        element.click()

        # update server calls after a successful click by selenium
        update_activity()

    except Exception:
        # click attempt failed
        # try something funky and try again

        if tryNum == 0:
            # try scrolling the element into view
            browser.execute_script(
                "document.getElementsByClassName('" + element.get_attribute(
                    "class") + "')[0].scrollIntoView({ inline: 'center' });")

        elif tryNum == 1:
            # well, that didn't work, try scrolling to the top and then
            # clicking again
            browser.execute_script("window.scrollTo(0,0);")

        elif tryNum == 2:
            # that didn't work either, try scrolling to the bottom and then
            # clicking again
            browser.execute_script(
                "window.scrollTo(0,document.body.scrollHeight);")

        else:
            # try `execute_script` as a last resort
            # print("attempting last ditch effort for click, `execute_script`")
            browser.execute_script(
                "document.getElementsByClassName('" + element.get_attribute(
                    "class") + "')[0].click()")
            # update server calls after last click attempt by JS
            update_activity()
            # end condition for the recursive function
            return

        # update server calls after the scroll(s) in 0, 1 and 2 attempts
        update_activity()

        # sleep for 1 second to allow window to adjust (may or may not be
        # needed)
        sleep_actual(1)

        tryNum += 1

        # try again!
        click_element(browser, Settings, element, tryNum)


def format_number(number):
    """
    Format number. Remove the unused comma. Replace the concatenation with
    relevant zeros. Remove the dot.

    :param number: str

    :return: int
    """
    formatted_num = number.replace(',', '')
    formatted_num = re.sub(r'(k)$', '00' if '.' in formatted_num else '000',
                           formatted_num)
    formatted_num = re.sub(r'(m)$',
                           '00000' if '.' in formatted_num else '000000',
                           formatted_num)
    formatted_num = formatted_num.replace('.', '')
    try:
        return int(formatted_num)
    except Exception:
        return 0


# def username_url_to_username(base_url, username_url):
#     a = username_url.replace(base_url, "")
#     username = a.split('/')
#     return username[0]


def get_number_of_posts(browser):
    """Get the number of posts from the profile screen"""
    try:
        num_of_posts = browser.execute_script(
            "return window._sharedData.entry_data."
            "ProfilePage[0].graphql.user.edge_owner_to_timeline_media.count")

    except WebDriverException:

        try:
            num_of_posts_txt = browser.find_element_by_xpath(
                "//section/main/div/header/section/ul/li[1]/span/span").text

        except NoSuchElementException:
            num_of_posts_txt = browser.find_element_by_xpath(
                "//section/div[3]/div/header/section/ul/li[1]/span/span").text

        num_of_posts_txt = num_of_posts_txt.replace(" ", "")
        num_of_posts_txt = num_of_posts_txt.replace(",", "")
        num_of_posts = int(num_of_posts_txt)

    return num_of_posts


def get_friend_count(browser, base_url, username, userid, logger, Settings):
    """ Gets the followers & following counts of a given user """
    if base_url[-1] != '/':
        base_url = base_url + '/'
    user_link = base_url + "{}/friends".format(userid)
    web_address_navigator(browser, user_link, logger)

    try:
        friend_count = browser.execute_script(
            "return window._sharedData.entry_data."
            "ProfilePage[0].graphql.user.edge_follow.count")

    except WebDriverException:
        try:
            friend_count = format_number(
                browser.find_element_by_xpath(Settings.friend_count_xpath).text)

        except NoSuchElementException as e:
            logger.error(e)
            return None
    return friend_count

def get_following_count(browser, base_url, username, userid, logger, Settings):
    """ Gets the followers & following counts of a given user """
    if base_url[-1] != '/':
        base_url = base_url + '/'
    user_link = base_url + "{}/following".format(userid)
    web_address_navigator(browser, user_link, logger)

    try:
        following_count = browser.execute_script(
            "return window._sharedData.entry_data."
            "ProfilePage[0].graphql.user.edge_follow.count")

    except WebDriverException:
        try:
            following_count = format_number(
                browser.find_element_by_xpath(Settings.following_count_xpath).text)

        except NoSuchElementException as e:
            logger.error(e)
            return None
    return following_count


def get_followers_count_nonfriend_public_case(
        browser, username, userid, logger):
    try:
        followers_text = browser.find_element_by_xpath(
            '//*[@id="pagelet_collections_followers"]/div/div[1]/div/a[@role="button"]/span').text.strip()
        followers_count = [
            format_number(s) for s in followers_text.split() if s.isdigit()][0]
    except NoSuchElementException as e2:
        logger.error(e2)
        return None
    return followers_count


def get_followers_count(browser, base_url, username, userid, logger, Settings):
    """ Gets the followers & following counts of a given user """
    if not base_url.endswith('/'):
        base_url = base_url + '/'
    user_link = base_url + "{}/followers".format(userid)
    web_address_navigator(browser, user_link, logger)

    # try:
    #     followers_count = browser.execute_script(
    #         "return window._sharedData.entry_data."
    #         "ProfilePage[0].graphql.user.edge_follow.count")
    # except WebDriverException:
    try:
        followers_count = format_number(
            browser.find_element_by_xpath(Settings.followers_count_xpath).text)
        if followers_count == 0:
            followers_count = get_followers_count_nonfriend_public_case(
                browser, username, userid, logger)
    except NoSuchElementException as e:
        logger.error(e)
        followers_count = get_followers_count_nonfriend_public_case(
            browser, username, userid, logger)
    return followers_count


def get_relationship_counts(
        browser, base_url, username, userid, logger, Settings):
    """ Gets the followers & following counts of a given user """
    followers_count = get_followers_count(
        browser, base_url, username, userid, logger, Settings)
    following_count = get_following_count(
        browser, base_url, username, userid, logger, Settings)
    friend_count = get_friend_count(
        browser, base_url, username, userid, logger, Settings)
    
    logger.info('followers_count = {}'.format(followers_count))
    logger.info('following_count = {}'.format(following_count))
    return followers_count, following_count, friend_count


def web_address_navigator(browser, link, logger):
    """Checks and compares current URL of web page and the URL to be
    navigated and if it is different, it does navigate"""
    current_url = get_current_url(browser)
    if current_url.strip("/") == link.strip("/"):
        return
    total_timeouts = 0
    page_type = None  # file or directory

    logger.info("Navigating from {} To {}".format(current_url, link))
    # remove slashes at the end to compare efficiently
    if current_url is not None and current_url.endswith('/'):
        current_url = current_url[:-1]

    if link.endswith('/'):
        link = link[:-1]
        page_type = "dir"  # slash at the end is a directory

    new_navigation = (current_url != link)

    if current_url is None or new_navigation:
        link = link + '/' if page_type == "dir" else link  # directory links
        # navigate faster
        while True:
            try:
                browser.get(link)
                # update server calls
                update_activity()
                sleep(2)
                break

            except TimeoutException as exc:
                if total_timeouts >= 7:
                    raise TimeoutException(
                        "Retried {} times to GET '{}' webpage "
                        "but failed out of a timeout!\n\t{}".format(
                            total_timeouts,
                            str(link).encode("utf-8"),
                            str(exc).encode("utf-8")))
                total_timeouts += 1
                sleep(2)


@contextmanager
def interruption_handler(threaded=False, SIG_type=signal.SIGINT,
                         handler=signal.SIG_IGN, notify=None, logger=None):
    """ Handles external interrupt, usually initiated by the user like
    KeyboardInterrupt with CTRL+C """
    if notify is not None and logger is not None:
        logger.warning(notify)

    if not threaded:
        original_handler = signal.signal(SIG_type, handler)

    try:
        yield

    finally:
        if not threaded:
            signal.signal(SIG_type, original_handler)


def highlight_print(Settings, username=None, message=None, priority=None, level=None,
                    logger=None):
    """ Print headers in a highlighted style """
    # can add other highlighters at other priorities enriching this function

    # find the number of chars needed off the length of the logger message
    output_len = (28 + len(username) + 3 + len(message) if logger
                  else len(message))
    show_logs = Settings.show_logs

    if priority in ["initialization", "end"]:
        # OOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO
        # E.g.:          Session started!
        # oooooooooooooooooooooooooooooooooooooooooooooooo
        upper_char = "O"
        lower_char = "o"

    elif priority == "login":
        # ................................................
        # E.g.:        Logged in successfully!
        # ''''''''''''''''''''''''''''''''''''''''''''''''
        upper_char = "."
        lower_char = "'"

    elif priority == "feature":  # feature highlighter
        # ________________________________________________
        # E.g.:    Starting to interact by users..
        # """"""""""""""""""""""""""""""""""""""""""""""""
        upper_char = "_"
        lower_char = "\""

    elif priority == "user iteration":
        # ::::::::::::::::::::::::::::::::::::::::::::::::
        # E.g.:            User: [1/4]
        upper_char = ":"
        lower_char = None

    elif priority == "post iteration":
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # E.g.:            Post: [2/10]
        upper_char = "~"
        lower_char = None

    elif priority == "workspace":
        # ._. ._. ._. ._. ._. ._. ._. ._. ._. ._. ._. ._.
        # E.g.: |> Workspace in use: "C:/Users/El/FacebookPy"
        upper_char = " ._. "
        lower_char = None

    if (upper_char
        and (show_logs
             or priority == "workspace")):
        print("\n{}".format(
            upper_char * int(ceil(output_len / len(upper_char)))))

    if level == "info":
        if logger:
            logger.info(message)
        else:
            print(message)

    elif level == "warning":
        if logger:
            logger.warning(message)
        else:
            print(message)

    elif level == "critical":
        if logger:
            logger.critical(message)
        else:
            print(message)

    if (lower_char
        and (show_logs
             or priority == "workspace")):
        print("{}".format(
            lower_char * int(ceil(output_len / len(lower_char)))))


def remove_duplicates(container, keep_order, logger):
    """ Remove duplicates from all kinds of data types easily """
    # add support for data types as needed in future
    # currently only 'list' data type is supported
    if isinstance(container, list):
        if keep_order is True:
            result = sorted(set(container), key=container.index)

        else:
            result = set(container)

    else:
        if not logger:
            logger = Settings.logger

        logger.warning("The given data type- '{}' is not supported "
                       "in `remove_duplicates` function, yet!"
                       .format(type(container)))
        result = container

    return result


# def dump_record_activity(profile_name, logger, logfolder, Settings):
#     """ Dump the record activity data to a local human-readable JSON """

#     try:
#         # get a DB and start a connection
#         db, id = get_database(Settings)
#         conn = sqlite3.connect(db)

#         with conn:
#             conn.row_factory = sqlite3.Row
#             cur = conn.cursor()

#             cur.execute("SELECT * FROM recordActivity WHERE profile_id=:var",
#                         {"var": id})
#             user_data = cur.fetchall()

#         if user_data:
#             ordered_user_data = {}
#             current_data = {}

#             # get the existing data
#             filename = "{}recordActivity.json".format(logfolder)
#             if os.path.isfile(filename):
#                 with open(filename) as recordActFile:
#                     current_data = json.load(recordActFile)

#             # re-order live user data in the required structure
#             for hourly_data in user_data:
#                 hourly_data = tuple(hourly_data)
#                 day = hourly_data[-1][:10]
#                 hour = hourly_data[-1][-8:-6]

#                 if day not in ordered_user_data.keys():
#                     ordered_user_data.update({day: {}})

#                 ordered_user_data[day].update({hour: {"likes": hourly_data[1],
#                                                       "comments": hourly_data[
#                                                           2],
#                                                       "follows": hourly_data[
#                                                           3],
#                                                       "unfollows": hourly_data[
#                                                           4],
#                                                       "server_calls":
#                                                           hourly_data[5]}})

#             # update user data with live data whilst preserving all other
#             # data (keys)
#             current_data.update({profile_name: ordered_user_data})

#             # dump the fresh record data to a local human readable JSON
#             with open(filename, 'w') as recordActFile:
#                 json.dump(current_data, recordActFile)

#     except Exception as exc:
#         logger.error(
#             "Pow! Error occurred while dumping record activity data to a "
#             "local JSON:\n\t{}".format(
#                 str(exc).encode("utf-8")))

#     finally:
#         if conn:
#             # close the open connection
#             conn.close()


def ping_server(host, logger):
    """
    Return True if host (str) responds to a ping request.
    Remember that a host may not respond to a ping (ICMP) request even if
    the host name is valid.
    """
    logger.info("Pinging '{}' to check the connectivity...".format(str(host)))

    # ping command count option as function of OS
    param = "-n" if system().lower() == "windows" else "-c"
    # building the command. Ex: "ping -c 1 google.com"
    command = ' '.join(["ping", param, '1', str(host)])
    need_sh = False if system().lower() == "windows" else True

    # pinging
    ping_attempts = 2
    connectivity = None

    while connectivity is not True and ping_attempts > 0:
        connectivity = call(command, shell=need_sh) == 0

        if connectivity is False:
            logger.warning(
                "Pinging the server again!\t~total attempts left: {}"
                .format(ping_attempts))
            ping_attempts -= 1
            sleep(5)

    if connectivity is False:
        logger.critical(
            "There is no connection to the '{}' server!".format(host))
        return False

    return True


def emergency_exit(browser, Settings, base_url, username,
                   userid, logger, logfolder, login_state=None):
    """ Raise emergency if the is no connection to server OR if user is not
    logged in """
    using_proxy = True if Settings.connection_type == "proxy" else False
    # ping the server only if connected directly rather than through a proxy
    if not using_proxy:
        server_address = base_url
        connection_state = ping_server(server_address, logger)
        if connection_state is False:
            return True, "not connected"

    # check if the user is logged in
    method = "activity counts"
    if login_state is None:
        login_state = check_authorization(
            browser,
            base_url,
            username,
            userid, method,
            logger,
            logfolder)
    if login_state is False:
        return True, "not logged in"

    return False, "no emergency"


def load_user_id(username, person, logger, logfolder):
    """ Load the user ID at reqeust from local records """
    pool_name = "{0}{1}_followedPool.csv".format(logfolder, username)
    user_id = "undefined"

    try:
        with open(pool_name, 'r+') as followedPoolFile:
            reader = csv.reader(followedPoolFile)

            for row in reader:
                entries = row[0].split(' ~ ')
                if len(entries) < 3:
                    # old entry which does not contain an ID
                    pass

                user_name = entries[1]
                if user_name == person:
                    user_id = entries[2]
                    break

        followedPoolFile.close()

    except BaseException as exc:
        logger.exception(
            "Failed to load the user ID of '{}'!\n{}".format(person,
                                                             str(exc).encode(
                                                                 "utf-8")))

    return user_id


def check_authorization(browser, base_url, username,
                        userid, method, logger, logfolder, notify=True):
    """ Check if user is NOW logged in """
    if notify is True:
        logger.info("Checking if '{}' is logged in...".format(username))

    # different methods can be added in future
    # if method == "activity counts":

    # navigate to owner's profile page only if it is on an unusual page
    if method == "activity counts":
        current_url = get_current_url(browser)
        logger.info(current_url)
        if (not current_url or base_url not in current_url):
            return False
        if not base_url.endswith('/'):
            base_url = base_url + '/'
        profile_link = base_url + '{}'.format(userid)
        web_address_navigator(browser, profile_link, logger)
        logger.critical("--> '{}' is not logged in!\n".format(username))
        nav = browser.find_elements_by_xpath('//div[@role="navigation"]')
        if len(nav) >= 1:
            # create cookie for username
            pickle.dump(browser.get_cookies(), open(
                '{0}{1}_cookie.pkl'.format(logfolder, username), 'wb'))
            return True
        return False


def get_username(browser, track, logger):
    """ Get the username of a user from the loaded profile page """
    if track == "profile":
        query = "return window._sharedData.entry_data. \
                    ProfilePage[0].graphql.user.username"

    elif track == "post":
        query = "return window._sharedData.entry_data. \
                    PostPage[0].graphql.shortcode_media.owner.username"

    try:
        username = browser.execute_script(query)

    except WebDriverException:
        try:
            browser.execute_script("location.reload()")
            update_activity()

            username = browser.execute_script(query)

        except WebDriverException:
            current_url = get_current_url(browser)
            logger.info("Failed to get the username from '{}' page".format(
                current_url or
                "user" if track == "profile" else "post"))
            username = None

    # in future add XPATH ways of getting username

    return username


def find_user_id(Settings, browser, track, username, logger):
    """  Find the user ID from the loaded page """
    if track in ["dialog", "profile"]:
        query = "return window._sharedData.entry_data.ProfilePage[" \
                "0].graphql.user.id"

    elif track == "post":
        query = "return window._sharedData.entry_data.PostPage[" \
                "0].graphql.shortcode_media.owner.id"
        meta_XP = "//meta[@property='instapp:owner_user_id']"

    failure_message = "Failed to get the user ID of '{}' from {} page!".format(
        username, track)

    try:
        user_id = browser.execute_script(query)

    except WebDriverException:
        try:
            browser.execute_script("location.reload()")
            update_activity()

            user_id = browser.execute_script(query)

        except WebDriverException:
            if track == "post":
                try:
                    user_id = browser.find_element_by_xpath(
                        meta_XP).get_attribute("content")
                    if user_id:
                        user_id = format_number(user_id)

                    else:
                        logger.error(
                            "{}\t~empty string".format(failure_message))
                        user_id = None

                except NoSuchElementException:
                    logger.error(failure_message)
                    user_id = None

            else:
                logger.error(failure_message)
                user_id = None

    return user_id


@contextmanager
def new_tab(browser):
    """ USE once a host tab must remain untouched and yet needs extra data-
    get from guest tab """
    try:
        # add a guest tab
        browser.execute_script("window.open()")
        sleep(1)
        # switch to the guest tab
        browser.switch_to.window(browser.window_handles[1])
        sleep(2)
        yield

    finally:
        # close the guest tab
        browser.execute_script("window.close()")
        sleep(1)
        # return to the host tab
        browser.switch_to.window(browser.window_handles[0])
        sleep(2)


def explicit_wait(browser, track, ec_params, logger, timeout=35, notify=True):
    """
    Explicitly wait until expected condition validates

    :param browser: webdriver instance
    :param track: short name of the expected condition
    :param ec_params: expected condition specific parameters - [param1, param2]
    :param logger: the logger instance
    """
    # list of available tracks:
    # <https://seleniumhq.github.io/selenium/docs/api/py/webdriver_support/
    # selenium.webdriver.support.expected_conditions.html>

    if not isinstance(ec_params, list):
        ec_params = [ec_params]

    # find condition according to the tracks
    if track == "VOEL":
        elem_address, find_method = ec_params
        ec_name = "visibility of element located"

        find_by = (By.XPATH if find_method == "XPath" else
                   By.CSS_SELECTOR if find_method == "CSS" else
                   By.CLASS_NAME)
        locator = (find_by, elem_address)
        condition = ec.visibility_of_element_located(locator)

    elif track == "TC":
        expect_in_title = ec_params[0]
        ec_name = "title contains '{}' string".format(expect_in_title)

        condition = ec.title_contains(expect_in_title)

    elif track == "PFL":
        ec_name = "page fully loaded"
        condition = (lambda browser: browser.execute_script(
            "return document.readyState")
            in ["complete" or "loaded"])

    elif track == "SO":
        ec_name = "staleness of"
        element = ec_params[0]

        condition = ec.staleness_of(element)

    # generic wait block
    try:
        wait = WebDriverWait(browser, timeout)
        result = wait.until(condition)

    except TimeoutException:
        if notify is True:
            logger.info(
                "Timed out with failure while explicitly waiting until {}!\n"
                .format(ec_name))
        return False

    return result


def get_current_url(browser):
    """ Get URL of the loaded webpage """
    try:
        current_url = browser.execute_script("return window.location.href")

    except WebDriverException:
        try:
            current_url = browser.current_url

        except WebDriverException:
            current_url = None

    return current_url


def get_username_from_id(browser, base_url, user_id, logger):
    """ Convert user ID to username """
    # method using graphql 'Account media' endpoint
    logger.info(
        "Trying to find the username from the given user ID by loading a post")

    query_hash = "42323d64886122307be10013ad2dcc44"  # earlier-
    # "472f257a40c653c64c666ce877d59d2b"
    graphql_query_URL = base_url + "graphql/query/?query_hash" \
        "={}".format(query_hash)
    variables = {"id": str(user_id), "first": 1}
    post_url = u"{}&variables={}".format(graphql_query_URL,
                                         str(json.dumps(variables)))

    web_address_navigator(browser, post_url, logger)
    try:
        pre = browser.find_element_by_tag_name("pre").text
    except NoSuchElementException:
        logger.info(
            "Encountered an error to find `pre` in page, skipping username.")
        return None
    user_data = json.loads(pre)["data"]["user"]

    if user_data:
        user_data = user_data["edge_owner_to_timeline_media"]

        if user_data["edges"]:
            post_code = user_data["edges"][0]["node"]["shortcode"]
            post_page = base_url + "/p/{}".format(post_code)

            web_address_navigator(browser, post_page, logger)
            username = get_username(browser, "post", logger)
            if username:
                return username

        else:
            if user_data["count"] == 0:
                logger.info(
                    "Profile with ID {}: no pics found".format(user_id))

            else:
                logger.info(
                    "Can't load pics of a private profile to find username ("
                    "ID: {})".format(
                        user_id))

    else:
        logger.info(
            "No profile found, the user may have blocked you (ID: {})".format(
                user_id))
        return None

    """  method using private API
    #logger.info("Trying to find the username from the given user ID by a
    quick API call")

    #req = requests.get(u"https://i.facebook.com/api/v1/users/{}/info/"
    #                   .format(user_id))
    #if req:
    #    data = json.loads(req.text)
    #    if data["user"]:
    #        username = data["user"]["username"]
    #        return username
    """

    """ Having a BUG (random log-outs) with the method below, use it only in
    the external sessions
    # method using graphql 'Follow' endpoint
    logger.info("Trying to find the username from the given user ID "
                "by using the GraphQL Follow endpoint")

    user_link_by_id = ("https://web.facebook.com/web/friendships/{}/follow/"
                       .format(user_id))

    web_address_navigator(browser, user_link_by_id)
    username = get_username(browser, "profile", logger)
    """

    return None


def is_page_available(browser, logger, Settings):
    """ Check if the page is available and valid """
    expected_keywords = ["Page Not Found", "Content Unavailable"]
    page_title = get_page_title(browser, logger)

    if any(keyword in page_title for keyword in expected_keywords):
        reload_webpage(browser, Settings)
        page_title = get_page_title(browser, logger)

        if any(keyword in page_title for keyword in expected_keywords):
            if "Page Not Found" in page_title:
                logger.warning(
                    "The page isn't available!\t~the link may be broken, "
                    "or the page may have been removed...")

            elif "Content Unavailable" in page_title:
                logger.warning(
                    "The page isn't available!\t~the user may have blocked "
                    "you...")

            return False

    return True


def reload_webpage(browser, Settings):
    """ Reload the current webpage """
    browser.execute_script("location.reload()")
    update_activity()
    sleep(2)

    return True


def get_page_title(browser, logger):
    """ Get the title of the webpage """
    # wait for the current page fully load to get the correct page's title
    explicit_wait(browser, "PFL", [], logger, 10)

    try:
        page_title = browser.title

    except WebDriverException:
        try:
            page_title = browser.execute_script("return document.title")

        except WebDriverException:
            try:
                page_title = browser.execute_script(
                    "return document.getElementsByTagName('title')[0].text")

            except WebDriverException:
                logger.info("Unable to find the title of the page :(")
                return None

    return page_title


def click_visibly(browser, Settings, element):
    """ Click as the element become visible """
    if element.is_displayed():
        click_element(browser, Settings, element)

    else:
        browser.execute_script("arguments[0].style.visibility = 'visible'; "
                               "arguments[0].style.height = '10px'; "
                               "arguments[0].style.width = '10px'; "
                               "arguments[0].style.opacity = 1",
                               element)
        # update server calls
        update_activity()

        click_element(browser, Settings, element)

    return True


def get_action_delay(action, Settings):
    """ Get the delay time to sleep after doing actions """
    defaults = {"like": 2,
                "comment": 2,
                "follow": 3,
                "unfollow": 10}
    config = Settings.action_delays

    if (not config or
            config["enabled"] is not True or
            config[action] is None or
            type(config[action]) not in [int, float]):
        return defaults[action]

    else:
        custom_delay = config[action]

    # randomize the custom delay in user-defined range
    if (config["randomize"] is True and
            isinstance(config["random_range"], tuple) and
            len(config["random_range"]) == 2 and
            all((type(i) in [type(None), int, float] for i in
                 config["random_range"])) and
            any(not isinstance(i, None) for i in config["random_range"])):
        min_range = config["random_range"][0]
        max_range = config["random_range"][1]

        if not min_range or min_range < 0:
            min_range = 100

        if not max_range or max_range < 0:
            max_range = 100

        if min_range > max_range:
            a = min_range
            min_range = max_range
            max_range = a

        custom_delay = random.uniform(custom_delay * min_range / 100,
                                      custom_delay * max_range / 100)

    if (custom_delay < defaults[action] and
            config["safety_match"] is not False):
        return defaults[action]

    return custom_delay


def deform_emojis(text):
    """ Convert unicode emojis into their text form """
    new_text = ''
    emojiless_text = ''
    data = regex.findall(r'\X', text)
    emojis_in_text = []

    for word in data:
        if any(char in UNICODE_EMOJI for char in word):
            word_emoji = (emoji.demojize(word)
                          .replace(':', '')
                          .replace('_', ' '))
            if word_emoji not in emojis_in_text:  # do not add an emoji if
                # already exists in text
                emojiless_text += ' '
                new_text += " ({}) ".format(word_emoji)
                emojis_in_text.append(word_emoji)
            else:
                emojiless_text += ' '
                new_text += ' '  # add a space [instead of an emoji to be
                # duplicated]

        else:
            new_text += word
            emojiless_text += word

    emojiless_text = remove_extra_spaces(emojiless_text)
    new_text = remove_extra_spaces(new_text)

    return new_text, emojiless_text


def extract_text_from_element(elem):
    """ As an element is valid and contains text, extract it and return """
    if elem and hasattr(elem, 'text') and elem.text:
        text = elem.text
    else:
        text = None

    return text


def truncate_float(number, precision, round=False):
    """ Truncate (shorten) a floating point value at given precision """

    # don't allow a negative precision [by mistake?]
    precision = abs(precision)

    if round:
        # python 2.7+ supported method [recommended]
        short_float = round(number, precision)

        # python 2.6+ supported method
        """short_float = float("{0:.{1}f}".format(number, precision))
        """

    else:
        operate_on = 1  # returns the absolute number (e.g. 11.0 from 11.456)

        for i in range(precision):
            operate_on *= 10

        short_float = float(int(number * operate_on)) / operate_on

    return short_float


def get_time_until_next_month():
    """ Get total seconds remaining until the next month """
    now = datetime.datetime.now()
    next_month = now.month + 1 if now.month < 12 else 1
    year = now.year if now.month < 12 else now.year + 1
    date_of_next_month = datetime.datetime(year, next_month, 1)

    remaining_seconds = (date_of_next_month - now).total_seconds()

    return remaining_seconds


def remove_extra_spaces(text):
    """ Find and remove redundant spaces more than 1 in text """
    new_text = re.sub(
        r" {2,}", ' ', text
    )

    return new_text


def has_any_letters(text):
    """ Check if the text has any letters in it """
    # result = re.search("[A-Za-z]", text)   # works only with english letters
    result = any(c.isalpha() for c in
                 text)  # works with any letters - english or non-english

    return result


def save_account_progress(browser, base_url, username, user_id, logger):
    """
    Check account current progress and update database

    Args:
        :browser: web driver
        :username: Account to be updated
        :logger: library to log actions
    """
    logger.info('Saving account progress...')
    followers, following, friends = get_relationship_counts(
        browser, base_url, username, user_id, logger, Settings)

    # TODO:FIX IT
    # save profile total posts
    # posts = getUserData("graphql.user.edge_owner_to_timeline_media.count",
    #                     browser)
    posts = 0

    try:
        # DB instance
        db, id = get_database(Settings)
        conn = sqlite3.connect(db)
        logger.info(
            'INSERTING Data INTO accountsProgress: {}, {}, {}, {}, {}'.format(
                id, followers, following, friends, posts))
        with conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            sql = ("INSERT INTO accountsProgress (profile_id, followers, "
                   "following, friendeds, total_posts, created, modified) "
                   "VALUES (?, ?, ?, ?, ?, strftime('%Y-%m-%d %H:%M:%S'), "
                   "strftime('%Y-%m-%d %H:%M:%S'))")
            cur.execute(sql, (id, followers, following, friends, posts))
            conn.commit()
    except Exception:
        logger.exception('message')


def get_users_from_dialog(base_url, old_data, dialog, logger):
    """
    Prepared to work specially with the dynamic data load in the 'Likes'
    dialog box
    """

    user_blocks = dialog.find_elements_by_tag_name('a')

    loaded_users = []
    for u in user_blocks:
        try:
            last_word = extract_text_from_element(u).split(' ')[-1]
            if last_word not in ['1', 'Close', 'mutual', 'friends', 'Message']:
                loaded_users.append(
                    u.get_attribute('href').replace(
                        base_url, '').split('?')[0])
        except Exception as e:
            logger.info(e)

    new_data = (old_data + loaded_users)
    new_data = remove_duplicates(new_data, True, None)

    return new_data


def progress_tracker(current_value, highest_value, initial_time, logger):
    """ Provide a progress tracker to keep value updated until finishes """
    if (current_value is None or
        highest_value is None or
            highest_value == 0):
        return

    try:
        real_time = time.time()
        progress_percent = int((current_value / highest_value) * 100)
        show_logs = Settings.show_logs

        elapsed_time = real_time - initial_time
        elapsed_formatted = truncate_float(elapsed_time, 2)
        elapsed = ("{} seconds".format(
            elapsed_formatted) if elapsed_formatted < 60 else
            "{} minutes".format(
            truncate_float(elapsed_formatted / 60, 2)))

        eta_time = abs((elapsed_time * 100) / (
            progress_percent if progress_percent != 0 else 1) - elapsed_time)
        eta_formatted = truncate_float(eta_time, 2)
        eta = ("{} seconds".format(eta_formatted) if eta_formatted < 60 else
               "{} minutes".format(truncate_float(eta_formatted / 60, 2)))

        tracker_line = "-----------------------------------"
        filled_index = int(progress_percent / 2.77)
        progress_container = (
            "["
            + tracker_line[:filled_index]
            + "+"
            + tracker_line[filled_index:]
            + "]"
        )
        progress_container = (
            progress_container[:filled_index + 1].replace("-", "=")
            + progress_container[filled_index + 1:]
        )

        total_message = ("\r  {}/{} {}  {}%    "
                         "|> Elapsed: {}    "
                         "|> ETA: {}      "
                         .format(current_value, highest_value,
                                 progress_container, progress_percent,
                                 elapsed, eta))

        if show_logs is True:
            sys.stdout.write(total_message)
            sys.stdout.flush()

    except Exception as exc:
        if not logger:
            logger = Settings.logger

        logger.info("Error occurred with Progress Tracker:\n{}".format(
            str(exc).encode("utf-8")))


def close_dialog_box(browser):
    """ Click on the close button spec. in the 'Likes' dialog box """

    try:
        close = browser.find_element_by_xpath(
            read_xpath("class_selectors", "likes_dialog_close_xpath")
        )
        click_element(browser, Settings, close)

    except NoSuchElementException as exc:
        print('Error closing dialog box:', exc)


def parse_cli_args():
    """ Parse arguments passed by command line interface """

    AP_kwargs = dict(prog="FacebookPy",
                     description="Parse FacebookPy constructor's arguments",
                     epilog="And that's how you'd pass arguments by CLI..",
                     conflict_handler="resolve")
    if python_version() < "3.5":
        parser = CustomizedArgumentParser(**AP_kwargs)
    else:
        AP_kwargs.update(allow_abbrev=False)
        parser = ArgumentParser(**AP_kwargs)

    """ Flags that REQUIRE a value once added
    ```python quickstart.py --username abc```
    """
    parser.add_argument(
        "-u", "--username", help="Username is the login id/login email/login phone no", type=str, metavar="abc")
    parser.add_argument(
        "-ui", "--userid", help="Userid is the string that shows on your facebook homepage url(ONLY APPLICABLE FOR FB)", type=str, metavar="abc")
    parser.add_argument(
        "-p", "--password", help="Password", type=str, metavar="123")
    parser.add_argument(
        "-e", "--email", help="login email", type=str, metavar="abcd@gmail.com")
    parser.add_argument(
        "-pd", "--page-delay", help="Implicit wait", type=int, metavar="25")
    parser.add_argument(
        "-pa", "--proxy-address", help="Proxy address",
        type=str, metavar="192.168.1.1")
    parser.add_argument(
        "-pp", "--proxy-port", help="Proxy port", type=str, metavar="8080")

    """ Auto-booleans: adding these flags ENABLE themselves automatically
    ```python quickstart.py --use-firefox```
    """
    parser.add_argument(
        "-uf", "--use-firefox", help="Use Firefox",
        action="store_true", default=None)
    parser.add_argument(
        "-hb", "--headless-browser", help="Headless browser",
        action="store_true", default=None)
    parser.add_argument(
        "-dil", "--disable-image-load", help="Disable image load",
        action="store_true", default=None)
    parser.add_argument(
        "-bsa", "--bypass-suspicious-attempt",
        help="Bypass suspicious attempt", action="store_true", default=None)
    parser.add_argument(
        "-bwm", "--bypass-with-mobile", help="Bypass with mobile phone",
        action="store_true", default=None)

    """ Style below can convert strings into booleans:
    ```parser.add_argument("--is-debug",
                           default=False,
                           type=lambda x: (str(x).capitalize() == "True"))```

    So that, you can pass bool values explicitly from CLI,
    ```python quickstart.py --is-debug True```

    NOTE: This style is the easiest of it and currently not being used.
    """

    args, args_unknown = parser.parse_known_args()
    """ Once added custom arguments if you use a reserved name of core flags
    and don't parse it, e.g.,
    `-ufa` will misbehave cos it has `-uf` reserved flag in it.

    But if you parse it, it's okay.
    """

    return args


class CustomizedArgumentParser(ArgumentParser):
    """
     Subclass ArgumentParser in order to turn off
    the abbreviation matching on older pythons.

    `allow_abbrev` parameter was added by Python 3.5 to do it.
    Thanks to @paul.j3 - https://bugs.python.org/msg204678 for this solution.
    """

    def _get_option_tuples(self, option_string):
        """
         Default of this method searches through all possible prefixes
        of the option string and all actions in the parser for possible
        interpretations.

        To view the original source of this method, running,
        ```
        import inspect; import argparse; inspect.getsourcefile(argparse)
        ```
        will give the location of the 'argparse.py' file that have this method.
        """
        return []
