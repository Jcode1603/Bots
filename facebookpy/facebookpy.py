"""OS Modules environ method to get the setup vars from the Environment"""
# import built-in & third-party modules
import time
from math import ceil
import random
import traceback
import pprint as pp
# from sys import platform
# from platform import python_version
import os
from dateutil.parser import parse
from selenium.webdriver.common import keys
# import csv
# import json
# import requests
# from selenium import webdriver
# from selenium.webdriver import DesiredCapabilities
from pyvirtualdisplay import Display
import logging
from contextlib import contextmanager
# from copy import deepcopy
import unicodedata
from sys import exit as clean_exit
from tempfile import gettempdir

# import FacebookPy modules
# from socialcommons.clarifai_util import check_image
from .comment_util import comment_image
from .comment_util import verify_commenting
# from .comment_util import get_comments_on_post

from .like_util import check_link
from .like_util import verify_liking
# from .like_util import get_links_for_tag
# from .like_util import get_links_from_feed
# from .like_util import get_tags
# from .like_util import get_links_for_location
from .like_util import like_image
from .like_util import get_links_for_username
# from .like_util import like_comment
from .login_util import login_user
# from .settings import Settings
from .print_log_writer import log_follower_num
from .print_log_writer import log_following_num

from time import sleep
# from socialcommons.time_util import set_sleep_percentage
# from socialcommons.util import get_active_users
from .util import validate_userid
# from socialcommons.util import web_address_navigator
from .util import interruption_handler
from .util import highlight_print
# from socialcommons.util import dump_record_activity
from .util import truncate_float
from .util import save_account_progress
from .util import parse_cli_args
from .unfollow_util  import get_given_user_followers
# from .unfollow_util  import get_given_user_following
# from .unfollow_util  import unfollow
from .unfollow_util  import unfollow_user
from .unfollow_util  import follow_user
from .unfollow_util  import follow_restriction
from .unfollow_util  import dump_follow_restriction
# from .unfollow_util  import set_automated_followed_pool
# from .unfollow_util  import get_follow_requests
from .unfriend_util import friend_user
# from .commenters_util import extract_information
from .commenters_util import users_liked
from .commenters_util import get_post_urls_from_profile
from .messaging_util import open_message
# from .relationship_tools import get_following
# from .relationship_tools import get_followers
# from .relationship_tools import get_unfollowers
# from .relationship_tools import get_nonfollowers
# from .relationship_tools import get_fans
# from .relationship_tools import get_mutual_following
from .database_engine import get_database
# from socialcommons.text_analytics import text_analysis
# from socialcommons.text_analytics import yandex_supported_languages
from .browser import set_selenium_local_session
from .browser import close_browser
from .file_manager import get_workspace
from .file_manager import get_logfolder

# import exceptions
from selenium.common.exceptions import NoSuchElementException
from .exceptions import SocialPyError
from .settings import Settings
from selenium import common
from selenium.webdriver.common.action_chains import ActionChains


class FacebookPy:
    """Class to be instantiated to use the script"""
    def __init__(self,
                 username=None,
                 userid=None,
                 password=None,
                 nogui=False,
                 selenium_local_session=True,
                 use_firefox=False,
                 browser_profile_path=None,
                 page_delay=25,
                 show_logs=True,
                 headless_browser=False,
                 proxy_address=None,
                 proxy_chrome_extension=None,
                 proxy_port=None,
                 disable_image_load=False,
                 bypass_suspicious_attempt=False,
                 bypass_with_mobile=False,
                 multi_logs=True):

        cli_args = parse_cli_args()
        username = cli_args.username or username
        userid = cli_args.userid or userid
        password = cli_args.password or password
        use_firefox = cli_args.use_firefox or use_firefox
        page_delay = cli_args.page_delay or page_delay
        headless_browser = cli_args.headless_browser or headless_browser
        proxy_address = cli_args.proxy_address or proxy_address
        proxy_port = cli_args.proxy_port or proxy_port
        disable_image_load = cli_args.disable_image_load or disable_image_load
        bypass_suspicious_attempt = (
            cli_args.bypass_suspicious_attempt or bypass_suspicious_attempt)
        bypass_with_mobile = cli_args.bypass_with_mobile or bypass_with_mobile

        # IS_RUNNING = True
        # workspace must be ready before anything
        if not get_workspace(Settings):
            raise SocialPyError(
                "Oh no! I don't have a workspace to work at :'(")

        self.nogui = nogui
        if nogui:
            self.display = Display(visible=0, size=(800, 600))
            self.display.start()

        self.browser = None
        self.headless_browser = headless_browser
        self.proxy_address = proxy_address
        self.proxy_port = proxy_port
        self.proxy_chrome_extension = proxy_chrome_extension
        self.selenium_local_session = selenium_local_session
        self.bypass_suspicious_attempt = bypass_suspicious_attempt
        self.bypass_with_mobile = bypass_with_mobile
        self.disable_image_load = disable_image_load

        self.username = username or os.environ.get('FACEBOOK_USER')
        self.password = password or os.environ.get('FACEBOOK_PW')

        self.userid = userid
        if not self.userid:
            self.userid = self.username.split('@')[0]

        Settings.profile["name"] = self.username

        self.page_delay = page_delay
        self.switch_language = True
        self.use_firefox = use_firefox
        Settings.use_firefox = self.use_firefox
        self.browser_profile_path = browser_profile_path

        self.do_comment = False
        self.comment_percentage = 0
        self.comments = ['Cool!', 'Nice!', 'Looks good!']
        self.photo_comments = []
        self.video_comments = []

        # self.do_reply_to_comments = False
        # self.reply_to_comments_percent = 0
        # self.comment_replies = []
        # self.photo_comment_replies = []
        # self.video_comment_replies = []

        self.liked_img = 0
        self.already_liked = 0
        self.liked_comments = 0
        self.commented = 0
        self.replied_to_comments = 0
        self.followed = 0
        self.already_followed = 0
        self.unfollowed = 0
        self.followed_by = 0
        self.following_num = 0
        self.inap_img = 0
        self.not_valid_users = 0
        self.video_played = 0
        self.already_Visited = 0

        self.follow_times = 1
        self.do_follow = False
        self.follow_percentage = 0
        self.dont_include = set()
        self.white_list = set()
        self.blacklist = {'enabled': 'True', 'campaign': ''}
        self.automatedFollowedPool = {"all": [], "eligible": []}
        self.do_like = False
        self.like_percentage = 0
        self.smart_hashtags = []

        self.dont_like = ['sex', 'nsfw']
        self.mandatory_words = []
        self.ignore_if_contains = []
        self.ignore_users = []

        self.user_interact_amount = 0
        self.user_interact_media = None
        self.user_interact_percentage = 0
        self.user_interact_random = False
        self.dont_follow_inap_post = True

        # self.use_clarifai = False
        # self.clarifai_api_key = None
        # self.clarifai_models = []
        # self.clarifai_workflow = []
        # self.clarifai_probability = 0.50
        # self.clarifai_img_tags = []
        # self.clarifai_img_tags_skip = []
        # self.clarifai_full_match = False
        # self.clarifai_check_video = False
        # self.clarifai_proxy = None

        self.potency_ratio = None   # 1.3466
        self.delimit_by_numbers = None

        self.max_followers = None   # 90000
        self.max_following = None   # 66834
        self.min_followers = None   # 35
        self.min_following = None   # 27

        self.delimit_liking = False
        self.liking_approved = True
        self.max_likes = 1000
        self.min_likes = 0

        self.delimit_commenting = False
        self.commenting_approved = True
        self.max_comments = 35
        self.min_comments = 0
        self.comments_mandatory_words = []
        self.max_posts = None
        self.min_posts = None
        self.skip_business_categories = []
        self.dont_skip_business_categories = []
        self.skip_business = False
        self.skip_no_profile_pic = False
        self.skip_private = True
        self.skip_business_percentage = 100
        self.skip_no_profile_pic_percentage = 100
        self.skip_private_percentage = 100

        self.relationship_data = {
            username: {"all_following": [], "all_followers": []}}

        self.simulation = {"enabled": True, "percentage": 100}

        self.mandatory_language = False
        self.mandatory_character = []
        self.check_letters = {}

        # use this variable to terminate the nested loops after quotient
        # reaches
        self.quotient_breach = False
        # hold the consecutive jumps and set max of it used with QS to break
        # loops
        self.jumps = {"consequent": {"likes": 0, "comments": 0, "follows": 0,
                                     "unfollows": 0},
                      "limit": {"likes": 7, "comments": 3, "follows": 5,
                                "unfollows": 4}}

        # stores the features' name which are being used by other features
        self.internal_usage = {}

        if (
                self.proxy_address and self.proxy_port > 0) or \
                self.proxy_chrome_extension:
            Settings.connection_type = "proxy"

        self.aborting = False
        self.start_time = time.time()

        # assign logger
        self.show_logs = show_logs
        Settings.show_logs = show_logs or None
        self.multi_logs = multi_logs
        self.logfolder = get_logfolder(self.username, self.multi_logs, Settings)
        self.logger = self.get_facebookpy_logger(self.show_logs)

        get_database(Settings, make=True)  # IMPORTANT: think twice before relocating

        if self.selenium_local_session is True:
            self.set_selenium_local_session(Settings)

    def get_facebookpy_logger(self, show_logs):
        """
        Handles the creation and retrieval of loggers to avoid
        re-instantiation.
        """

        existing_logger = Settings.loggers.get(self.username)
        if existing_logger is not None:
            return existing_logger
        else:
            # initialize and setup logging system for the FacebookPy object
            logger = logging.getLogger(self.username)
            logger.setLevel(logging.DEBUG)
            file_handler = logging.FileHandler(
                '{}general.log'.format(self.logfolder))
            file_handler.setLevel(logging.DEBUG)
            extra = {"username": self.username}
            logger_formatter = logging.Formatter(
                '%(levelname)s [%(asctime)s] [%(username)s]  %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S')
            file_handler.setFormatter(logger_formatter)
            logger.addHandler(file_handler)

            if show_logs is True:
                console_handler = logging.StreamHandler()
                console_handler.setLevel(logging.DEBUG)
                console_handler.setFormatter(logger_formatter)
                logger.addHandler(console_handler)

            logger = logging.LoggerAdapter(logger, extra)

            Settings.loggers[self.username] = logger
            Settings.logger = logger
            return logger

    def set_selenium_local_session(self, Settings):
        self.browser, err_msg = \
            set_selenium_local_session(self.proxy_address,
                                       self.proxy_port,
                                       self.proxy_chrome_extension,
                                       self.headless_browser,
                                       self.use_firefox,
                                       self.browser_profile_path,
                                       # Replaces
                                       # browser User
                                       # Agent from
                                       # "HeadlessChrome".
                                       self.disable_image_load,
                                       self.page_delay,
                                       self.logger,
                                       Settings)
        if len(err_msg) > 0:
            raise SocialPyError(err_msg)

    # def set_selenium_remote_session(self, selenium_url='',
    #                                 selenium_driver=None):
    #     """
    #     Starts remote session for a selenium server.
    #     Creates a new selenium driver instance for remote session or uses
    #     provided
    #     one. Useful for docker setup.

    #     :param selenium_url: string
    #     :param selenium_driver: selenium WebDriver
    #     :return: self
    #     """
    #     if self.aborting:
    #         return self

    #     if selenium_driver:
    #         self.browser = selenium_driver
    #     else:
    #         if self.use_firefox:
    #             self.browser = webdriver.Remote(
    #                 command_executor=selenium_url,
    #                 desired_capabilities=DesiredCapabilities.FIREFOX)
    #         else:
    #             self.browser = webdriver.Remote(
    #                 command_executor=selenium_url,
    #                 desired_capabilities=DesiredCapabilities.CHROME)

    #     message = "Session started!"
    #     highlight_print(Settings, self.username, message, "initialization", "info",
    #                     self.logger)
    #     print('')

    #     return self

    def login(self):
        """Used to login the user either with the username and password"""
        if not login_user(self.browser,
                          self.username,
                          self.userid,
                          self.password,
                          self.logger,
                          self.logfolder,
                          self.switch_language,
                          self.bypass_suspicious_attempt,
                          self.bypass_with_mobile):
            message = "Wrong login data!"
            highlight_print(Settings, self.username,
                            message,
                            "login",
                            "critical",
                            self.logger)

            self.aborting = True

        else:
            message = "Logged in successfully!"
            highlight_print(Settings, self.username,
                            message,
                            "login",
                            "info",
                            self.logger)
            # try to save account progress
            try:
                save_account_progress(self.browser,
                                    "https://web.facebook.com/",
                                    self.username,
                                    self.userid,
                                    self.logger)
            except Exception:
                self.logger.warning(
                    'Unable to save account progress, skipping data update')

        self.following_num = log_following_num(self.browser,
                                            Settings,
                                            "https://web.facebook.com/",
                                            self.username,
                                            self.userid,
                                            self.logger,
                                            self.logfolder)

        return self

    # def set_sleep_reduce(self, percentage):
    #     set_sleep_percentage(percentage)
    #     return self

    # def set_action_delays(self,
    #                       enabled=False,
    #                       like=None,
    #                       comment=None,
    #                       follow=None,
    #                       unfollow=None,
    #                       randomize=False,
    #                       random_range=(None, None),
    #                       safety_match=True):
    #     """ Set custom sleep delay after actions """
    #     Settings.action_delays.update({"enabled": enabled,
    #                                    "like": like,
    #                                    "comment": comment,
    #                                    "follow": follow,
    #                                    "unfollow": unfollow,
    #                                    "randomize": randomize,
    #                                    "random_range": random_range,
    #                                    "safety_match": safety_match})

    # def set_do_comment(self, enabled=False, percentage=0):
    #     """
    #      Defines if images should be commented or not.
    #     E.g. percentage=25 means every ~4th picture will be commented.
    #     """

    #     if self.aborting:
    #         return self

    #     self.do_comment = enabled
    #     self.comment_percentage = percentage

    #     return self

    # def set_comments(self, comments=None, media=None):
    #     """Changes the possible comments"""
    #     if self.aborting:
    #         return self

    #     if (media not in [None, 'Photo', 'Video']):
    #         self.logger.warning('Unkown media type! Treating as "any".')
    #         media = None

    #     self.comments = comments or []

    #     if media is None:
    #         self.comments = comments
    #     else:
    #         attr = '{}_comments'.format(media.lower())
    #         setattr(self, attr, comments)

    #     return self


    def set_do_follow(self, enabled=False, percentage=0, times=1):
        """Defines if the user of the liked image should be followed"""
        if self.aborting:
            return self

        self.follow_times = times
        self.do_follow = enabled
        self.follow_percentage = percentage

        return self

    # def set_do_like(self, enabled=False, percentage=0):
    #     if self.aborting:
    #         return self

    #     self.do_like = enabled
    #     self.like_percentage = min(percentage, 100)

    #     return self

    # def set_dont_like(self, tags=None):
    #     """Changes the possible restriction tags, if one of this
    #      words is in the description, the image won't be liked but user
    #      still might be unfollowed"""
    #     if self.aborting:
    #         return self

    #     if not isinstance(tags, list):
    #         self.logger.warning('Unable to use your set_dont_like '
    #                             'configuration!')
    #         self.aborting = True

    #     self.dont_like = tags or []

    #     return self

    # def set_mandatory_words(self, tags=None):
    #     """Changes the possible restriction tags, if all of this
    #      hashtags is in the description, the image will be liked"""
    #     if self.aborting:
    #         return self

    #     if not isinstance(tags, list):
    #         self.logger.warning('Unable to use your set_mandatory_words '
    #                             'configuration!')
    #         self.aborting = True

    #     self.mandatory_words = tags or []

    #     return self


    def set_user_interact(self, amount=10, percentage=100, randomize=False, media=None):
        """Define if posts of given user should be interacted"""
        if self.aborting:
            return self

        self.user_interact_amount = amount
        self.user_interact_random = randomize
        self.user_interact_percentage = percentage
        self.user_interact_media = media

        return self

    # def set_ignore_users(self, users=None):
    #     """Changes the possible restriction to users, if a user who posts
    #     is one of these, the image won't be liked"""
    #     if self.aborting:
    #         return self

    #     self.ignore_users = users or []

    #     return self

    # def set_ignore_if_contains(self, words=None):
    #     """Ignores the don't likes if the description contains
    #     one of the given words"""
    #     if self.aborting:
    #         return self

    #     self.ignore_if_contains = words or []

    #     return self


    def set_dont_include(self, friends=None):
        """Defines which accounts should not be unfollowed"""
        if self.aborting:
            return self

        self.dont_include = set(friends) or set()
        self.white_list = set(friends) or set()

        return self

    # def set_switch_language(self, option=True):
    #     self.switch_language = option
    #     return self

    # def set_use_clarifai(self,
    #                      enabled=False,
    #                      api_key=None,
    #                      models=None,
    #                      workflow=None,
    #                      probability=0.50,
    #                      full_match=False,
    #                      check_video=False,
    #                      proxy=None):
    #     """
    #     Defines if the clarifai img api should be used
    #     Which 'project' will be used (only 5000 calls per month)

    #     Raises:
    #         SocialPyError if os is windows
    #     """
    #     if self.aborting:
    #         return self

    #     # if os.name == 'nt':
    #     #    raise SocialPyError('Clarifai is not supported on Windows')

    #     self.use_clarifai = enabled

    #     if api_key is None and self.clarifai_api_key is None:
    #         self.clarifai_api_key = os.environ.get('CLARIFAI_API_KEY')
    #     elif api_key is not None:
    #         self.clarifai_api_key = api_key

    #     self.clarifai_models = models or ['general']
    #     self.clarifai_workflow = workflow or []
    #     self.clarifai_probability = probability
    #     self.clarifai_full_match = full_match
    #     self.clarifai_check_video = check_video

    #     if proxy is not None:
    #         self.clarifai_proxy = 'https://' + proxy

    #     return self

    # def set_smart_hashtags(self,
    #                        tags=None,
    #                        limit=3,
    #                        sort='top',
    #                        log_tags=True):
    #     """Generate smart hashtags based on https://displaypurposes.com/"""
    #     """ranking, banned and spammy tags are filtered out."""

    #     if tags is None:
    #         print('set_smart_hashtags is misconfigured')
    #         return

    #     for tag in tags:
    #         req = requests.get(
    #             u'https://d212rkvo8t62el.cloudfront.net/tag/{}'.format(tag))
    #         data = json.loads(req.text)

    #         if data['tagExists'] is True:
    #             if sort == 'top':
    #                 # sort by ranking
    #                 ordered_tags_by_rank = sorted(
    #                     data['results'], key=lambda d: d['rank'], reverse=True)
    #                 ranked_tags = (ordered_tags_by_rank[:limit])
    #                 for item in ranked_tags:
    #                     # add smart hashtag to like list
    #                     self.smart_hashtags.append(item['tag'])

    #             elif sort == 'random':
    #                 random_tags = random.sample(data['results'], limit)
    #                 for item in random_tags:
    #                     self.smart_hashtags.append(item['tag'])

    #             if log_tags is True:
    #                 for item in self.smart_hashtags:
    #                     print(u'[smart hashtag generated: {}]'.format(item))
    #         else:
    #             print(u'Too few results for #{} tag'.format(tag))

    #     # delete duplicated tags
    #     self.smart_hashtags = list(set(self.smart_hashtags))
    #     return self

    # def set_mandatory_language(self, enabled=False, character_set='LATIN'):
    #     """Restrict the description of the image to a character set"""
    #     if self.aborting:
    #         return self

    #     if (character_set not in ['LATIN', 'GREEK', 'CYRILLIC', 'ARABIC',
    #                               'HEBREW', 'CJK', 'HANGUL', 'HIRAGANA',
    #                               'KATAKANA', 'THAI']):
    #         self.logger.warning('Unkown character set! Treating as "LATIN".')
    #         character_set = 'LATIN'

    #     self.mandatory_language = enabled
    #     self.mandatory_character = character_set

    #     return self

    # def clarifai_check_img_for(self, tags=None, tags_skip=None, comment=False,
    #                            comments=None):
    #     """Defines the tags the images should be checked for"""
    #     if self.aborting:
    #         return self

    #     if tags is None and not self.clarifai_img_tags:
    #         self.use_clarifai = False
    #     elif tags:
    #         self.clarifai_img_tags.append((tags, comment, comments))
    #         self.clarifai_img_tags_skip = tags_skip or []

    #     return self

    # def query_clarifai(self):
    #     """Method for querying Clarifai using parameters set in
    #     clarifai_check_img_for"""
    #     return check_image(self.browser, self.clarifai_api_key,
    #                        self.clarifai_img_tags,
    #                        self.clarifai_img_tags_skip, self.logger,
    #                        self.clarifai_models,
    #                        self.clarifai_workflow, self.clarifai_probability,
    #                        self.clarifai_full_match, self.clarifai_check_video,
    #                        proxy=self.clarifai_proxy)

    # def follow_commenters(self, usernames, amount=10, daysold=365, max_pic=50,
    #                       sleep_delay=600, interact=False):
    #     """ Follows users' commenters """

    #     if self.aborting:
    #         return self

    #     message = "Starting to follow commenters.."
    #     highlight_print(Settings, self.username, message, "feature", "info", self.logger)

    #     if not isinstance(usernames, list):
    #         usernames = [usernames]

    #     followed_all = 0
    #     followed_new = 0

    #     # hold the current global values for differentiating at the end
    #     already_followed_init = self.already_followed
    #     not_valid_users_init = self.not_valid_users
    #     liked_init = self.liked_img
    #     already_liked_init = self.already_liked
    #     commented_init = self.commented
    #     inap_img_init = self.inap_img

    #     relax_point = random.randint(7,
    #                                  14)  # you can use some plain value
    #     # `10` instead of this quitely randomized score
    #     self.quotient_breach = False

    #     for username in usernames:
    #         if self.quotient_breach:
    #             break

    #         self.logger.info(
    #             "Following commenters of '{}' from {} pictures in last {} "
    #             "days...\nScrapping wall..".format(
    #                 username,
    #                 max_pic,
    #                 daysold))
    #         commenters = extract_information(self.browser, username, daysold,
    #                                          max_pic)

    #         if len(commenters) > 0:
    #             self.logger.info(
    #                 "Going to follow top {} users.\n".format(amount))
    #             sleep(1)
    #             # This way of iterating will prevent sleep interference
    #             # between functions
    #             random.shuffle(commenters)
    #             for commenter in commenters[:amount]:
    #                 if self.quotient_breach:
    #                     self.logger.warning(
    #                         "--> Follow quotient reached its peak!"
    #                         "\t~leaving Follow-Commenters activity\n")
    #                     break

    #                 with self.feature_in_feature("follow_by_list", True):
    #                     followed = self.follow_by_list(commenter,
    #                                                    self.follow_times,
    #                                                    sleep_delay,
    #                                                    interact)
    #                 if followed > 0:
    #                     followed_all += 1
    #                     followed_new += 1
    #                     self.logger.info(
    #                         "Total Follow: {}\n".format(str(followed_all)))
    #                     # Take a break after a good following
    #                     if followed_new >= relax_point:
    #                         delay_random = random.randint(
    #                             ceil(sleep_delay * 0.85),
    #                             ceil(sleep_delay * 1.14))
    #                         sleep_time = ("{} seconds".format(delay_random) if
    #                                       delay_random < 60 else
    #                                       "{} minutes".format(truncate_float(
    #                                           delay_random / 60, 2)))
    #                         self.logger.info(
    #                             "------=>  Followed {} new users ~sleeping "
    #                             "about {}"
    #                             .format(followed_new, sleep_time))
    #                         sleep(delay_random)
    #                         relax_point = random.randint(7, 14)
    #                         followed_new = 0
    #                         pass

    #         else:
    #             self.logger.info("Noone commented, noone to follow.\n")

    #         sleep(1)

    #     self.logger.info("Finished following Commenters!\n")

    #     # find the feature-wide action sizes by taking a difference
    #     already_followed = (self.already_followed - already_followed_init)
    #     not_valid_users = (self.not_valid_users - not_valid_users_init)
    #     liked = (self.liked_img - liked_init)
    #     already_liked = (self.already_liked - already_liked_init)
    #     commented = (self.commented - commented_init)
    #     inap_img = (self.inap_img - inap_img_init)

    #     # print results
    #     self.logger.info("Followed: {}".format(followed_all))
    #     self.logger.info("Already followed: {}".format(already_followed))
    #     self.logger.info("Not valid users: {}".format(not_valid_users))

    #     if interact is True:
    #         print('')
    #         # print results out of interactions
    #         self.logger.info("Liked: {}".format(liked))
    #         self.logger.info("Already Liked: {}".format(already_liked))
    #         self.logger.info("Commented: {}".format(commented))
    #         self.logger.info("Inappropriate: {}".format(inap_img))

    #     return self


    def fetch_birthdays(self):
        self.browser.get("https://web.facebook.com/{}/friends".format(self.userid))
        time.sleep(2)
        try:
            for i in range(10):
                # self.browser.execute_script("window.scrollTo(0, " + str(1000+i*1000) + ")")
                self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)

            profile_as = self.browser.find_elements_by_css_selector("li > div > div > div.uiProfileBlockContent > div > div:nth-child(2) > div > a")

            print("Found", len(profile_as), "profiles")
            profiles = []
            for profile_a in profile_as:
                friend_url = profile_a.get_attribute('href').split('?')[0].split('#')[0]
                if len(friend_url.split('/')) > 4:
                    continue
                profiles.append(friend_url)

            # pp.pprint(profiles)
            for profile in profiles:
                # self.browser.get(profile+'/about?section=year-overviews')
                # life_events = self.browser.find_elements_by_css_selector("div > ul > li > div > div > ul > li > div > div > a > span")
                # if len(life_events) > 0:
                #     # print(profile, life_events[-1].text)
                #     try:
                #         if 'Born on' in life_events[-1].text:
                #             dob = life_events[-1].text.split('Born on ')[1]
                #             print(profile, dob)
                #             continue
                #     except Exception as e:
                #         pass

                self.browser.get(profile+'/about')
                overview_events = self.browser.find_elements_by_css_selector("div > ul > li > div > div > span > div:nth-child(2)")
                for overview_event in overview_events:
                    # print(profile, overview_event.text)
                    try:
                        from dateutil.parser import parse
                        dob = parse(overview_event.text)
                        print(profile, dob)
                        continue
                    except Exception as e:
                        pass

        except Exception as e:
                traceback.print_exc()



    def follow_likers(self, userids, photos_grab_amount=3,
                      follow_likers_per_photo=3, randomize=True,
                      sleep_delay=600,
                      interact=False):
        """ Follows users' likers """
        if self.aborting:
            return self

        message = "Starting to follow likers.."
        highlight_print(Settings, self.username, message, "feature", "info", self.logger)

        if not isinstance(userids, list):
            userids = [userids]

        if photos_grab_amount > 12:
            self.logger.info(
                "Sorry, you can only grab likers from first 12 photos for "
                "given username now.\n")
            photos_grab_amount = 12

        followed_all = 0
        followed_new = 0

        # hold the current global values for differentiating at the end
        already_followed_init = self.already_followed
        not_valid_users_init = self.not_valid_users
        liked_init = self.liked_img
        already_liked_init = self.already_liked
        commented_init = self.commented
        inap_img_init = self.inap_img

        relax_point = random.randint(7,
                                     14)  # you can use some plain value
        # `10` instead of this quitely randomized score
        self.quotient_breach = False

        for userid in userids:
            if self.quotient_breach:
                break

            post_urls = get_post_urls_from_profile(self.browser, userid,
                                                   photos_grab_amount,
                                                   randomize)
            sleep(1)
            if not isinstance(post_urls, list):
                post_urls = [post_urls]

            # self.logger.info('post_urls:')
            # self.logger.info(post_urls)

            for post_url in post_urls:
                if self.quotient_breach:
                    break

                likers = users_liked(self.browser, post_url, self.logger,
                                     follow_likers_per_photo)
                # This way of iterating will prevent sleep interference
                # between functions
                random.shuffle(likers)

                for liker in likers[:follow_likers_per_photo]:
                    if self.quotient_breach:
                        self.logger.warning(
                            "--> Follow quotient reached its peak!"
                            "\t~leaving Follow-Likers activity\n")
                        break

                    with self.feature_in_feature("follow_by_list", True):
                        followed = self.follow_by_list(liker,
                                                       self.follow_times,
                                                       sleep_delay,
                                                       interact)
                    if followed > 0:
                        followed_all += 1
                        followed_new += 1
                        self.logger.info(
                            "Total Follow: {}\n".format(str(followed_all)))
                        # Take a break after a good following
                        if followed_new >= relax_point:
                            delay_random = random.randint(
                                ceil(sleep_delay * 0.85),
                                ceil(sleep_delay * 1.14))
                            sleep_time = ("{} seconds".format(delay_random) if
                                          delay_random < 60 else
                                          "{} minutes".format(truncate_float(
                                              delay_random / 60, 2)))
                            self.logger.info(
                                "------=>  Followed {} new users ~sleeping "
                                "about {}"
                                .format(followed_new, sleep_time))
                            sleep(delay_random)
                            relax_point = random.randint(7, 14)
                            followed_new = 0
                            pass

        self.logger.info("Finished following Likers!\n")

        # find the feature-wide action sizes by taking a difference
        already_followed = (self.already_followed - already_followed_init)
        not_valid_users = (self.not_valid_users - not_valid_users_init)
        liked = (self.liked_img - liked_init)
        already_liked = (self.already_liked - already_liked_init)
        commented = (self.commented - commented_init)
        inap_img = (self.inap_img - inap_img_init)

        # print results
        self.logger.info("Followed: {}".format(followed_all))
        self.logger.info("Already followed: {}".format(already_followed))
        self.logger.info("Not valid users: {}".format(not_valid_users))

        if interact is True:
            print('')
            # print results out of interactions
            self.logger.info("Liked: {}".format(liked))
            self.logger.info("Already Liked: {}".format(already_liked))
            self.logger.info("Commented: {}".format(commented))
            self.logger.info("Inappropriate: {}".format(inap_img))

        return self
    
    def search(self, query=''):

        bot = self.browser
        bot.get('https://web.facebook.com/groups/feed/')
        time.sleep(5)

        try:
            searchbox = bot.find_element_by_xpath("//input[@placeholder='Search groups'][@type='search']")
        except common.exceptions.NoSuchElementException:
            time.sleep(2)
            searchbox = bot.find_element_by_xpath("//div[contains(@class, 'oajrlxb2 rq0escxv f1sip0of hidtqoto e70eycc3 lzcic4wl hzawbc8m ijkhr0an aaoq3grb sgqwj88q b3i9ofy5 oo9gr5id b1f16np4 hdh3q7d8 dwo3fsh8 qu0x051f esr5mh6w e9989ue4 r7d6kgcz br7hx15l h2jyy9rg n3ddgdk9 owxd89k7 ihxqhq3m jq4qci2q k4urcfbm iu8raji3 tv7at329 l60d2q6s d1544ag0 hwnh5xvq fjf4s8hc aj8hi1zk r4fl40cc kd8v7px7 m07ooulj mzan44vs')]")

        searchbox.clear()
        searchbox.send_keys(query)
        searchbox.send_keys(keys.Keys.RETURN)
        time.sleep(5)
        """latest_button = bot.find_element_by_xpath("//span[text()='Latest']")
        time.sleep(2)
        latest_button.click()"""
        time.sleep(1)

    def like_comment(self, keyword, comment):
 
        """
        This function automatically retrieves
        the tweets and then likes and retweets them
 
        Arguments:
            hashtag {string} -- twitter hashtag
        """
 
        bot = self.browser
 
        # fetches the latest tweets with the provided hashtag
        self.search(query=keyword)
        """bot.get(
            'https://twitter.com / search?q =% 23' + \
            hashtag+'&src = typed_query&f = live'
        )"""
 
        time.sleep(3)
 
        # using set so that only unique links
        # are present and to avoid unnecessary repetition
        links = set()
 
        # obtaining the links of the tweets
        for i in range(7):
            # executing javascript code
            # to scroll the webpage
            bot.execute_script(
                'window.scrollTo(0, document.body.scrollHeight)'
            )
 
            time.sleep(5)
 
            # using list comprehension
            # for adding all the tweets link to the set
            # this particular piece of code might
            # look very complicated but the only reason
            # I opted for list comprehension because is
            # lot faster than traditional loops
            [
                links.add(elem.get_attribute('href'))\
                for elem in bot.find_elements_by_xpath("//a[@role='link'][contains(@href, 'post')]")
            ]
        print(links)
 
        # traversing through the generated links
        for link in links:
            # opens individual links
            time.sleep(7)
            if '/posts/' in link:
                print(link)
                bot.get(link)
            
 
                try:
                    time.sleep(5)
                    try:
                        comment_button = bot.find_element_by_xpath(
                            "//div[@aria-label='Leave a comment']"
                        )
                        time.sleep(1)
                        bot.execute_script('arguments[0].scrollIntoView();', comment_button)
                        time.sleep(2)
                        comment_button.click()
                        time.sleep(2)
                        print("button 1 works")
                    except:
                        try:
                            print("button 1 didn't work")
                            time.sleep(1)
                            comment_button=bot.find_element_by_xpath("//div[@aria-label='Write a comment']")
                            time.sleep(1)
                            bot.execute_script('arguments[0].scrollIntoView();', comment_button)
                            time.sleep(2)
                            comment_button.click()
                            time.sleep(2)              
                        except common.exceptions.NoSuchElementException:
                            print("didnt find text area 1")
                            try:
                                time.sleep(2)
                                comment_button=bot.find_element_by_xpath("//p[contains(@class, 'hcukyx3x oygrvhab cxmmr5t8 kvgmc6g5')]")
                                time.sleep(1)
                                bot.execute_script('arguments[0].scrollIntoView();', comment_button)
                                time.sleep(2)
                                comment_button.click()
                                time.sleep(2)  
                            except common.exceptions.NoSuchElementException:
                                pass
                    
                    time.sleep(3)

                    (ActionChains(bot).send_keys(comment)
                    .perform())
                    time.sleep(5)
                    (ActionChains(bot)
                    .send_keys(keys.Keys.RETURN).perform())
                    #
                    
                    print('found button')
                    # retweet button selector
                    """bot.find_element_by_css_selector(
                        '.css-18t94o4[data-testid ="retweet"]'
                    ).click()"""
                    time.sleep(3)
                    # initializes action chain
                    actions = ActionChains(bot)
                    # sends RETURN key to retweet without comment
                    #actions.send_keys(keys.Keys.RETURN).perform()
                    time.sleep(4)
                    # adding higher sleep time to avoid
                    # getting detected as bot by twitter
                    time.sleep(10)
                except:
                    print("something went wrong")
                    time.sleep(2)
            else:
                pass
    
        # fetches the main homepage
        bot.get('https://web.facebook.com/')

    def friend_by_list(self, friendlist, times=1, sleep_delay=600,
                       interact=False):
        for acc_to_friend in friendlist:
            friend_state, msg = friend_user(self.browser,
                                            "profile",
                                            self.username,
                                            acc_to_friend,
                                            None,
                                            self.blacklist,
                                            self.logger,
                                            self.logfolder)

    def follow_by_list(self, followlist, times=1, sleep_delay=600,
                       interact=False):
        """Allows to follow by any scrapped list"""
        if not isinstance(followlist, list):
            followlist = [followlist]

        if self.aborting:
            self.logger.info(">>> self aborting prevented")
            # return self

        # standalone means this feature is started by the user
        standalone = True if "follow_by_list" not in \
                             self.internal_usage.keys() else False
        # skip validation in case of it is already accomplished
        users_validated = True if not standalone and not \
            self.internal_usage["follow_by_list"]["validate"] else False

        self.follow_times = times or 0

        followed_all = 0
        followed_new = 0
        already_followed = 0
        not_valid_users = 0

        # hold the current global values for differentiating at the end
        liked_init = self.liked_img
        already_liked_init = self.already_liked
        commented_init = self.commented
        inap_img_init = self.inap_img

        relax_point = random.randint(7,
                                     14)  # you can use some plain value
        # `10` instead of this quitely randomized score
        self.quotient_breach = False

        for acc_to_follow in followlist:
            if self.jumps["consequent"]["follows"] >= self.jumps["limit"][
                    "follows"]:
                self.logger.warning(
                    "--> Follow quotient reached its peak!\t~leaving "
                    "Follow-By-Tags activity\n")
                # reset jump counter before breaking the loop
                self.jumps["consequent"]["follows"] = 0
                # turn on `quotient_breach` to break the internal iterators
                # of the caller
                self.quotient_breach = True if not standalone else False
                break

            if follow_restriction("read", acc_to_follow, self.follow_times,
                                  self.logger):
                print('')
                continue

            # Take a break after a good following
            if followed_new >= relax_point:
                delay_random = random.randint(
                    ceil(sleep_delay * 0.85),
                    ceil(sleep_delay * 1.14))
                sleep_time = ("{} seconds".format(delay_random) if
                              delay_random < 60 else
                              "{} minutes".format(truncate_float(
                                  delay_random / 60, 2)))
                self.logger.info("Followed {} new users  ~sleeping about {}\n"
                                 .format(followed_new, sleep_time))
                sleep(delay_random)
                followed_new = 0
                relax_point = random.randint(7, 14)
                pass

            if not follow_restriction("read", acc_to_follow, self.follow_times,
                                      self.logger):
                follow_state, msg = follow_user(self.browser,
                                                "profile",
                                                self.username,
                                                acc_to_follow,
                                                None,
                                                self.blacklist,
                                                self.logger,
                                                self.logfolder)
                sleep(random.randint(1, 3))

                if follow_state is True:
                    followed_all += 1
                    followed_new += 1
                    # reset jump counter after a successful follow
                    self.jumps["consequent"]["follows"] = 0

                    if standalone:  # print only for external usage (
                        # internal callers have their printers)
                        self.logger.info(
                            "Total Follow: {}\n".format(str(followed_all)))

                    # Check if interaction is expected
                    if interact and self.do_like:
                        do_interact = random.randint(0,
                                                     100) <= \
                            self.user_interact_percentage
                        # Do interactions if any
                        if do_interact and self.user_interact_amount > 0:
                            original_do_follow = self.do_follow  # store the
                            # original value of `self.do_follow`
                            self.do_follow = False  # disable following
                            # temporarily cos the user is already followed
                            # above
                            self.interact_by_users(acc_to_follow,
                                                   self.user_interact_amount,
                                                   self.user_interact_random,
                                                   self.user_interact_media)
                            self.do_follow = original_do_follow  # revert
                            # back original `self.do_follow` value (either
                            # it was `False` or `True`)

                elif msg == "already followed":
                    already_followed += 1

                elif msg == "jumped":
                    # will break the loop after certain consecutive jumps
                    self.jumps["consequent"]["follows"] += 1

                sleep(1)

        if standalone:  # print only for external usage (internal callers
            # have their printers)
            self.logger.info("Finished following by List!\n")
            # print summary
            self.logger.info("Followed: {}".format(followed_all))
            self.logger.info("Already followed: {}".format(already_followed))
            self.logger.info("Not valid users: {}".format(not_valid_users))

            if interact is True:
                print('')
                # find the feature-wide action sizes by taking a difference
                liked = (self.liked_img - liked_init)
                already_liked = (self.already_liked - already_liked_init)
                commented = (self.commented - commented_init)
                inap_img = (self.inap_img - inap_img_init)

                # print the summary out of interactions
                self.logger.info("Liked: {}".format(liked))
                self.logger.info("Already Liked: {}".format(already_liked))
                self.logger.info("Commented: {}".format(commented))
                self.logger.info("Inappropriate: {}".format(inap_img))

        # always sum up general objects regardless of the request size
        self.followed += followed_all
        self.already_followed += already_followed
        self.not_valid_users += not_valid_users

        return followed_all

    def set_relationship_bounds(self,
                                enabled=None,
                                potency_ratio=None,
                                delimit_by_numbers=None,
                                min_posts=None,
                                max_posts=None,
                                max_followers=None,
                                max_following=None,
                                min_followers=None,
                                min_following=None):
        """Sets the potency ratio and limits to the provide an efficient
        activity between the targeted masses"""

        self.potency_ratio = potency_ratio if enabled is True else None
        self.delimit_by_numbers = delimit_by_numbers if enabled is True else \
            None

        self.max_followers = max_followers
        self.min_followers = min_followers

        self.max_following = max_following
        self.min_following = min_following

        self.min_posts = min_posts if enabled is True else None
        self.max_posts = max_posts if enabled is True else None

    def validate_user_call(self, user_name):
        """ Short call of validate_userid() function """
        validation, details = \
            validate_userid(self.browser,
                            "https://web.facebook.com/",
                            user_name,
                            self.username,
                            self.userid,
                            self.ignore_users,
                            self.blacklist,
                            self.potency_ratio,
                            self.delimit_by_numbers,
                            self.max_followers,
                            self.max_following,
                            self.min_followers,
                            self.min_following,
                            self.min_posts,
                            self.max_posts,
                            self.skip_private,
                            self.skip_private_percentage,
                            self.skip_no_profile_pic,
                            self.skip_no_profile_pic_percentage,
                            self.skip_business,
                            self.skip_business_percentage,
                            self.skip_business_categories,
                            self.dont_skip_business_categories,
                            self.logger,
                            self.logfolder, Settings)
        return validation, details

    def fetch_smart_comments(self, is_video, temp_comments):
        if temp_comments:
            # Use clarifai related comments only!
            comments = temp_comments
        elif is_video:
            comments = (self.comments +
                        self.video_comments)
        else:
            comments = (self.comments +
                        self.photo_comments)

        return comments

    # def set_skip_users(self,
    #                    skip_private=True,
    #                    private_percentage=100,
    #                    skip_no_profile_pic=False,
    #                    no_profile_pic_percentage=100,
    #                    skip_business=False,
    #                    business_percentage=100,
    #                    skip_business_categories=[],
    #                    dont_skip_business_categories=[]):

    #     self.skip_business = skip_business
    #     self.skip_private = skip_private
    #     self.skip_no_profile_pic = skip_no_profile_pic
    #     self.skip_business_percentage = business_percentage
    #     self.skip_no_profile_pic_percentage = no_profile_pic_percentage
    #     self.skip_private_percentage = private_percentage
    #     if skip_business:
    #         self.skip_business_categories = skip_business_categories
    #         if len(skip_business_categories) == 0:
    #             self.dont_skip_business_categories = \
    #                 dont_skip_business_categories
    #         else:
    #             if len(dont_skip_business_categories) != 0:
    #                 self.logger.warning(
    #                     "Both skip_business_categories and "
    #                     "dont_skip_business categories provided in "
    #                     "skip_business feature," +
    #                     "will skip only the categories listed in "
    #                     "skip_business_categories parameter")
    #                 # dont_skip_business_categories = [] Setted by default
    #                 # in init

    # def set_delimit_liking(self,
    #                        enabled=None,
    #                        max=None,
    #                        min=None):

    #     self.delimit_liking = True if enabled is True else False
    #     self.max_likes = max
    #     self.min_likes = min

    # def set_delimit_commenting(self,
    #                            enabled=False,
    #                            max=None,
    #                            min=None,
    #                            comments_mandatory_words=[]):

    #     self.delimit_commenting = True if enabled is True else False
    #     self.max_comments = max
    #     self.min_comments = min

    #     # comment only when the image description contain at least one of
    #     # those words
    #     self.comments_mandatory_words = comments_mandatory_words

    # def set_simulation(self, enabled=True, percentage=100):
    #     """ Sets aside simulation parameters """
    #     if enabled not in [True, False]:
    #         self.logger.info(
    #             "Invalid simulation parameter! Please use correct syntax "
    #             "with accepted values.")

    #     elif enabled is False:
    #         self.simulation["enabled"] = False

    #     else:
    #         percentage = 0 if percentage is None else percentage
    #         self.simulation = {"enabled": True, "percentage": percentage}

    # def like_by_locations(self,
    #                       locations=None,
    #                       amount=50,
    #                       media=None,
    #                       skip_top_posts=True):
    #     """Likes (default) 50 images per given locations"""
    #     if self.aborting:
    #         return self

    #     liked_img = 0
    #     already_liked = 0
    #     inap_img = 0
    #     commented = 0
    #     followed = 0
    #     not_valid_users = 0

    #     locations = locations or []
    #     self.quotient_breach = False

    #     for index, location in enumerate(locations):
    #         if self.quotient_breach:
    #             break

    #         self.logger.info('Location [{}/{}]'
    #                          .format(index + 1, len(locations)))
    #         self.logger.info('--> {}'.format(location.encode('utf-8')))

    #         try:
    #             links = get_links_for_location(self.browser,
    #                                            location,
    #                                            amount,
    #                                            self.logger,
    #                                            media,
    #                                            skip_top_posts)
    #         except NoSuchElementException as exc:
    #             self.logger.warning(
    #                 "Error occurred while getting images from location: {}  "
    #                 "~maybe too few images exist\n\t{}\n".format(location, str(
    #                     exc).encode("utf-8")))
    #             continue

    #         for i, link in enumerate(links):
    #             if self.jumps["consequent"]["likes"] >= self.jumps["limit"][
    #                     "likes"]:
    #                 self.logger.warning(
    #                     "--> Like quotient reached its peak!\t~leaving "
    #                     "Like-By-Locations activity\n")
    #                 self.quotient_breach = True
    #                 # reset jump counter after a breach report
    #                 self.jumps["consequent"]["likes"] = 0
    #                 break

    #             self.logger.info('[{}/{}]'.format(i + 1, len(links)))
    #             self.logger.info(link)

    #             try:
    #                 inappropriate, user_name, is_video, reason, scope = (
    #                     check_link(self.browser,
    #                                link,
    #                                self.dont_like,
    #                                self.mandatory_words,
    #                                self.mandatory_language,
    #                                self.is_mandatory_character,
    #                                self.mandatory_character,
    #                                self.check_character_set,
    #                                self.ignore_if_contains,
    #                                self.logger))

    #                 if not inappropriate and self.delimit_liking:
    #                     self.liking_approved = verify_liking(self.browser,
    #                                                          self.max_likes,
    #                                                          self.min_likes,
    #                                                          self.logger)

    #                 if not inappropriate and self.liking_approved:
    #                     # validate user
    #                     validation, details = self.validate_user_call(
    #                         user_name)

    #                     if validation is not True:
    #                         self.logger.info(
    #                             "--> Not a valid user: {}".format(details))
    #                         not_valid_users += 1
    #                         continue
    #                     else:
    #                         web_address_navigator( self.browser, link, Settings)

    #                     # try to like
    #                     like_state, msg = like_image(self.browser,
    #                                                  user_name,
    #                                                  self.blacklist,
    #                                                  self.logger,
    #                                                  self.logfolder,
    #                                                  Settings)

    #                     if like_state is True:
    #                         liked_img += 1
    #                         # reset jump counter after a successful like
    #                         self.jumps["consequent"]["likes"] = 0

    #                         checked_img = True
    #                         temp_comments = []

    #                         commenting = random.randint(
    #                             0, 100) <= self.comment_percentage
    #                         following = random.randint(
    #                             0, 100) <= self.follow_percentage

    #                         if self.use_clarifai and (following or commenting):
    #                             try:
    #                                 checked_img, temp_comments, \
    #                                     clarifai_tags = (
    #                                         self.query_clarifai())

    #                             except Exception as err:
    #                                 self.logger.error(
    #                                     'Image check error: {}'.format(err))

    #                         # comments
    #                         if (self.do_comment and
    #                                 user_name not in self.dont_include and
    #                                 checked_img and
    #                                 commenting):

    #                             if self.delimit_commenting:
    #                                 (self.commenting_approved,
    #                                  disapproval_reason) = verify_commenting(
    #                                     self.browser,
    #                                     self.max_comments,
    #                                     self.min_comments,
    #                                     self.comments_mandatory_words,
    #                                     self.logger)
    #                             if self.commenting_approved:
    #                                 # smart commenting
    #                                 comments = self.fetch_smart_comments(
    #                                     is_video,
    #                                     temp_comments)
    #                                 if comments:
    #                                     comment_state, msg = comment_image(
    #                                         self.browser,
    #                                         user_name,
    #                                         comments,
    #                                         self.blacklist,
    #                                         self.logger,
    #                                         self.logfolder,
    #                                         Settings)
    #                                     if comment_state is True:
    #                                         commented += 1

    #                             else:
    #                                 self.logger.info(disapproval_reason)

    #                         else:
    #                             self.logger.info('--> Not commented')
    #                             sleep(1)

    #                         # following
    #                         if (self.do_follow and
    #                                 user_name not in self.dont_include and
    #                                 checked_img and
    #                                 following and
    #                                 not follow_restriction("read", user_name,
    #                                                        self.follow_times,
    #                                                        self.logger)):

    #                             follow_state, msg = follow_user(self.browser,
    #                                                             "post",
    #                                                             self.username,
    #                                                             user_name,
    #                                                             None,
    #                                                             self.blacklist,
    #                                                             self.logger,
    #                                                             self.logfolder)
    #                             if follow_state is True:
    #                                 followed += 1

    #                         else:
    #                             self.logger.info('--> Not following')
    #                             sleep(1)

    #                     elif msg == "already liked":
    #                         already_liked += 1

    #                     elif msg == "jumped":
    #                         # will break the loop after certain consecutive
    #                         # jumps
    #                         self.jumps["consequent"]["likes"] += 1

    #                 else:
    #                     self.logger.info(
    #                         '--> Image not liked: {}'.format(
    #                             reason.encode('utf-8')))
    #                     inap_img += 1

    #             except NoSuchElementException as err:
    #                 self.logger.error('Invalid Page: {}'.format(err))

    #         self.logger.info('Location: {}'.format(location.encode('utf-8')))
    #         self.logger.info('Liked: {}'.format(liked_img))
    #         self.logger.info('Already Liked: {}'.format(already_liked))
    #         self.logger.info('Commented: {}'.format(commented))
    #         self.logger.info('Followed: {}'.format(followed))
    #         self.logger.info('Inappropriate: {}'.format(inap_img))
    #         self.logger.info('Not valid users: {}\n'.format(not_valid_users))

    #     self.followed += followed
    #     self.liked_img += liked_img
    #     self.already_liked += already_liked
    #     self.commented += commented
    #     self.inap_img += inap_img
    #     self.not_valid_users += not_valid_users

    #     return self

    # def comment_by_locations(self,
    #                          locations=None,
    #                          amount=50,
    #                          media=None,
    #                          skip_top_posts=True):
    #     """Likes (default) 50 images per given locations"""
    #     if self.aborting:
    #         return self

    #     commented = 0
    #     followed = 0
    #     inap_img = 0
    #     not_valid_users = 0

    #     locations = locations or []
    #     self.quotient_breach = False

    #     for index, location in enumerate(locations):
    #         if self.quotient_breach:
    #             break

    #         self.logger.info('Location [{}/{}]'
    #                          .format(index + 1, len(locations)))
    #         self.logger.info('--> {}'.format(location.encode('utf-8')))

    #         try:
    #             links = get_links_for_location(self.browser,
    #                                            location,
    #                                            amount,
    #                                            self.logger,
    #                                            media,
    #                                            skip_top_posts)
    #         except NoSuchElementException:
    #             self.logger.warning('Too few images, skipping this location')
    #             continue

    #         for i, link in enumerate(links):
    #             if self.jumps["consequent"]["comments"] >= self.jumps["limit"][
    #                     "comments"]:
    #                 self.logger.warning(
    #                     "--> Comment quotient reached its peak!\t~leaving "
    #                     "Comment-By-Locations activity\n")
    #                 self.quotient_breach = True
    #                 # reset jump counter after a breach report
    #                 self.jumps["consequent"]["comments"] = 0
    #                 break

    #             self.logger.info('[{}/{}]'.format(i + 1, len(links)))
    #             self.logger.info(link)

    #             try:
    #                 inappropriate, user_name, is_video, reason, scope = (
    #                     check_link(self.browser,
    #                                link,
    #                                self.dont_like,
    #                                self.mandatory_words,
    #                                self.mandatory_language,
    #                                self.is_mandatory_character,
    #                                self.mandatory_character,
    #                                self.check_character_set,
    #                                self.ignore_if_contains,
    #                                self.logger))
    #                 if not inappropriate:
    #                     # validate user
    #                     validation, details = self.validate_user_call(
    #                         user_name)
    #                     if validation is not True:
    #                         self.logger.info(details)
    #                         not_valid_users += 1
    #                         continue
    #                     else:
    #                         web_address_navigator( self.browser, link, Settings)

    #                     # try to comment
    #                     self.logger.info(
    #                         "--> Image not liked: Likes are disabled for the "
    #                         "'Comment-By-Locations' feature")

    #                     checked_img = True
    #                     temp_comments = []
    #                     commenting = random.randint(
    #                         0, 100) <= self.comment_percentage
    #                     following = random.randint(
    #                         0, 100) <= self.follow_percentage

    #                     if not commenting:
    #                         self.logger.info(
    #                             "--> Image not commented: skipping out of "
    #                             "given comment percentage")
    #                         continue

    #                     if self.use_clarifai:
    #                         try:
    #                             checked_img, temp_comments, clarifai_tags = (
    #                                 self.query_clarifai())

    #                         except Exception as err:
    #                             self.logger.error(
    #                                 'Image check error: {}'.format(err))

    #                     if (self.do_comment and
    #                             user_name not in self.dont_include and
    #                             checked_img):

    #                         if self.delimit_commenting:
    #                             (self.commenting_approved,
    #                              disapproval_reason) = verify_commenting(
    #                                 self.browser,
    #                                 self.max_comments,
    #                                 self.min_comments,
    #                                 self.comments_mandatory_words,
    #                                 self.logger)
    #                         if self.commenting_approved:
    #                             # smart commenting
    #                             comments = \
    #                                 self.fetch_smart_comments(is_video,
    #                                                           temp_comments)
    #                             if comments:
    #                                 comment_state, msg = comment_image(
    #                                     self.browser,
    #                                     user_name,
    #                                     comments,
    #                                     self.blacklist,
    #                                     self.logger,
    #                                     self.logfolder,
    #                                     Settings)
    #                                 if comment_state is True:
    #                                     commented += 1
    #                                     # reset jump counter after a
    #                                     # successful comment
    #                                     self.jumps["consequent"][
    #                                         "comments"] = 0

    #                                     # try to follow
    #                                     if (self.do_follow and
    #                                             user_name not in
    #                                             self.dont_include and
    #                                             checked_img and
    #                                             following and
    #                                             not follow_restriction(
    #                                                 "read",
    #                                                 user_name,
    #                                                 self.follow_times,
    #                                                 self.logger)):

    #                                         follow_state, msg = follow_user(
    #                                             self.browser,
    #                                             "post",
    #                                             self.username,
    #                                             user_name,
    #                                             None,
    #                                             self.blacklist,
    #                                             self.logger,
    #                                             self.logfolder)
    #                                         if follow_state is True:
    #                                             followed += 1

    #                                     else:
    #                                         self.logger.info(
    #                                             '--> Not following')
    #                                         sleep(1)

    #                             elif msg == "jumped":
    #                                 # will break the loop after certain
    #                                 # consecutive jumps
    #                                 self.jumps["consequent"]["comments"] += 1

    #                         else:
    #                             self.logger.info(disapproval_reason)

    #                     else:
    #                         self.logger.info('--> Not commented')
    #                         sleep(1)

    #                 else:
    #                     self.logger.info(
    #                         '--> Image not commented: {}'.format(
    #                             reason.encode('utf-8')))
    #                     inap_img += 1

    #             except NoSuchElementException as err:
    #                 self.logger.error('Invalid Page: {}'.format(err))

    #     self.logger.info('Location: {}'.format(location.encode('utf-8')))
    #     self.logger.info('Commented: {}'.format(commented))
    #     self.logger.info('Followed: {}'.format(followed))
    #     self.logger.info('Inappropriate: {}'.format(inap_img))
    #     self.logger.info('Not valid users: {}\n'.format(not_valid_users))

    #     self.followed += followed
    #     self.not_valid_users += not_valid_users

    #     return self

    # def like_by_tags(self,
    #                  tags=None,
    #                  amount=50,
    #                  skip_top_posts=True,
    #                  use_smart_hashtags=False,
    #                  interact=False,
    #                  randomize=False,
    #                  media=None):
    #     """Likes (default) 50 images per given tag"""
    #     if self.aborting:
    #         return self

    #     liked_img = 0
    #     already_liked = 0
    #     inap_img = 0
    #     commented = 0
    #     followed = 0
    #     not_valid_users = 0

    #     # if smart hashtag is enabled
    #     if use_smart_hashtags is True and self.smart_hashtags is not []:
    #         print('Using smart hashtags')
    #         tags = self.smart_hashtags

    #     # deletes white spaces in tags
    #     tags = [tag.strip() for tag in tags]
    #     tags = tags or []
    #     self.quotient_breach = False

    #     for index, tag in enumerate(tags):
    #         if self.quotient_breach:
    #             break

    #         self.logger.info('Tag [{}/{}]'.format(index + 1, len(tags)))
    #         self.logger.info('--> {}'.format(tag.encode('utf-8')))

    #         try:
    #             links = get_links_for_tag(self.browser,
    #                                       tag,
    #                                       amount,
    #                                       skip_top_posts,
    #                                       randomize,
    #                                       media,
    #                                       self.logger)
    #         except NoSuchElementException:
    #             self.logger.info('Too few images, skipping this tag')
    #             continue

    #         for i, link in enumerate(links):
    #             if self.jumps["consequent"]["likes"] >= self.jumps["limit"][
    #                     "likes"]:
    #                 self.logger.warning(
    #                     "--> Like quotient reached its peak!\t~leaving "
    #                     "Like-By-Tags activity\n")
    #                 self.quotient_breach = True
    #                 # reset jump counter after a breach report
    #                 self.jumps["consequent"]["likes"] = 0
    #                 break

    #             self.logger.info('[{}/{}]'.format(i + 1, len(links)))
    #             self.logger.info(link)

    #             try:
    #                 inappropriate, user_name, is_video, reason, scope = (
    #                     check_link(self.browser,
    #                                link,
    #                                self.dont_like,
    #                                self.mandatory_words,
    #                                self.mandatory_language,
    #                                self.is_mandatory_character,
    #                                self.mandatory_character,
    #                                self.check_character_set,
    #                                self.ignore_if_contains,
    #                                self.logger)
    #                 )

    #                 if not inappropriate and self.delimit_liking:
    #                     self.liking_approved = verify_liking(self.browser,
    #                                                          self.max_likes,
    #                                                          self.min_likes,
    #                                                          self.logger)

    #                 if not inappropriate and self.liking_approved:
    #                     # validate user
    #                     validation, details = self.validate_user_call(
    #                         user_name)
    #                     if validation is not True:
    #                         self.logger.info(details)
    #                         not_valid_users += 1
    #                         continue
    #                     else:
    #                         web_address_navigator( self.browser, link, Settings)

    #                     # try to like
    #                     like_state, msg = like_image(self.browser,
    #                                                  user_name,
    #                                                  self.blacklist,
    #                                                  self.logger,
    #                                                  self.logfolder,
    #                                                  Settings)

    #                     if like_state is True:
    #                         liked_img += 1
    #                         # reset jump counter after a successful like
    #                         self.jumps["consequent"]["likes"] = 0

    #                         checked_img = True
    #                         temp_comments = []

    #                         commenting = (random.randint(0, 100) <=
    #                                       self.comment_percentage)
    #                         following = (random.randint(0, 100) <=
    #                                      self.follow_percentage)

    #                         if self.use_clarifai and (following or commenting):
    #                             try:
    #                                 checked_img, temp_comments, \
    #                                     clarifai_tags = (
    #                                         self.query_clarifai())

    #                             except Exception as err:
    #                                 self.logger.error(
    #                                     'Image check error: {}'.format(err))

    #                         # comments
    #                         if (self.do_comment and
    #                                 user_name not in self.dont_include and
    #                                 checked_img and
    #                                 commenting):

    #                             if self.delimit_commenting:
    #                                 (self.commenting_approved,
    #                                  disapproval_reason) = verify_commenting(
    #                                     self.browser,
    #                                     self.max_comments,
    #                                     self.min_comments,
    #                                     self.comments_mandatory_words,
    #                                     self.logger)
    #                             if self.commenting_approved:
    #                                 # smart commenting
    #                                 comments = self.fetch_smart_comments(
    #                                     is_video,
    #                                     temp_comments)
    #                                 if comments:
    #                                     comment_state, msg = comment_image(
    #                                         self.browser,
    #                                         user_name,
    #                                         comments,
    #                                         self.blacklist,
    #                                         self.logger,
    #                                         self.logfolder,
    #                                         Settings)
    #                                     if comment_state is True:
    #                                         commented += 1

    #                             else:
    #                                 self.logger.info(disapproval_reason)

    #                         else:
    #                             self.logger.info('--> Not commented')
    #                             sleep(1)

    #                         # following
    #                         if (self.do_follow and
    #                                 user_name not in self.dont_include and
    #                                 checked_img and
    #                                 following and
    #                                 not follow_restriction("read", user_name,
    #                                                        self.follow_times,
    #                                                        self.logger)):

    #                             follow_state, msg = follow_user(self.browser,
    #                                                             "post",
    #                                                             self.username,
    #                                                             user_name,
    #                                                             None,
    #                                                             self.blacklist,
    #                                                             self.logger,
    #                                                             self.logfolder)
    #                             if follow_state is True:
    #                                 followed += 1
    #                         else:
    #                             self.logger.info('--> Not following')
    #                             sleep(1)

    #                         # interactions (if any)
    #                         if interact:
    #                             self.logger.info(
    #                                 "--> User gonna be interacted: '{}'"
    #                                 .format(user_name))

    #                             self.like_by_users(user_name,
    #                                                self.user_interact_amount,
    #                                                self.user_interact_random,
    #                                                self.user_interact_media)

    #                     elif msg == "already liked":
    #                         already_liked += 1

    #                     elif msg == "jumped":
    #                         # will break the loop after certain consecutive
    #                         # jumps
    #                         self.jumps["consequent"]["likes"] += 1

    #                 else:
    #                     self.logger.info(
    #                         '--> Image not liked: {}'.format(
    #                             reason.encode('utf-8')))
    #                     inap_img += 1

    #             except NoSuchElementException as err:
    #                 self.logger.error('Invalid Page: {}'.format(err))

    #     self.logger.info('Tag: {}'.format(tag.encode('utf-8')))
    #     self.logger.info('Liked: {}'.format(liked_img))
    #     self.logger.info('Already Liked: {}'.format(already_liked))
    #     self.logger.info('Commented: {}'.format(commented))
    #     self.logger.info('Followed: {}'.format(followed))
    #     self.logger.info('Inappropriate: {}'.format(inap_img))
    #     self.logger.info('Not valid users: {}\n'.format(not_valid_users))

    #     self.liked_img += liked_img
    #     self.already_liked += already_liked
    #     self.commented += commented
    #     self.followed += followed
    #     self.inap_img += inap_img
    #     self.not_valid_users += not_valid_users

    #     return self

    # def like_by_users(self, usernames, amount=10, randomize=False, media=None):
    #     """Likes some amounts of images for each usernames"""
    #     if self.aborting:
    #         return self

    #     if not isinstance(usernames, list):
    #         usernames = [usernames]

    #     liked_img = 0
    #     total_liked_img = 0
    #     already_liked = 0
    #     inap_img = 0
    #     commented = 0
    #     followed = 0
    #     not_valid_users = 0

    #     usernames = usernames or []
    #     self.quotient_breach = False

    #     for index, username in enumerate(usernames):
    #         if self.quotient_breach:
    #             break

    #         self.logger.info("Username [{}/{}]"
    #                          .format(index + 1, len(usernames)))
    #         self.logger.info("--> {}"
    #                          .format(username.encode('utf-8')))

    #         following = random.randint(0, 100) <= self.follow_percentage

    #         validation, details = self.validate_user_call(username)
    #         if not validation:
    #             self.logger.info("--> Not a valid user: {}".format(details))
    #             not_valid_users += 1
    #             continue

    #         try:
    #             links = get_links_for_username(
    #                 self.browser,
    #                 self.username,
    #                 username,
    #                 amount,
    #                 self.logger,
    #                 self.logfolder,
    #                 randomize,
    #                 media)

    #         except NoSuchElementException:
    #             self.logger.error('Element not found, skipping this username')
    #             continue

    #         if (self.do_follow and
    #                 username not in self.dont_include and
    #                 following and
    #                 not follow_restriction("read",
    #                                        username,
    #                                        self.follow_times,
    #                                        self.logger)):
    #             follow_state, msg = follow_user(self.browser,
    #                                             "profile",
    #                                             self.username,
    #                                             username,
    #                                             None,
    #                                             self.blacklist,
    #                                             self.logger,
    #                                             self.logfolder)
    #             if follow_state is True:
    #                 followed += 1
    #         else:
    #             self.logger.info('--> Not following')
    #             sleep(1)

    #         if links is False:
    #             continue

    #         # Reset like counter for every username
    #         liked_img = 0

    #         for i, link in enumerate(links):
    #             # Check if target has reached
    #             if liked_img >= amount:
    #                 self.logger.info('-------------')
    #                 self.logger.info("--> Total liked image reached it's "
    #                                  "amount given: {}".format(liked_img))
    #                 break

    #             if self.jumps["consequent"]["likes"] >= self.jumps["limit"][
    #                     "likes"]:
    #                 self.logger.warning(
    #                     "--> Like quotient reached its peak!\t~leaving "
    #                     "Like-By-Users activity\n")
    #                 self.quotient_breach = True
    #                 # reset jump counter after a breach report
    #                 self.jumps["consequent"]["likes"] = 0
    #                 break

    #             self.logger.info('Post [{}/{}]'.format(liked_img + 1, amount))
    #             self.logger.info(link)

    #             try:
    #                 inappropriate, user_name, is_video, reason, scope = (
    #                     check_link(self.browser,
    #                                link,
    #                                self.dont_like,
    #                                self.mandatory_words,
    #                                self.mandatory_language,
    #                                self.is_mandatory_character,
    #                                self.mandatory_character,
    #                                self.check_character_set,
    #                                self.ignore_if_contains,
    #                                self.logger))

    #                 if not inappropriate and self.delimit_liking:
    #                     self.liking_approved = verify_liking(self.browser,
    #                                                          self.max_likes,
    #                                                          self.min_likes,
    #                                                          self.logger)

    #                 if not inappropriate and self.liking_approved:
    #                     like_state, msg = like_image(self.browser,
    #                                                  user_name,
    #                                                  self.blacklist,
    #                                                  self.logger,
    #                                                  self.logfolder,
    #                                                  Settings)
    #                     if like_state is True:
    #                         total_liked_img += 1
    #                         liked_img += 1
    #                         # reset jump counter after a successful like
    #                         self.jumps["consequent"]["likes"] = 0

    #                         checked_img = True
    #                         temp_comments = []

    #                         commenting = random.randint(
    #                             0, 100) <= self.comment_percentage

    #                         if self.use_clarifai and (following or commenting):
    #                             try:
    #                                 checked_img, temp_comments, \
    #                                     clarifai_tags = (
    #                                         self.query_clarifai())

    #                             except Exception as err:
    #                                 self.logger.error(
    #                                     'Image check error: {}'.format(err))

    #                         if (self.do_comment and
    #                                 user_name not in self.dont_include and
    #                                 checked_img and
    #                                 commenting):

    #                             if self.delimit_commenting:
    #                                 (self.commenting_approved,
    #                                  disapproval_reason) = verify_commenting(
    #                                     self.browser,
    #                                     self.max_comments,
    #                                     self.min_comments,
    #                                     self.comments_mandatory_words,
    #                                     self.logger)
    #                             if self.commenting_approved:
    #                                 # smart commenting
    #                                 comments = self.fetch_smart_comments(
    #                                     is_video,
    #                                     temp_comments)
    #                                 if comments:
    #                                     comment_state, msg = comment_image(
    #                                         self.browser,
    #                                         user_name,
    #                                         comments,
    #                                         self.blacklist,
    #                                         self.logger,
    #                                         self.logfolder,
    #                                         Settings)
    #                                     if comment_state is True:
    #                                         commented += 1

    #                             else:
    #                                 self.logger.info(disapproval_reason)

    #                         else:
    #                             self.logger.info('--> Not commented')
    #                             sleep(1)

    #                     elif msg == "already liked":
    #                         already_liked += 1

    #                     elif msg == "jumped":
    #                         # will break the loop after certain consecutive
    #                         # jumps
    #                         self.jumps["consequent"]["likes"] += 1

    #                 else:
    #                     self.logger.info(
    #                         '--> Image not liked: {}'.format(
    #                             reason.encode('utf-8')))
    #                     inap_img += 1

    #             except NoSuchElementException as err:
    #                 self.logger.error('Invalid Page: {}'.format(err))

    #         if liked_img < amount:
    #             self.logger.info('-------------')
    #             self.logger.info("--> Given amount not fullfilled, "
    #                              "image pool reached its end\n")

    #     self.logger.info('User: {}'.format(username.encode('utf-8')))
    #     self.logger.info('Liked: {}'.format(total_liked_img))
    #     self.logger.info('Already Liked: {}'.format(already_liked))
    #     self.logger.info('Commented: {}'.format(commented))
    #     self.logger.info('Inappropriate: {}'.format(inap_img))
    #     self.logger.info('Not valid users: {}\n'.format(not_valid_users))

    #     self.liked_img += liked_img
    #     self.already_liked += already_liked
    #     self.commented += commented
    #     self.inap_img += inap_img
    #     self.not_valid_users += not_valid_users

    #     return self
    def open_message_to_user(self, endusers, message):
        if not isinstance(endusers, list):
            endusers = [endusers]
        for enduser in endusers:
            open_message(self.browser, "profile", self.username, enduser, None, self.logger, self.logfolder, message)
            sleep(3)

    def message_group_users(self, keyword, message):
 
        bot = self.browser
 
        # fetches the latest tweets with the provided hashtag
        self.search(query=keyword)
        """bot.get(
            'https://twitter.com / search?q =% 23' + \
            hashtag+'&src = typed_query&f = live'
        )"""
 
        time.sleep(3)
 
        # using set so that only unique links
        # are present and to avoid unnecessary repetition
        links = set()
 
        # obtaining the links of the tweets
        for i in range(7):
            # executing javascript code
            # to scroll the webpage
            bot.execute_script(
                'window.scrollTo(0, document.body.scrollHeight)'
            )
 
            time.sleep(5)
 
            # using list comprehension
            # for adding all the tweets link to the set
            # this particular piece of code might
            # look very complicated but the only reason
            # I opted for list comprehension because is
            # lot faster than traditional loops
            [
                links.add(elem.get_attribute('href'))\
                for elem in bot.find_elements_by_xpath("//a[@role='link'][contains(@href, 'groups')]")
            ]
        print(links)
 
        # traversing through the generated links
        for link in links:
            # opens individual links
            time.sleep(7)
            if 'https://web.facebook.com/groups/' in link:
                if "user" not in link and "post" not in link and "search" not in link and len(link)>42:
                    print(link)
                    bot.get(link+'members')
                    user_links = set()
                    for i in range(5):
                        # executing javascript code
                        # to scroll the webpage
                        bot.execute_script(
                            'window.scrollTo(0, document.body.scrollHeight)'
                        )
             
                        time.sleep(5)
             
                        # using list comprehension
                        # for adding all the tweets link to the set
                        # this particular piece of code might
                        # look very complicated but the only reason
                        # I opted for list comprehension because is
                        # lot faster than traditional loops
                        [
                            user_links.add(elem.get_attribute('href'))\
                            for elem in bot.find_elements_by_xpath("//a[@role='link'][contains(@href, '/user/')]")
                        ]
                    print(user_links)
                    user_count=0
                    user_links=random.sample(user_links, len(user_links))
                    user_links=list(dict.fromkeys(user_links))
                    for user_link in user_links:
                        if user_count<25:
                            open_message(bot, "profile", self.username, user_link, None, self.logger, self.logfolder, message, from_group=True)
                            user_count+=1

                else:
                    pass
    
        # fetches the main homepage
        bot.get('https://web.facebook.com/')

    def interact_by_users(self,
                          usernames,
                          amount=10,
                          randomize=False,
                          media=None):
        """Likes some amounts of images for each usernames"""
        if self.aborting:
            return self

        message = "Starting to interact by users.."
        highlight_print(Settings, self.username, message, "feature", "info", self.logger)

        if not isinstance(usernames, list):
            usernames = [usernames]

        time.sleep(3)
 
        # using set so that only unique links
        # are present and to avoid unnecessary repetition
        for username in usernames:
            self.browser.get('web.facebook.com/{}'.format(username))
            links = set()
            # obtaining the links of the tweets
            for i in range(9):
                # executing javascript code
                # to scroll the webpage
                self.browser.execute_script(
                    'window.scrollTo(0, document.body.scrollHeight)'
                )
    
                time.sleep(4)

        # standalone means this feature is started by the user
        standalone = True if "interact_by_users" not in \
                             self.internal_usage.keys() else False
        # skip validation in case of it is already accomplished
        users_validated = True if not standalone and not \
            self.internal_usage["interact_by_users"]["validate"] else False

        total_liked_img = 0
        already_liked = 0
        inap_img = 0
        commented = 0
        followed = 0
        already_followed = 0
        not_valid_users = 0

        self.quotient_breach = False

        for index, username in enumerate(usernames):
            if self.quotient_breach:
                # keep `quotient_breach` active to break the internal
                # iterators of the caller
                self.quotient_breach = True if not standalone else False
                break

            self.logger.info(
                'Username [{}/{}]'.format(index + 1, len(usernames)))
            self.logger.info('--> {}'.format(username.encode('utf-8')))


            track = 'profile'
            # decision making
            # static conditions
            not_dont_include = username not in self.dont_include
            follow_restricted = follow_restriction("read", username,
                                                   self.follow_times,
                                                   self.logger)
            counter = 0
            while True:
                following = (random.randint(0,
                                            100) <= self.follow_percentage and
                             self.do_follow and
                             not_dont_include and
                             not follow_restricted)
                commenting = (random.randint(0,
                                             100) <= self.comment_percentage
                              and
                              self.do_comment and
                              not_dont_include)
                liking = (random.randint(0, 100) <= self.like_percentage)

                counter += 1

                # if we have only one image to like/comment
                if commenting and not liking and amount == 1:
                    continue

                if following or commenting or liking:
                    self.logger.info(
                        'username actions: following={} commenting={} '
                        'liking={}'.format(
                            following, commenting, liking))
                    break

                # if for some reason we have no actions on this user
                if counter > 5:
                    self.logger.info(
                        'username={} could not get interacted'.format(
                            username))
                    break

            try:
                links = get_links_for_username(self.browser,
                                               self.username,
                                               username,
                                               amount,
                                               self.logger,
                                               self.logfolder,
                                               randomize,
                                               media)
            except NoSuchElementException:
                self.logger.error('Element not found, skipping this username')
                continue

            if links is False:
                continue

            # Reset like counter for every username
            liked_img = 0

            for i, link in enumerate(links[:amount]):
                if self.jumps["consequent"]["likes"] >= self.jumps["limit"][
                        "likes"]:
                    self.logger.warning(
                        "--> Like quotient reached its peak!\t~leaving "
                        "Interact-By-Users activity\n")
                    self.quotient_breach = True
                    # reset jump counter after a breach report
                    self.jumps["consequent"]["likes"] = 0
                    break

                # Check if target has reached
                if liked_img >= amount:
                    self.logger.info('-------------')
                    self.logger.info("--> Total liked image reached it's "
                                     "amount given: {}".format(liked_img))
                    break

                self.logger.info(
                    'Post [{}/{}]'.format(liked_img + 1, len(links[:amount])))
                self.logger.info(link)

                try:
                    inappropriate, user_name, is_video, reason, scope = (
                        check_link(self.browser,
                                   link,
                                   self.dont_like,
                                   self.mandatory_words,
                                   self.mandatory_language,
                                   self.is_mandatory_character,
                                   self.mandatory_character,
                                   self.check_character_set,
                                   self.ignore_if_contains,
                                   self.logger))
                    track = "post"

                    if not inappropriate:
                        # after first image we roll again
                        if i > 0:
                            liking = (random.randint(0,
                                                     100) <=
                                      self.like_percentage)
                            commenting = (random.randint(0,
                                                         100) <=
                                          self.comment_percentage and
                                          self.do_comment and
                                          not_dont_include)

                        # like
                        if self.do_like and liking and self.delimit_liking:
                            self.liking_approved = \
                                verify_liking(self.browser,
                                              self.max_likes,
                                              self.min_likes,
                                              self.logger)

                        if self.do_like and liking and self.liking_approved:
                            like_state, msg = like_image(self.browser,
                                                         user_name,
                                                         self.blacklist,
                                                         self.logger,
                                                         self.logfolder,
                                                         Settings)
                            if like_state is True:
                                total_liked_img += 1
                                liked_img += 1
                                # reset jump counter after a successful like
                                self.jumps["consequent"]["likes"] = 0

                                # comment
                                checked_img = True
                                temp_comments = []

                                # if self.use_clarifai and commenting:
                                #     try:
                                #         # checked_img, temp_comments, \
                                #             # clarifai_tags = (
                                #             #     self.query_clarifai())

                                #     except Exception as err:
                                #         self.logger.error(
                                #             'Image check error: {}'.format(
                                #                 err))

                                if commenting and checked_img:

                                    if self.delimit_commenting:
                                        (self.commenting_approved,
                                         disapproval_reason) = \
                                            verify_commenting(
                                                self.browser,
                                                self.max_comments,
                                                self.min_comments,
                                                self.comments_mandatory_words,
                                                self.logger)
                                    if self.commenting_approved:
                                        # smart commenting
                                        comments = self.fetch_smart_comments(
                                            is_video,
                                            temp_comments)
                                        if comments:
                                            comment_state, msg = comment_image(
                                                self.browser,
                                                user_name,
                                                comments,
                                                self.blacklist,
                                                self.logger,
                                                self.logfolder,
                                                Settings)
                                            if comment_state is True:
                                                commented += 1

                                    else:
                                        self.logger.info(disapproval_reason)

                                else:
                                    self.logger.info('--> Not commented')
                                    sleep(1)

                            elif msg == "already liked":
                                already_liked += 1

                            elif msg == "jumped":
                                # will break the loop after certain
                                # consecutive jumps
                                self.jumps["consequent"]["likes"] += 1

                    else:
                        self.logger.info(
                            '--> Image not liked: {}'.format(
                                reason.encode('utf-8')))
                        inap_img += 1

                except NoSuchElementException as err:
                    self.logger.info('Invalid Page: {}'.format(err))

            # follow
            if following and not (self.dont_follow_inap_post and inap_img > 0):

                follow_state, msg = follow_user(
                    self.browser,
                    track,
                    self.username,
                    username,
                    None,
                    self.blacklist,
                    self.logger,
                    self.logfolder)
                if follow_state is True:
                    followed += 1

                elif msg == "already followed":
                    already_followed += 1

            else:
                self.logger.info('--> Not following')
                sleep(1)

            if liked_img < amount:
                self.logger.info('-------------')
                self.logger.info("--> Given amount not fullfilled, image pool "
                                 "reached its end\n")

        if len(usernames) > 1:
            # final words
            interacted_media_size = (len(usernames) * amount - inap_img)
            self.logger.info(
                "Finished interacting on total of {} "
                "images from {} users! xD\n"
                .format(interacted_media_size, len(usernames)))

            # print results
            self.logger.info('Liked: {}'.format(total_liked_img))
            self.logger.info('Already Liked: {}'.format(already_liked))
            self.logger.info('Commented: {}'.format(commented))
            self.logger.info('Followed: {}'.format(followed))
            self.logger.info('Already Followed: {}'.format(already_followed))
            self.logger.info('Inappropriate: {}'.format(inap_img))
            self.logger.info('Not valid users: {}\n'.format(not_valid_users))

        self.liked_img += total_liked_img
        self.already_liked += already_liked
        self.commented += commented
        self.followed += followed
        self.already_followed += already_followed
        self.inap_img += inap_img
        self.not_valid_users += not_valid_users

        return self

    # def interact_by_users_tagged_posts(self,
    #                                    usernames,
    #                                    amount=10,
    #                                    randomize=False,
    #                                    media=None):
    #     """Likes some amounts of tagged images for each usernames"""
    #     if self.aborting:
    #         return self

    #     if not isinstance(usernames, list):
    #         usernames = [usernames]

    #     # standalone means this feature is started by the user
    #     standalone = True if "interact_by_users" not in \
    #                          self.internal_usage.keys() else False
    #     # skip validation in case of it is already accomplished
    #     users_validated = True if not standalone and not \
    #         self.internal_usage["interact_by_users"]["validate"] else False

    #     total_liked_img = 0
    #     already_liked = 0
    #     inap_img = 0
    #     commented = 0
    #     followed = 0
    #     already_followed = 0
    #     not_valid_users = 0

    #     self.quotient_breach = False

    #     for index, username in enumerate(usernames):
    #         if self.quotient_breach:
    #             # keep `quotient_breach` active to break the internal
    #             # iterators of the caller
    #             self.quotient_breach = True if not standalone else False
    #             break

    #         self.logger.info(
    #             'Username [{}/{}]'.format(index + 1, len(usernames)))
    #         self.logger.info('--> {}'.format(username.encode('utf-8')))

    #         if not users_validated and username != self.username:
    #             validation, details = self.validate_user_call(username)
    #             if not validation:
    #                 self.logger.info(
    #                     "--> not a valid user: {}".format(details))
    #                 not_valid_users += 1
    #                 continue

    #         # decision making
    #         # static conditions
    #         not_dont_include = username not in self.dont_include
    #         follow_restricted = follow_restriction("read", username,
    #                                                self.follow_times,
    #                                                self.logger)
    #         counter = 0
    #         while True:
    #             following = (random.randint(0,
    #                                         100) <= self.follow_percentage and
    #                          self.do_follow and
    #                          not_dont_include and
    #                          not follow_restricted)
    #             commenting = (random.randint(0,
    #                                          100) <= self.comment_percentage
    #                           and
    #                           self.do_comment and
    #                           not_dont_include)
    #             liking = (random.randint(0, 100) <= self.like_percentage)

    #             counter += 1

    #             # if we have only one image to like/comment
    #             if commenting and not liking and amount == 1:
    #                 continue
    #             if following or commenting or liking:
    #                 self.logger.info(
    #                     'username actions: following={} commenting={} '
    #                     'liking={}'.format(
    #                         following, commenting, liking))
    #                 break
    #             # if for some reason we have no actions on this user
    #             if counter > 5:
    #                 self.logger.info(
    #                     'username={} could not get interacted'.format(
    #                         username))
    #                 break

    #         try:
    #             links = get_links_for_username(self.browser,
    #                                            self.username,
    #                                            username,
    #                                            amount,
    #                                            self.logger,
    #                                            self.logfolder,
    #                                            randomize,
    #                                            media,
    #                                            taggedImages=True)
    #         except NoSuchElementException:
    #             self.logger.error('Element not found, skipping this username')
    #             continue

    #         if links is False:
    #             continue

    #         # Reset like counter for every username
    #         liked_img = 0

    #         for i, link in enumerate(links[:amount]):
    #             if self.jumps["consequent"]["likes"] >= self.jumps["limit"][
    #                     "likes"]:
    #                 self.logger.warning(
    #                     "--> Like quotient reached its peak!\t~leaving "
    #                     "Interact-By-Users activity\n")
    #                 self.quotient_breach = True
    #                 # reset jump counter after a breach report
    #                 self.jumps["consequent"]["likes"] = 0
    #                 break

    #             # Check if target has reached
    #             if liked_img >= amount:
    #                 self.logger.info('-------------')
    #                 self.logger.info("--> Total liked image reached it's "
    #                                  "amount given: {}".format(liked_img))
    #                 break

    #             self.logger.info(
    #                 'Post [{}/{}]'.format(liked_img + 1, len(links[:amount])))
    #             self.logger.info(link)

    #             try:
    #                 inappropriate, user_name, is_video, reason, scope = (
    #                     check_link(self.browser,
    #                                link,
    #                                self.dont_like,
    #                                self.mandatory_words,
    #                                self.mandatory_language,
    #                                self.is_mandatory_character,
    #                                self.mandatory_character,
    #                                self.check_character_set,
    #                                self.ignore_if_contains,
    #                                self.logger))

    #                 if not inappropriate:
    #                     # after first image we roll again
    #                     if i > 0:
    #                         liking = (
    #                             random.randint(0,
    #                                            100) <=
    #                             self.like_percentage)
    #                         commenting = (
    #                             random.randint(0,
    #                                            100) <=
    #                             self.comment_percentage and
    #                             self.do_comment and
    #                             not_dont_include)

    #                     # like
    #                     if self.do_like and liking and self.delimit_liking:
    #                         self.liking_approved = verify_liking(
    #                             self.browser,
    #                             self.max_likes,
    #                             self.min_likes,
    #                             self.logger)

    #                     if self.do_like and liking and self.liking_approved:
    #                         like_state, msg = like_image(self.browser,
    #                                                      user_name,
    #                                                      self.blacklist,
    #                                                      self.logger,
    #                                                      self.logfolder,
    #                                                      Settings)
    #                         if like_state is True:
    #                             total_liked_img += 1
    #                             liked_img += 1
    #                             # reset jump counter after a successful like
    #                             self.jumps["consequent"]["likes"] = 0

    #                             # comment
    #                             checked_img = True
    #                             temp_comments = []

    #                             if self.use_clarifai and commenting:
    #                                 try:
    #                                     (checked_img,
    #                                      temp_comments,
    #                                      clarifai_tags) = self.query_clarifai()
    #                                 except Exception as err:
    #                                     self.logger.error(
    #                                         'Image check error: {}'.format(
    #                                             err))

    #                             if commenting and checked_img:

    #                                 if self.delimit_commenting:
    #                                     (self.commenting_approved,
    #                                      disapproval_reason) = \
    #                                         verify_commenting(
    #                                             self.browser,
    #                                             self.max_comments,
    #                                             self.min_comments,
    #                                             self.comments_mandatory_words,
    #                                             self.logger)
    #                                 if self.commenting_approved:
    #                                     if temp_comments:
    #                                         # use clarifai related comments
    #                                         # only!
    #                                         comments = temp_comments

    #                                     elif is_video:
    #                                         comments = (self.comments +
    #                                                     self.video_comments)

    #                                     else:
    #                                         comments = (self.comments +
    #                                                     self.photo_comments)

    #                                     comment_state, msg = comment_image(
    #                                         self.browser,
    #                                         user_name,
    #                                         comments,
    #                                         self.blacklist,
    #                                         self.logger,
    #                                         self.logfolder,
    #                                         Settings)
    #                                     if comment_state is True:
    #                                         commented += 1

    #                                 else:
    #                                     self.logger.info(disapproval_reason)

    #                             else:
    #                                 self.logger.info('--> Not commented')
    #                                 sleep(1)

    #                         elif msg == "already liked":
    #                             already_liked += 1

    #                         elif msg == "jumped":
    #                             # will break the loop after certain
    #                             # consecutive jumps
    #                             self.jumps["consequent"]["likes"] += 1

    #                 else:
    #                     self.logger.info(
    #                         '--> Image not liked: {}'.format(
    #                             reason.encode('utf-8')))
    #                     inap_img += 1

    #             except NoSuchElementException as err:
    #                 self.logger.info('Invalid Page: {}'.format(err))

    #         # follow
    #         if following and not (self.dont_follow_inap_post and inap_img > 0):

    #             follow_state, msg = follow_user(
    #                 self.browser,
    #                 "profile",
    #                 self.username,
    #                 username,
    #                 None,
    #                 self.blacklist,
    #                 self.logger,
    #                 self.logfolder)
    #             if follow_state is True:
    #                 followed += 1

    #             elif msg == "already followed":
    #                 already_followed += 1

    #         else:
    #             self.logger.info('--> Not following')
    #             sleep(1)

    #         if liked_img < amount:
    #             self.logger.info('-------------')
    #             self.logger.info("--> Given amount not fullfilled, image pool "
    #                              "reached its end\n")

    #     # final words
    #     interacted_media_size = (len(usernames) * amount - inap_img)
    #     self.logger.info(
    #         "Finished interacting on total of {} images from {} users! xD\n"
    #         .format(interacted_media_size, len(usernames)))

    #     # print results
    #     self.logger.info('Liked: {}'.format(total_liked_img))
    #     self.logger.info('Already Liked: {}'.format(already_liked))
    #     self.logger.info('Commented: {}'.format(commented))
    #     self.logger.info('Followed: {}'.format(followed))
    #     self.logger.info('Already Followed: {}'.format(already_followed))
    #     self.logger.info('Inappropriate: {}'.format(inap_img))
    #     self.logger.info('Not valid users: {}\n'.format(not_valid_users))

    #     self.liked_img += total_liked_img
    #     self.already_liked += already_liked
    #     self.commented += commented
    #     self.followed += followed
    #     self.already_followed += already_followed
    #     self.inap_img += inap_img
    #     self.not_valid_users += not_valid_users

    #     return self

    # def like_from_image(self, url, amount=50, media=None):
    #     """Gets the tags from an image and likes 50 images for each tag"""
    #     if self.aborting:
    #         return self

    #     try:
    #         if not url:
    #             urls = self.browser.find_elements_by_xpath(
    #                 "//main//article//div//div[1]//div[1]//a[1]")
    #             url = urls[0].get_attribute("href")
    #             self.logger.info("new url {}".format(url))
    #         tags = get_tags(self.browser, url)
    #         self.logger.info(tags)
    #         self.like_by_tags(tags, amount, media)
    #     except TypeError as err:
    #         self.logger.error('Sorry, an error occurred: {}'.format(err))
    #         self.aborting = True
    #         return self

    #     return self

    # def interact_user_followers(self, usernames, amount=10, randomize=False):

    #     if self.aborting:
    #         return self

    #     if self.do_follow is not True and self.do_like is not True:
    #         self.logger.info(
    #             "Please enable following or liking in settings in order to "
    #             "do interactions.")
    #         return self

    #     elif self.user_interact_amount <= 0:
    #         self.logger.info(
    #             "Please choose an amount higher than zero in "
    #             "`set_user_interact` in order to do interactions.")
    #         return self

    #     if not isinstance(usernames, list):
    #         usernames = [usernames]

    #     interacted_all = 0
    #     not_valid_users = 0
    #     simulated_unfollow = 0

    #     # hold the current global values for differentiating at the end
    #     liked_init = self.liked_img
    #     already_liked_init = self.already_liked
    #     commented_init = self.commented
    #     followed_init = self.followed
    #     inap_img_init = self.inap_img

    #     self.quotient_breach = False

    #     for index, user in enumerate(usernames):
    #         if self.quotient_breach:
    #             break

    #         self.logger.info("User '{}' [{}/{}]"
    #                          .format((user),
    #                                  index + 1,
    #                                  len(usernames)))
    #         try:
    #             person_list, simulated_list = get_given_user_followers(
    #                 self.browser,
    #                 self.username,
    #                 self.userid,
    #                 user,
    #                 amount,
    #                 self.dont_include,
    #                 randomize,
    #                 self.blacklist,
    #                 self.follow_times,
    #                 self.simulation,
    #                 self.jumps,
    #                 self.logger,
    #                 self.logfolder)

    #         except (TypeError, RuntimeWarning) as err:
    #             if isinstance(err, RuntimeWarning):
    #                 self.logger.warning(
    #                     u'Warning: {} , skipping to next user'.format(err))
    #                 continue

    #             else:
    #                 self.logger.error(
    #                     'Sorry, an error occurred: {}'.format(err))
    #                 self.aborting = True
    #                 return self

    #         print('')
    #         self.logger.info(
    #             "Grabbed {} usernames from '{}'s `Followers` to do "
    #             "interaction."
    #             .format(len(person_list), user))

    #         interacted_personal = 0

    #         for index, person in enumerate(person_list):
    #             if self.quotient_breach:
    #                 self.logger.warning(
    #                     "--> Like quotient reached its peak!"
    #                     "\t~leaving Interact-User-Followers activity\n")
    #                 break

    #             self.logger.info("User '{}' [{}/{}]".format((person),
    #                                                         index + 1,
    #                                                         len(person_list)))

    #             validation, details = self.validate_user_call(person)
    #             if validation is not True:
    #                 self.logger.info(details)
    #                 not_valid_users += 1

    #                 if person in simulated_list:
    #                     self.logger.warning(
    #                         "--> Simulated Unfollow {}:"
    #                         " unfollowing '{}' due to mismatching "
    #                         "validation..."
    #                         .format(simulated_unfollow + 1, person))
    #                     unfollow_state, msg = \
    #                         unfollow_user(self.browser,
    #                                       "profile",
    #                                       self.username,
    #                                       person,
    #                                       None,
    #                                       None,
    #                                       self.relationship_data,
    #                                       self.logger,
    #                                       self.logfolder)
    #                     if unfollow_state is True:
    #                         simulated_unfollow += 1

    #                 continue

    #             # Do interactions if any
    #             do_interact = random.randint(0,
    #                                          100) <= \
    #                 self.user_interact_percentage

    #             if do_interact is False:
    #                 self.logger.info(
    #                     "Skipping user '{}' due to the interaction "
    #                     "percentage of {}"
    #                     .format(person, self.user_interact_percentage))
    #                 continue

    #             else:
    #                 interacted_all += 1
    #                 interacted_personal += 1

    #                 self.logger.info(
    #                     "Interaction [{}/{}]  |  Total Interaction: {}"
    #                     .format(interacted_personal,
    #                             len(person_list),
    #                             interacted_all))

    #                 with self.feature_in_feature("interact_by_users", False):
    #                     self.interact_by_users(person,
    #                                            self.user_interact_amount,
    #                                            self.user_interact_random,
    #                                            self.user_interact_media)
    #                 if self.aborting:
    #                     return self
    #                 sleep(1)

    #     # final words
    #     self.logger.info(
    #         "Finished interacting {} people from {} users' `Followers`! xD\n"
    #         .format(interacted_all, len(usernames)))

    #     # find the feature-wide action sizes by taking a difference
    #     liked = (self.liked_img - liked_init)
    #     already_liked = (self.already_liked - already_liked_init)
    #     commented = (self.commented - commented_init)
    #     followed = (self.followed - followed_init)
    #     inap_img = (self.inap_img - inap_img_init)

    #     # print results
    #     self.logger.info('Liked: {}'.format(liked))
    #     self.logger.info('Already Liked: {}'.format(already_liked))
    #     self.logger.info('Commented: {}'.format(commented))
    #     self.logger.info('Followed: {}'.format(followed))
    #     self.logger.info('Inappropriate: {}'.format(inap_img))
    #     self.logger.info('Not valid users: {}\n'.format(not_valid_users))

    #     self.not_valid_users += not_valid_users

    #     return self

    # def interact_user_following(self, usernames, amount=10, randomize=False):

    #     if self.aborting:
    #         return self

    #     if self.do_follow is not True and self.do_like is not True:
    #         self.logger.info("Please enable following or liking in settings"
    #                          " in order to do interactions.")
    #         return self

    #     elif self.user_interact_amount <= 0:
    #         self.logger.info(
    #             "Please choose an amount higher than zero in"
    #             " `set_user_interact` in order to do interactions.")
    #         return self

    #     if not isinstance(usernames, list):
    #         usernames = [usernames]

    #     interacted_all = 0
    #     not_valid_users = 0
    #     simulated_unfollow = 0

    #     # hold the current global values for differentiating at the end
    #     liked_init = self.liked_img
    #     already_liked_init = self.already_liked
    #     commented_init = self.commented
    #     followed_init = self.followed
    #     inap_img_init = self.inap_img

    #     self.quotient_breach = False

    #     for index, user in enumerate(usernames):
    #         if self.quotient_breach:
    #             break

    #         self.logger.info("User '{}' [{}/{}]"
    #                          .format((user),
    #                                  index + 1,
    #                                  len(usernames)))
    #         try:
    #             person_list, simulated_list = get_given_user_following(
    #                 self.browser,
    #                 self.username,
    #                 user,
    #                 amount,
    #                 self.dont_include,
    #                 randomize,
    #                 self.blacklist,
    #                 self.follow_times,
    #                 self.simulation,
    #                 self.jumps,
    #                 self.logger,
    #                 self.logfolder)

    #         except (TypeError, RuntimeWarning) as err:
    #             if isinstance(err, RuntimeWarning):
    #                 self.logger.warning(
    #                     u'Warning: {} , skipping to next user'.format(err))
    #                 continue

    #             else:
    #                 self.logger.error(
    #                     'Sorry, an error occurred: {}'.format(err))
    #                 self.aborting = True
    #                 return self

    #         print('')
    #         self.logger.info(
    #             "Grabbed {} usernames from '{}'s `Following` to do "
    #             "interaction."
    #             .format(len(person_list), user))
    #         interacted_personal = 0

    #         for index, person in enumerate(person_list):
    #             if self.quotient_breach:
    #                 self.logger.warning(
    #                     "--> Like quotient reached its peak!"
    #                     "\t~leaving Interact-User-Following activity\n")
    #                 break

    #             self.logger.info("User '{}' [{}/{}]".format((person),
    #                                                         index + 1,
    #                                                         len(person_list)))

    #             validation, details = self.validate_user_call(person)
    #             if validation is not True:
    #                 self.logger.info(details)
    #                 not_valid_users += 1

    #                 if person in simulated_list:
    #                     self.logger.warning(
    #                         "--> Simulated Unfollow {}:"
    #                         " unfollowing '{}' due to mismatching "
    #                         "validation..."
    #                         .format(simulated_unfollow + 1, person))

    #                     unfollow_state, msg = unfollow_user(
    #                         self.browser,
    #                         "profile",
    #                         self.username,
    #                         person,
    #                         None,
    #                         None,
    #                         self.relationship_data,
    #                         self.logger,
    #                         self.logfolder)
    #                     if unfollow_state is True:
    #                         simulated_unfollow += 1

    #                 continue

    #             # Do interactions if any
    #             do_interact = random.randint(0,
    #                                          100) <= \
    #                 self.user_interact_percentage

    #             if do_interact is False:
    #                 self.logger.info("Skipping user '{}' due to"
    #                                  " the interaction percentage of {}"
    #                                  .format(person,
    #                                          self.user_interact_percentage))
    #                 continue

    #             else:
    #                 interacted_all += 1
    #                 interacted_personal += 1

    #                 self.logger.info(
    #                     "Interaction [{}/{}]  |  Total Interaction: {}"
    #                     .format(interacted_personal,
    #                             len(person_list),
    #                             interacted_all))

    #                 with self.feature_in_feature("interact_by_users", False):
    #                     self.interact_by_users(person,
    #                                            self.user_interact_amount,
    #                                            self.user_interact_random,
    #                                            self.user_interact_media)
    #                 if self.aborting:
    #                     return self
    #                 sleep(1)

    #     # final words
    #     self.logger.info("Finished interacting {} people"
    #                      " from {} users' `Following`! xD\n"
    #                      .format(interacted_all,
    #                              len(usernames)))

    #     # find the feature-wide action sizes by taking a difference
    #     liked = (self.liked_img - liked_init)
    #     already_liked = (self.already_liked - already_liked_init)
    #     commented = (self.commented - commented_init)
    #     followed = (self.followed - followed_init)
    #     inap_img = (self.inap_img - inap_img_init)

    #     # print results
    #     self.logger.info('Liked: {}'.format(liked))
    #     self.logger.info('Already Liked: {}'.format(already_liked))
    #     self.logger.info('Commented: {}'.format(commented))
    #     self.logger.info('Followed: {}'.format(followed))
    #     self.logger.info('Inappropriate: {}'.format(inap_img))
    #     self.logger.info('Not valid users: {}\n'.format(not_valid_users))

    #     self.not_valid_users += not_valid_users

    #     return self


    """def follow_user_followers(self,
                              usernames,
                              amount=10,
                              randomize=False,
                              interact=False,
                              sleep_delay=600):
        if self.aborting:
            return self

        message = "Starting to follow user `Followers`.."
        highlight_print(Settings, self.username, message, "feature", "info", self.logger)

        if not isinstance(usernames, list):
            usernames = [usernames]

        followed_all = 0
        followed_new = 0
        not_valid_users = 0

        # below, you can use some static value `10` instead of random ones..
        relax_point = random.randint(7, 14)

        # hold the current global values for differentiating at the end
        already_followed_init = self.already_followed
        liked_init = self.liked_img
        already_liked_init = self.already_liked
        commented_init = self.commented
        inap_img_init = self.inap_img

        self.quotient_breach = False

        for index, user in enumerate(usernames):
            if self.quotient_breach:
                break

            self.logger.info(
                "User '{}' [{}/{}]".format((user), index + 1, len(usernames)))

            try:
                person_list, simulated_list = get_given_user_followers(
                    self.browser,
                    self.username,
                    self.userid,
                    user,
                    amount,
                    self.dont_include,
                    randomize,
                    self.blacklist,
                    self.follow_times,
                    self.simulation,
                    self.jumps,
                    self.logger,
                    self.logfolder)

            except (TypeError, RuntimeWarning) as err:
                if isinstance(err, RuntimeWarning):
                    self.logger.warning(
                        u'Warning: {} , skipping to next user'.format(err))
                    continue

                else:
                    self.logger.error(
                        'Sorry, an error occurred: {}'.format(err))
                    self.aborting = True
                    return self

            print('')
            self.logger.info(
                "Grabbed {} usernames from '{}'s `Followers` to do following\n"
                .format(len(person_list), user))

            followed_personal = 0
            simulated_unfollow = 0

            for index, person in enumerate(person_list):
                if self.quotient_breach:
                    self.logger.warning(
                        "--> Follow quotient reached its peak!"
                        "\t~leaving Follow-User-Followers activity\n")
                    break

                self.logger.info(
                    "Ongoing Follow [{}/{}]: now following '{}'..."
                    .format(index + 1, len(person_list), person))

                validation, details = self.validate_user_call(person)
                if validation is not True:
                    self.logger.info(details)
                    not_valid_users += 1

                    if person in simulated_list:
                        self.logger.warning(
                            "--> Simulated Unfollow {}: unfollowing"
                            " '{}' due to mismatching validation...\n"
                            .format(simulated_unfollow + 1, person))

                        unfollow_state, msg = unfollow_user(
                            self.browser,
                            "profile",
                            self.username,
                            self.userid,
                            person,
                            None,
                            None,
                            self.relationship_data,
                            self.logger,
                            self.logfolder)
                        if unfollow_state is True:
                            simulated_unfollow += 1
                    # skip this [non-validated] user
                    continue

                # go ahead and follow, then interact (if any)
                with self.feature_in_feature("follow_by_list", False):
                    followed = self.follow_by_list(person,
                                                   self.follow_times,
                                                   sleep_delay,
                                                   interact)
                sleep(1)

                if followed > 0:
                    followed_all += 1
                    followed_new += 1
                    followed_personal += 1

                self.logger.info("Follow per user: {}  |  Total Follow: {}\n"
                                 .format(followed_personal, followed_all))

                # take a break after a good following
                if followed_new >= relax_point:
                    delay_random = random.randint(
                        ceil(sleep_delay * 0.85),
                        ceil(sleep_delay * 1.14))
                    sleep_time = ("{} seconds".format(delay_random) if
                                  delay_random < 60 else
                                  "{} minutes".format(truncate_float(
                                      delay_random / 60, 2)))
                    self.logger.info(
                        "------=>  Followed {} new users ~sleeping about {}\n"
                        .format(followed_new, sleep_time))
                    sleep(delay_random)
                    relax_point = random.randint(7, 14)
                    followed_new = 0

        # final words
        self.logger.info("Finished following {} users' `Followers`! xD\n"
                         .format(len(usernames)))
        # find the feature-wide action sizes by taking a difference
        already_followed = (self.already_followed - already_followed_init)
        inap_img = (self.inap_img - inap_img_init)
        liked = (self.liked_img - liked_init)
        already_liked = (self.already_liked - already_liked_init)
        commented = (self.commented - commented_init)

        # print results
        self.logger.info("Followed: {}".format(followed_all))
        self.logger.info("Already followed: {}".format(already_followed))
        self.logger.info("Not valid users: {}".format(not_valid_users))

        if interact is True:
            print('')
            # print results out of interactions
            self.logger.info("Liked: {}".format(liked))
            self.logger.info("Already Liked: {}".format(already_liked))
            self.logger.info("Commented: {}".format(commented))
            self.logger.info("Inappropriate: {}".format(inap_img))

        self.not_valid_users += not_valid_users

        return self"""

    # def follow_user_following(self,
    #                           usernames,
    #                           amount=10,
    #                           randomize=False,
    #                           interact=False,
    #                           sleep_delay=600):
    #     """ Follow the `Following` of given users """
    #     if self.aborting:
    #         return self

    #     message = "Starting to follow user `Following`.."
    #     highlight_print(Settings, self.username, message, "feature", "info", self.logger)

    #     if not isinstance(usernames, list):
    #         usernames = [usernames]

    #     followed_all = 0
    #     followed_new = 0
    #     not_valid_users = 0

    #     # hold the current global values for differentiating at the end
    #     already_followed_init = self.already_followed
    #     liked_init = self.liked_img
    #     already_liked_init = self.already_liked
    #     commented_init = self.commented
    #     inap_img_init = self.inap_img

    #     # below, can use a static value instead of from random range..
    #     relax_point = random.randint(7, 14)
    #     self.quotient_breach = False

    #     for index, user in enumerate(usernames):
    #         if self.quotient_breach:
    #             break

    #         self.logger.info("User '{}' [{}/{}]".format((user),
    #                                                     index + 1,
    #                                                     len(usernames)))
    #         try:
    #             person_list, simulated_list = get_given_user_following(
    #                 self.browser,
    #                 self.username,
    #                 user,
    #                 amount,
    #                 self.dont_include,
    #                 randomize,
    #                 self.blacklist,
    #                 self.follow_times,
    #                 self.simulation,
    #                 self.jumps,
    #                 self.logger,
    #                 self.logfolder)

    #         except (TypeError, RuntimeWarning) as err:
    #             if isinstance(err, RuntimeWarning):
    #                 self.logger.warning(
    #                     u'Warning: {} , skipping to next user'.format(err))
    #                 continue

    #             else:
    #                 self.logger.error(
    #                     'Sorry, an error occurred: {}'.format(err))
    #                 self.aborting = True
    #                 return self

    #         print('')
    #         self.logger.info(
    #             "Grabbed {} usernames from '{}'s `Following` to do following\n"
    #             .format(len(person_list), user))

    #         followed_personal = 0
    #         simulated_unfollow = 0

    #         for index, person in enumerate(person_list):
    #             if self.quotient_breach:
    #                 self.logger.warning(
    #                     "--> Follow quotient reached its peak!"
    #                     "\t~leaving Follow-User-Following activity\n")
    #                 break

    #             self.logger.info(
    #                 "Ongoing Follow [{}/{}]: now following '{}'..."
    #                 .format(index + 1, len(person_list), person)
    #             )

    #             validation, details = self.validate_user_call(person)
    #             if validation is not True:
    #                 self.logger.info(details)
    #                 not_valid_users += 1

    #                 if person in simulated_list:
    #                     self.logger.warning(
    #                         "--> Simulated Unfollow {}:"
    #                         " unfollowing '{}' due to mismatching "
    #                         "validation...\n"
    #                         .format(simulated_unfollow + 1, person))

    #                     unfollow_state, msg = unfollow_user(
    #                         self.browser,
    #                         "profile",
    #                         self.username,
    #                         person,
    #                         None,
    #                         None,
    #                         self.relationship_data,
    #                         self.logger,
    #                         self.logfolder)
    #                     if unfollow_state is True:
    #                         simulated_unfollow += 1
    #                 # skip the [non-validated] user
    #                 continue

    #             # go ahead and follow, then interact (if any)
    #             with self.feature_in_feature("follow_by_list", False):
    #                 followed = self.follow_by_list(person,
    #                                                self.follow_times,
    #                                                sleep_delay,
    #                                                interact)
    #             sleep(1)

    #             if followed > 0:
    #                 followed_all += 1
    #                 followed_new += 1
    #                 followed_personal += 1

    #             self.logger.info("Follow per user: {}  |  Total Follow: {}\n"
    #                              .format(followed_personal, followed_all))

    #             # take a break after a good following
    #             if followed_new >= relax_point:
    #                 delay_random = random.randint(
    #                     ceil(sleep_delay * 0.85),
    #                     ceil(sleep_delay * 1.14))
    #                 sleep_time = ("{} seconds".format(delay_random) if
    #                               delay_random < 60 else
    #                               "{} minutes".format(truncate_float(
    #                                   delay_random / 60, 2)))
    #                 self.logger.info(
    #                     "------=>  Followed {} new users ~sleeping about {}\n"
    #                     .format(followed_new, sleep_time))
    #                 sleep(delay_random)
    #                 relax_point = random.randint(7, 14)
    #                 followed_new = 0

    #     # final words
    #     self.logger.info("Finished following {} users' `Following`! xD\n"
    #                      .format(len(usernames)))

    #     # find the feature-wide action sizes by taking a difference
    #     already_followed = (self.already_followed - already_followed_init)
    #     inap_img = (self.inap_img - inap_img_init)
    #     liked = (self.liked_img - liked_init)
    #     already_liked = (self.already_liked - already_liked_init)
    #     commented = (self.commented - commented_init)

    #     # print results
    #     self.logger.info("Followed: {}".format(followed_all))
    #     self.logger.info("Already followed: {}".format(already_followed))
    #     self.logger.info("Not valid users: {}".format(not_valid_users))

    #     if interact is True:
    #         print('')
    #         # print results out of interactions
    #         self.logger.info("Liked: {}".format(liked))
    #         self.logger.info("Already Liked: {}".format(already_liked))
    #         self.logger.info("Commented: {}".format(commented))
    #         self.logger.info("Inappropriate: {}".format(inap_img))

    #     self.not_valid_users += not_valid_users

    #     return self

    # def unfollow_users(self,
    #                    amount=10,
    #                    customList=(False, [], "all"),
    #                    FacebookpyFollowed=(False, "all"),
    #                    nonFollowers=False,
    #                    allFollowing=False,
    #                    style="FIFO",
    #                    unfollow_after=None,
    #                    sleep_delay=600):
    #     """Unfollows (default) 10 users from your following list"""

    #     if self.aborting:
    #         return self

    #     message = "Starting to unfollow users.."
    #     highlight_print(Settings, self.username, message,
    #                     "feature", "info", self.logger)

    #     if unfollow_after is not None:
    #         if not python_version().startswith(('2.7', '3')):
    #             self.logger.warning(
    #                 "`unfollow_after` parameter is not"
    #                 " available for Python versions below 2.7")
    #             unfollow_after = None

    #     self.automatedFollowedPool = set_automated_followed_pool(
    #         self.username,
    #         unfollow_after,
    #         self.logger,
    #         self.logfolder)

    #     try:
    #         unfollowed = unfollow(self.browser,
    #                               self.username,
    #                               self.userid,
    #                               amount,
    #                               customList,
    #                               FacebookpyFollowed,
    #                               nonFollowers,
    #                               allFollowing,
    #                               style,
    #                               self.automatedFollowedPool,
    #                               self.relationship_data,
    #                               self.dont_include,
    #                               self.white_list,
    #                               sleep_delay,
    #                               self.jumps,
    #                               self.logger,
    #                               self.logfolder)
    #         self.logger.info(
    #             "--> Total people unfollowed : {}\n".format(unfollowed))
    #         self.unfollowed += unfollowed

    #     except Exception as exc:
    #         if isinstance(exc, RuntimeWarning):
    #             self.logger.warning(
    #                 u'Warning: {} , stopping unfollow_users'.format(exc))
    #             return self

    #         else:
    #             self.logger.error('Sorry, an error occurred: {}'.format(exc))
    #             self.aborting = True
    #             return self

    #     return self

    # def remove_follow_requests(self,
    #                            amount=200,
    #                            sleep_delay=600):
    #     """Remove user unaccepted follow requests"""

    #     if self.aborting:
    #         return self

    #     message = "Starting to get follow requests.."
    #     highlight_print(Settings, self.username,
    #                     message,
    #                     "feature",
    #                     "info",
    #                     self.logger)

    #     follow_requests = get_follow_requests(self.browser,
    #                                           amount,
    #                                           sleep_delay,
    #                                           self.logger,
    #                                           self.logfolder)

    #     unfollow_count = 0

    #     for person in follow_requests:
    #         self.logger.warning(
    #             "--> Unfollow {}/{}:"
    #             " Removing request for: '{}' "
    #             .format(unfollow_count + 1, len(follow_requests), person))

    #         unfollow_state, msg = unfollow_user(self.browser,
    #                                             "profile",
    #                                             self.username,
    #                                             person,
    #                                             None,
    #                                             None,
    #                                             self.relationship_data,
    #                                             self.logger,
    #                                             self.logfolder)

    #         if unfollow_state is True:
    #             unfollow_count += 1
    #             self.unfollowed += 1

    #     return self

    # def like_by_feed(self, **kwargs):
    #     """Like the users feed"""

    #     if self.aborting:
    #         return self

    #     for i in self.like_by_feed_generator(**kwargs):
    #         pass

    #     return self

    # def like_by_feed_generator(self,
    #                            amount=50,
    #                            randomize=False,
    #                            unfollow=False,
    #                            interact=False):
    #     """Like the users feed"""

    #     if self.aborting:
    #         return

    #     liked_img = 0
    #     already_liked = 0
    #     inap_img = 0
    #     inap_unfollow = 0
    #     commented = 0
    #     followed = 0
    #     skipped_img = 0
    #     num_of_search = 0
    #     not_valid_users = 0
    #     link_not_found_loop_error = 0

    #     history = []
    #     self.quotient_breach = False

    #     while liked_img < amount:
    #         if self.quotient_breach:
    #             break

    #         try:
    #             # Gets another load of links to be tested
    #             links = get_links_from_feed(self.browser,
    #                                         amount,
    #                                         num_of_search,
    #                                         self.logger)

    #             if len(links) > 0:
    #                 link_not_found_loop_error = 0

    #             if len(links) == 0:
    #                 link_not_found_loop_error += 1
    #                 if link_not_found_loop_error >= 10:
    #                     self.logger.warning(
    #                         "Loop error, 0 links"
    #                         " for 10 times consecutively, exit loop")
    #                     break

    #         except NoSuchElementException:
    #             self.logger.warning('Too few images, aborting')
    #             self.aborting = True
    #             return

    #         num_of_search += 1

    #         for i, link in enumerate(links):
    #             if liked_img == amount:
    #                 break

    #             if (self.jumps["consequent"]["likes"]
    #                     >= self.jumps["limit"]["likes"]):
    #                 self.logger.warning("--> Like quotient reached its peak!"
    #                                     "\t~leaving Like-By-Feed activity\n")
    #                 self.quotient_breach = True
    #                 # reset jump counter after a breach report
    #                 self.jumps["consequent"]["likes"] = 0
    #                 break

    #             if randomize and random.choice([True, False]):
    #                 self.logger.warning('Post Randomly Skipped...\n')
    #                 skipped_img += 1
    #                 continue
    #             else:
    #                 if link in history:
    #                     self.logger.info('This link has already '
    #                                      'been visited: {}'
    #                                      .format(link))
    #                     continue
    #                 else:
    #                     self.logger.info('New link found...')
    #                     history.append(link)
    #                     self.logger.info('[{} posts liked /{} amount]'
    #                                      .format(liked_img, amount))
    #                     self.logger.info(link)

    #                     try:
    #                         (inappropriate, user_name,
    #                          is_video, reason, scope) = check_link(
    #                             self.browser,
    #                             link,
    #                             self.dont_like,
    #                             self.mandatory_words,
    #                             self.mandatory_language,
    #                             self.is_mandatory_character,
    #                             self.mandatory_character,
    #                             self.check_character_set,
    #                             self.ignore_if_contains,
    #                             self.logger)

    #                         if not inappropriate and self.delimit_liking:
    #                             self.liking_approved = verify_liking(
    #                                 self.browser,
    #                                 self.max_likes,
    #                                 self.min_likes,
    #                                 self.logger)
    #                         if not inappropriate and self.liking_approved:
    #                             # validate user
    #                             validation, details = self.validate_user_call(
    #                                 user_name)
    #                             if validation is not True:
    #                                 self.logger.info(details)
    #                                 not_valid_users += 1
    #                                 continue
    #                             else:
    #                                 web_address_navigator( self.browser, link, Settings)

    #                             # try to like
    #                             like_state, msg = like_image(self.browser,
    #                                                          user_name,
    #                                                          self.blacklist,
    #                                                          self.logger,
    #                                                          self.logfolder,
    #                                                          Settings)

    #                             if like_state is True:
    #                                 liked_img += 1
    #                                 # reset jump counter after a successful
    #                                 # like
    #                                 self.jumps["consequent"]["likes"] = 0

    #                                 checked_img = True
    #                                 temp_comments = []

    #                                 commenting = random.randint(
    #                                     0, 100) <= self.comment_percentage
    #                                 following = random.randint(
    #                                     0, 100) <= self.follow_percentage

    #                                 if (self.use_clarifai and
    #                                         (following or commenting)):
    #                                     try:
    #                                         (checked_img,
    #                                          temp_comments,
    #                                          clarifai_tags) = \
    #                                             self.query_clarifai()

    #                                     except Exception as err:
    #                                         self.logger.error(
    #                                             'Image check error:'
    #                                             ' {}'.format(err))

    #                                 # commenting
    #                                 if (self.do_comment and
    #                                         user_name not in
    #                                         self.dont_include and
    #                                         checked_img and
    #                                         commenting):
    #                                     if self.delimit_commenting:
    #                                         (self.commenting_approved,
    #                                          disapproval_reason) = \
    #                                             verify_commenting(
    #                                                 self.browser,
    #                                                 self.max_comments,
    #                                                 self.min_comments,
    #                                                 self.comments_mandatory_words,
    #                                                 self.logger)

    #                                     if self.commenting_approved:
    #                                         # smart commenting
    #                                         comments = \
    #                                             self.fetch_smart_comments(
    #                                                 is_video,
    #                                                 temp_comments)
    #                                         if comments:
    #                                             comment_state, \
    #                                                 msg = comment_image(
    #                                                     self.browser,
    #                                                     user_name,
    #                                                     comments,
    #                                                     self.blacklist,
    #                                                     self.logger,
    #                                                     self.logfolder,
    #                                                     Settings)
    #                                         if comment_state is True:
    #                                             commented += 1

    #                                     else:
    #                                         self.logger.info(
    #                                             disapproval_reason)

    #                                 else:
    #                                     self.logger.info('--> Not commented')
    #                                     sleep(1)

    #                                 # following
    #                                 if (self.do_follow and
    #                                         user_name not in
    #                                         self.dont_include and
    #                                         checked_img and
    #                                         following and
    #                                         not follow_restriction(
    #                                             "read", user_name,
    #                                             self.follow_times,
    #                                             self.logger)):
    #                                     follow_state, msg = follow_user(
    #                                         self.browser,
    #                                         "post",
    #                                         self.username,
    #                                         user_name,
    #                                         None,
    #                                         self.blacklist,
    #                                         self.logger,
    #                                         self.logfolder)
    #                                     if follow_state is True:
    #                                         followed += 1
    #                                 else:
    #                                     self.logger.info('--> Not following')
    #                                     sleep(1)

    #                                 # interactions (if any)
    #                                 if interact:
    #                                     self.logger.info(
    #                                         "--> User gonna be interacted: "
    #                                         "'{}'".format(user_name))

    #                                     self.like_by_users(
    #                                         user_name,
    #                                         self.user_interact_amount,
    #                                         self.user_interact_random,
    #                                         self.user_interact_media)
    #                                 # :P
    #                                 yield self

    #                             elif msg == "already liked":
    #                                 already_liked += 1

    #                             elif msg == "jumped":
    #                                 # will break the loop after
    #                                 # certain consecutive jumps
    #                                 self.jumps["consequent"]["likes"] += 1

    #                         elif inappropriate:
    #                             inap_img += 1
    #                             self.logger.info(
    #                                 "--> Image not liked: {}"
    #                                 .format(reason.encode('utf-8')))

    #                             if "Inappropriate" in reason and unfollow:
    #                                 # example of unfollowing
    #                                 # directly from a post page (faster)
    #                                 self.logger.warning(
    #                                     "--> Ongoing Unfollow {}: unfollowing"
    #                                     " '{}' due to inappropriate content..."
    #                                     .format(inap_unfollow + 1, user_name))

    #                                 unfollow_state, msg = unfollow_user(
    #                                     self.browser,
    #                                     "post",
    #                                     self.username,
    #                                     user_name,
    #                                     None,
    #                                     None,
    #                                     self.relationship_data,
    #                                     self.logger,
    #                                     self.logfolder)

    #                                 if unfollow_state is True:
    #                                     inap_unfollow += 1

    #                     except NoSuchElementException as err:
    #                         self.logger.error('Invalid Page: {}'.format(err))

    #     self.logger.info('Liked: {}'.format(liked_img))
    #     self.logger.info('Already Liked: {}'.format(already_liked))
    #     self.logger.info('Commented: {}'.format(commented))
    #     self.logger.info('Followed: {}'.format(followed))
    #     self.logger.info('Inappropriate: {}'.format(inap_img))
    #     self.logger.info('Not valid users: {}'.format(not_valid_users))
    #     self.logger.info('Randomly Skipped: {}\n'.format(skipped_img))

    #     self.liked_img += liked_img
    #     self.already_liked += already_liked
    #     self.commented += commented
    #     self.followed += followed
    #     self.inap_img += inap_img
    #     self.not_valid_users += not_valid_users

    #     return

    # def set_dont_unfollow_active_users(self,
    #                                    enabled=False,
    #                                    posts=4,
    #                                    boundary=500):
    #     """Prevents unfollow followers who have liked one of
    #     your latest X posts"""

    #     if self.aborting:
    #         return

    #     # do nothing
    #     if not enabled:
    #         return

    #     # list of users who liked our media
    #     active_users = get_active_users(self.browser,
    #                                     self.username,
    #                                     posts,
    #                                     boundary,
    #                                     self.logger,
    #                                     Selectors)

    #     # include active user to not unfollow list
    #     self.dont_include.update(active_users)

    # def set_blacklist(self, enabled, campaign):
    #     """
    #      Enable/disable blacklist. If enabled, adds users to a blacklist
    #     after interact with and adds users to dont_include list
    #     """

    #     if enabled is False:
    #         self.dont_include = self.white_list
    #         return

    #     self.blacklist['enabled'] = True
    #     self.blacklist['campaign'] = campaign

    #     try:
    #         with open('{}blacklist.csv'.format(self.logfolder), 'r') \
    #                 as blacklist:
    #             reader = csv.DictReader(blacklist)
    #             for row in reader:
    #                 if row['campaign'] == campaign:
    #                     self.dont_include.add(row['username'])
    #     # except:
    #     except Exception:
    #         self.logger.info('Campaign {} first run'.format(campaign))

    # def grab_followers(self,
    #                    username=None,
    #                    userid=None,
    #                    amount=None,
    #                    live_match=False,
    #                    store_locally=True):
    #     """
    #      Gets and returns `followers` information of given user
    #     in desired amount, also, saves locally
    #     """

    #     message = "Starting to get the `Followers` data.."
    #     highlight_print(Settings, self.username, message, "feature", "info", self.logger)

    #     if username is None:
    #         self.logger.warning(
    #             "Please provide a username to grab `Followers` data"
    #             "  ~e.g. your own username or somebody else's")
    #         return self

    #     elif amount is None:
    #         self.logger.warning("Please put amount to grab `Followers` data")
    #         return self

    #     elif amount != "full" and \
    #             (type(amount) != int or (
    #             (type(amount) == int and amount <= 0))):
    #         self.logger.info("Please provide a valid amount bigger than"
    #                          " zero (0) to grab `Followers` data")
    #         return self

    #     # Get `followers` data
    #     grabbed_followers = get_followers(self.browser,
    #                                       username,
    #                                       userid,
    #                                       amount,
    #                                       self.relationship_data,
    #                                       live_match,
    #                                       store_locally,
    #                                       self.logger,
    #                                       self.logfolder)
    #     return grabbed_followers

    # def grab_following(self,
    #                    username=None,
    #                    amount=None,
    #                    live_match=False,
    #                    store_locally=True):
    #     """
    #      Gets and returns `following` information of given user
    #     in desired amount, also, saves locally
    #     """

    #     message = "Starting to get the `Following` data.."
    #     highlight_print(Settings, self.username, message, "feature", "info", self.logger)

    #     if username is None:
    #         self.logger.warning(
    #             "Please provide a username to grab `Following` data"
    #             "  ~e.g. your own username or somebody else's")
    #         return self

    #     elif amount is None:
    #         self.logger.warning("Please put amount to grab `Following` data")
    #         return self

    #     elif amount != "full" and \
    #             (type(amount) != int or (
    #             (type(amount) == int and amount <= 0))):
    #         self.logger.info("Please provide a valid amount bigger than"
    #                          " zero (0) to grab `Following` data")
    #         return self

    #     # get `following` data
    #     grabbed_following = get_following(self.browser,
    #                                       username,
    #                                       userid,
    #                                       amount,
    #                                       self.relationship_data,
    #                                       live_match,
    #                                       store_locally,
    #                                       self.logger,
    #                                       self.logfolder)
    #     return grabbed_following

    # def pick_unfollowers(self,
    #                      username=None,
    #                      compare_by="latest",
    #                      compare_track="first",
    #                      live_match=False,
    #                      store_locally=True,
    #                      print_out=True):
    #     """
    #      Compares the `followers` stored in a latest local
    #     copy against either lively generated data or previous
    #     local copy and returns absent followers
    #     """

    #     message = "Starting to pick Unfollowers of {}..".format(username)
    #     highlight_print(Settings, self.username, message, "feature", "info", self.logger)

    #     # get all and active Unfollowers
    #     all_unfollowers, active_unfollowers = get_unfollowers(
    #         self.browser,
    #         username,
    #         compare_by,
    #         compare_track,
    #         self.relationship_data,
    #         live_match,
    #         store_locally,
    #         print_out,
    #         self.logger,
    #         self.logfolder)

    #     return all_unfollowers, active_unfollowers

    # def pick_nonfollowers(self,
    #                       username=None,
    #                       live_match=False,
    #                       store_locally=True):
    #     """ Returns Nonfollowers data of a given user """

    #     message = "Starting to pick Nonfollowers of {}..".format(username)
    #     highlight_print(Settings, self.username, message, "feature", "info", self.logger)

    #     # get Nonfollowers
    #     nonfollowers = get_nonfollowers(self.browser,
    #                                     username,
    #                                     self.relationship_data,
    #                                     live_match,
    #                                     store_locally,
    #                                     self.logger,
    #                                     self.logfolder)

    #     return nonfollowers

    # def pick_fans(self,
    #               username=None,
    #               live_match=False,
    #               store_locally=True):
    #     """
    #      Returns Fans data- all of the usernames who do follow
    #     the user WHOM user itself do not follow back
    #     """

    #     message = "Starting to pick Fans of {}..".format(username)
    #     highlight_print(Settings, self.username, message, "feature", "info", self.logger)

    #     # get Fans
    #     fans = get_fans(self.browser,
    #                     username,
    #                     self.relationship_data,
    #                     live_match,
    #                     store_locally,
    #                     self.logger,
    #                     self.logfolder)

    #     return fans

    # def pick_mutual_following(self,
    #                           username=None,
    #                           live_match=False,
    #                           store_locally=True):
    #     """
    #      Returns Mutual Following data- all of the usernames who
    #     do follow the user WHOM user itself also do follow back
    #     """

    #     message = "Starting to pick Mutual Following of {}..".format(username)
    #     highlight_print(Settings, self.username, message, "feature", "info", self.logger)

    #     # get Mutual Following
    #     mutual_following = get_mutual_following(self.browser,
    #                                             username,
    #                                             self.relationship_data,
    #                                             live_match,
    #                                             store_locally,
    #                                             self.logger,
    #                                             self.logfolder)

    #     return mutual_following

    def end(self):
        """Closes the current session"""

        # IS_RUNNING = False
        close_browser(self.browser, False, self.logger)

        with interruption_handler():
            # close virtual display
            if self.nogui:
                self.display.stop()

            # write useful information
            dump_follow_restriction(self.username,
                                    self.logger,
                                    self.logfolder)
            # dump_record_activity(self.username,
            #                      self.logger,
            #                      self.logfolder,
            #                      Settings)

            with open('{}followed.txt'.format(self.logfolder), 'w') \
                    as followFile:
                followFile.write(str(self.followed))

            # output live stats before leaving

            message = "Session ended!"
            highlight_print(Settings, self.username, message, "end", "info", self.logger)
            print("\n\n")

    # def follow_by_tags(self,
    #                    tags=None,
    #                    amount=50,
    #                    skip_top_posts=True,
    #                    use_smart_hashtags=False,
    #                    randomize=False,
    #                    media=None):
    #     if self.aborting:
    #         return self

    #     inap_img = 0
    #     followed = 0
    #     not_valid_users = 0

    #     # if smart hashtag is enabled
    #     if use_smart_hashtags is True and self.smart_hashtags is not []:
    #         print('Using smart hashtags')
    #         tags = self.smart_hashtags

    #     # deletes white spaces in tags
    #     tags = [tag.strip() for tag in tags]
    #     tags = tags or []
    #     self.quotient_breach = False

    #     for index, tag in enumerate(tags):
    #         if self.quotient_breach:
    #             break

    #         self.logger.info('Tag [{}/{}]'.format(index + 1, len(tags)))
    #         self.logger.info('--> {}'.format(tag.encode('utf-8')))

    #         try:
    #             links = get_links_for_tag(self.browser,
    #                                       tag,
    #                                       amount,
    #                                       skip_top_posts,
    #                                       randomize,
    #                                       media,
    #                                       self.logger)
    #         except NoSuchElementException:
    #             self.logger.info('Too few images, skipping this tag')
    #             continue

    #         for i, link in enumerate(links):
    #             if (self.jumps["consequent"]["follows"]
    #                     >= self.jumps["limit"]["follows"]):
    #                 self.logger.warning("--> Follow quotient reached its peak!"
    #                                     "\t~leaving Follow-By-Tags activity\n")
    #                 self.quotient_breach = True
    #                 # reset jump counter after a breach report
    #                 self.jumps["consequent"]["follows"] = 0
    #                 break

    #             self.logger.info('[{}/{}]'.format(i + 1, len(links)))
    #             self.logger.info(link)

    #             try:
    #                 inappropriate, user_name, is_video, reason, scope = (
    #                     check_link(self.browser,
    #                                link,
    #                                self.dont_like,
    #                                self.mandatory_words,
    #                                self.mandatory_language,
    #                                self.is_mandatory_character,
    #                                self.mandatory_character,
    #                                self.check_character_set,
    #                                self.ignore_if_contains,
    #                                self.logger)
    #                 )

    #                 if not inappropriate:
    #                     # validate user
    #                     validation, details = self.validate_user_call(
    #                         user_name)
    #                     if validation is not True:
    #                         self.logger.info(details)
    #                         not_valid_users += 1
    #                         continue
    #                     else:
    #                         web_address_navigator( self.browser, link, Settings)

    #                     # try to follow
    #                     follow_state, msg = follow_user(self.browser,
    #                                                     "post",
    #                                                     self.username,
    #                                                     user_name,
    #                                                     None,
    #                                                     self.blacklist,
    #                                                     self.logger,
    #                                                     self.logfolder)
    #                     if follow_state is True:
    #                         followed += 1
    #                         # reset jump counter after a successful follow
    #                         self.jumps["consequent"]["follows"] = 0

    #                     elif msg == "jumped":
    #                         # will break the loop after certain consecutive
    #                         # jumps
    #                         self.jumps["consequent"]["follows"] += 1

    #                 else:
    #                     self.logger.info(
    #                         '--> User not followed: {}'.format(reason))
    #                     inap_img += 1

    #             except NoSuchElementException as err:
    #                 self.logger.error('Invalid Page: {}'.format(err))

    #     self.logger.info('Followed: {}'.format(followed))
    #     self.logger.info('Inappropriate: {}'.format(inap_img))
    #     self.logger.info('Not valid users: {}\n'.format(not_valid_users))

    #     self.followed += followed
    #     self.inap_img += inap_img
    #     self.not_valid_users += not_valid_users

    #     return self

    # def interact_by_URL(self,
    #                     urls=[],
    #                     randomize=False,
    #                     interact=False):
    #     """ Interact on posts at given URLs """

    #     if self.aborting:
    #         return self

    #     message = "Starting to interact by given URLs.."
    #     highlight_print(Settings, self.username, message, "feature", "info", self.logger)

    #     if not isinstance(urls, list):
    #         urls = [urls]

    #     if randomize is True:
    #         random.shuffle(urls)

    #     liked_img = 0
    #     already_liked = 0
    #     inap_img = 0
    #     commented = 0
    #     followed = 0
    #     not_valid_users = 0

    #     for index, url in enumerate(urls):
    #         if (self.jumps["consequent"]["likes"]
    #                 >= self.jumps["limit"]["likes"]):
    #             self.logger.warning("--> Like quotient reached its peak!"
    #                                 "\t~leaving Interact-By-URL activity\n")
    #             # reset jump counter before breaking the loop
    #             self.jumps["consequent"]["likes"] = 0
    #             # we have not used `quotient_breach` here
    #             # cos this method has just one iterator
    #             break

    #         if "https://www.facebook.com/p/" not in url:
    #             url = "https://www.facebook.com/p/" + url

    #         self.logger.info('URL [{}/{}]'.format(index + 1, len(urls)))
    #         self.logger.info('--> {}'.format(url.encode('utf-8')))

    #         try:
    #             inappropriate, user_name, is_video, reason, scope = (
    #                 check_link(self.browser,
    #                            url,
    #                            self.dont_like,
    #                            self.mandatory_words,
    #                            self.mandatory_language,
    #                            self.is_mandatory_character,
    #                            self.mandatory_character,
    #                            self.check_character_set,
    #                            self.ignore_if_contains,
    #                            self.logger))

    #             if not inappropriate and self.delimit_liking:
    #                 self.liking_approved = verify_liking(self.browser,
    #                                                      self.max_likes,
    #                                                      self.min_likes,
    #                                                      self.logger)

    #             if not inappropriate and self.liking_approved:
    #                 # validate user
    #                 validation, details = self.validate_user_call(user_name)
    #                 if validation is not True:
    #                     self.logger.info(details)
    #                     not_valid_users += 1
    #                     continue
    #                 else:
    #                     web_address_navigator( self.browser, url)

    #                 # try to like
    #                 like_state, msg = like_image(self.browser,
    #                                              user_name,
    #                                              self.blacklist,
    #                                              self.logger,
    #                                              self.logfolder,
    #                                              Settings)

    #                 if like_state is True:
    #                     liked_img += 1
    #                     # reset jump counter after a successful like
    #                     self.jumps["consequent"]["likes"] = 0

    #                     checked_img = True
    #                     temp_comments = []

    #                     commenting = (random.randint(0, 100) <=
    #                                   self.comment_percentage)
    #                     following = (random.randint(0, 100) <=
    #                                  self.follow_percentage)

    #                     if self.use_clarifai and (following or commenting):
    #                         try:
    #                             (checked_img,
    #                              temp_comments,
    #                              clarifai_tags) = self.query_clarifai()

    #                         except Exception as err:
    #                             self.logger.error(
    #                                 'Image check error: {}'.format(err))

    #                     if (self.do_comment and
    #                             user_name not in self.dont_include and
    #                             checked_img and
    #                             commenting):

    #                         if self.delimit_commenting:
    #                             (self.commenting_approved,
    #                              disapproval_reason) = verify_commenting(
    #                                 self.browser,
    #                                 self.max_comments,
    #                                 self.min_comments,
    #                                 self.comments_mandatory_words,
    #                                 self.logger)
    #                         if self.commenting_approved:
    #                             # smart commenting
    #                             comments = \
    #                                 self.fetch_smart_comments(is_video,
    #                                                           temp_comments)
    #                             if comments:
    #                                 comment_state, msg = comment_image(
    #                                     self.browser,
    #                                     user_name,
    #                                     comments,
    #                                     self.blacklist,
    #                                     self.logger,
    #                                     self.logfolder,
    #                                     Settings)

    #                                 if comment_state is True:
    #                                     commented += 1
    #                         else:
    #                             self.logger.info(disapproval_reason)

    #                     else:
    #                         self.logger.info('--> Not commented')
    #                         sleep(1)

    #                     if (self.do_follow and
    #                             user_name not in self.dont_include and
    #                             checked_img and following and
    #                             not follow_restriction("read",
    #                                                    user_name,
    #                                                    self.follow_times,
    #                                                    self.logger)):
    #                         follow_state, msg = follow_user(
    #                             self.browser,
    #                             "post",
    #                             self.username,
    #                             user_name,
    #                             None,
    #                             self.blacklist,
    #                             self.logger,
    #                             self.logfolder)

    #                         if follow_state is True:
    #                             followed += 1
    #                     else:
    #                         self.logger.info('--> Not following')
    #                         sleep(1)

    #                     # check if interaction is expected
    #                     if interact is True:
    #                         do_interact = (random.randint(0, 100)
    #                                        <= self.user_interact_percentage)
    #                         # do interactions if any
    #                         if do_interact and self.user_interact_amount > 0:
    #                             self.interact_by_users(
    #                                 user_name,
    #                                 self.user_interact_amount,
    #                                 self.user_interact_random,
    #                                 self.user_interact_media)

    #                 elif msg == "already liked":
    #                     already_liked += 1

    #                 elif msg == "jumped":
    #                     # will break the loop after certain consecutive jumps
    #                     self.jumps["consequent"]["likes"] += 1

    #             else:
    #                 self.logger.info(
    #                     '--> Image not liked: {}'.format(
    #                         reason.encode('utf-8')))
    #                 inap_img += 1

    #         except NoSuchElementException as err:
    #             self.logger.error('Invalid Page: {}'.format(err))

    #     self.logger.info('Liked: {}'.format(liked_img))
    #     self.logger.info('Already Liked: {}'.format(already_liked))
    #     self.logger.info('Commented: {}'.format(commented))
    #     self.logger.info('Followed: {}'.format(followed))
    #     self.logger.info('Inappropriate: {}'.format(inap_img))
    #     self.logger.info('Not valid users: {}\n'.format(not_valid_users))

    #     self.liked_img += liked_img
    #     self.already_liked += already_liked
    #     self.commented += commented
    #     self.followed += followed
    #     self.inap_img += inap_img
    #     self.not_valid_users += not_valid_users

    #     return self

    # def set_quota_supervisor(self,
    #                          Settings,
    #                          enabled=False,
    #                          sleep_after=[],
    #                          sleepyhead=False,
    #                          stochastic_flow=False,
    #                          notify_me=False,
    #                          peak_likes=(None, None),
    #                          peak_comments=(None, None),
    #                          peak_follows=(None, None),
    #                          peak_unfollows=(None, None),
    #                          peak_server_calls=(None, None)):
    #     """
    #      Sets aside QS configuration ANY time in a session
    #     """
    #     # take a reference of the global configuration
    #     configuration = Settings.QS_config

    #     # strong type checking on peaks entered
    #     peak_values_combined = [peak_likes, peak_comments, peak_follows,
    #                             peak_unfollows, peak_server_calls]
    #     peaks_are_tuple = all(type(item) is tuple for
    #                           item in peak_values_combined)

    #     if peaks_are_tuple:
    #         peak_values_merged = [i for sub in peak_values_combined
    #                               for i in sub]
    #         integers_filtered = filter(lambda e: isinstance(e, int),
    #                                    peak_values_merged)

    #         peaks_are_provided = all(len(item) == 2 for
    #                                  item in peak_values_combined)
    #         peaks_are_valid = all(type(item) is int or type(item) is
    #                               type(None) for item in peak_values_merged)
    #         peaks_are_good = all(item >= 0 for item in integers_filtered)

    #     # set QS if peak values are eligible
    #     if (peaks_are_tuple and
    #             peaks_are_provided and
    #             peaks_are_valid and
    #             peaks_are_good):

    #         peaks = {"likes": {"hourly": peak_likes[0],
    #                            "daily": peak_likes[1]},
    #                  "comments": {"hourly": peak_comments[0],
    #                               "daily": peak_comments[1]},
    #                  "follows": {"hourly": peak_follows[0],
    #                              "daily": peak_follows[1]},
    #                  "unfollows": {"hourly": peak_unfollows[0],
    #                                "daily": peak_unfollows[1]},
    #                  "server_calls": {"hourly": peak_server_calls[0],
    #                                   "daily": peak_server_calls[1]}}

    #         if not isinstance(sleep_after, list):
    #             sleep_after = [sleep_after]

    #         rt = time.time()
    #         latesttime = {"hourly": rt, "daily": rt}
    #         orig_peaks = deepcopy(peaks)  # original peaks always remain static
    #         stochasticity = {"enabled": stochastic_flow,
    #                          "latesttime": latesttime,
    #                          "original_peaks": orig_peaks}

    #         if (platform.startswith("win32") and
    #                 python_version() < "2.7.15"):
    #             # UPDATE ME: remove this block once plyer is
    #             # verified to work on [very] old versions of Python 2
    #             notify_me = False

    #         # update QS configuration with the fresh settings
    #         configuration.update({"state": enabled,
    #                               "sleep_after": sleep_after,
    #                               "sleepyhead": sleepyhead,
    #                               "stochasticity": stochasticity,
    #                               "notify": notify_me,
    #                               "peaks": peaks})

    #     else:
    #         # turn off QS for the rest of the session
    #         # since peak values are ineligible
    #         configuration.update(state="False")

    #         # user should be warned only if has had QS turned on
    #         if enabled is True:
    #             self.logger.warning("Quota Supervisor: peak rates are misfit! "
    #                                 "Please use supported formats."
    #                                 "\t~disabled QS")

    @contextmanager
    def feature_in_feature(self, feature, validate_users):
        """
         Use once a host feature calls a guest
        feature WHERE guest needs special behaviour(s)
        """

        try:
            # add the guest which is gonna be used by the host :)
            self.internal_usage[feature] = {"validate": validate_users}
            yield

        finally:
            # remove the guest just after using it
            self.internal_usage.pop(feature)

    def live_report(self):
        """ Report live sessional statistics """

        print('')

        stats = [self.liked_img, self.already_liked,
                 self.commented,
                 self.followed, self.already_followed,
                 self.unfollowed,
                 self.inap_img,
                 self.not_valid_users]

        sessional_run_time = self.run_time()
        run_time_info = ("{} seconds".format(sessional_run_time) if
                         sessional_run_time < 60 else
                         "{} minutes".format(truncate_float(
                             sessional_run_time / 60, 2)) if
                         sessional_run_time < 3600 else
                         "{} hours".format(truncate_float(
                             sessional_run_time / 60 / 60, 2)))
        run_time_msg = "[Session lasted {}]".format(run_time_info)

        if any(stat for stat in stats):
            self.logger.info(
                "Sessional Live Report:\n"
                "\t|> LIKED {} images  |  ALREADY LIKED: {}\n"
                "\t|> COMMENTED on {} images\n"
                "\t|> FOLLOWED {} users  |  ALREADY FOLLOWED: {}\n"
                "\t|> UNFOLLOWED {} users\n"
                "\t|> LIKED {} comments\n"
                "\t|> REPLIED to {} comments\n"
                "\t|> INAPPROPRIATE images: {}\n"
                "\t|> NOT VALID users: {}\n"
                "\n{}"
                .format(self.liked_img,
                        self.already_liked,
                        self.commented,
                        self.followed,
                        self.already_followed,
                        self.unfollowed,
                        self.liked_comments,
                        self.replied_to_comments,
                        self.inap_img,
                        self.not_valid_users,
                        run_time_msg))
        else:
            self.logger.info("Sessional Live Report:\n"
                             "\t|> No any statistics to show\n"
                             "\n{}"
                             .format(run_time_msg))

    # def set_do_reply_to_comments(self,
    #                              enabled=False,
    #                              percentage=0):
    #     """ Define if the comments on posts should be replied """

    #     self.do_reply_to_comments = enabled
    #     self.reply_to_comments_percent = percentage

    #     return self

    # def set_comment_replies(self,
    #                         replies=[],
    #                         media=None):
    #     """ Set the replies to comments """

    #     if not replies:
    #         self.logger.info(
    #             "Please, provide some comment replies for use next time.")
    #         self.comment_replies = None
    #         self.photo_comment_replies = None
    #         self.video_comment_replies = None

    #         return self

    #     if media in ["Photo", "Video"]:
    #         attr = "{}_comment_replies".format(media.lower())
    #         setattr(self, attr, replies)

    #     else:
    #         if media is not None:
    #             self.logger.warning("Unkown media type set at"
    #                                 " comment replies! Treating as 'any'.")

    #         self.comment_replies = replies

    # def set_use_meaningcloud(self,
    #                          enabled=False,
    #                          license_key=None,
    #                          polarity="P",
    #                          agreement=None,
    #                          subjectivity=None,
    #                          confidence=100):
    #     """ Set MeaningCloud Sentiment Analysis API configuration """

    #     if license_key is None:
    #         license_key = os.environ.get("MEANINGCLOUD_LIC_KEY")

    #     if polarity.upper() not in ['P', "P+", "NEU", 'N', "N+"]:
    #         self.logger.info("Oh no! Please provide a valid polarity "
    #                          "score tag for MeaningCloud"
    #                          "\t~service will not operate")
    #         polarity = None

    #     if enabled and license_key and polarity:
    #         Settings.meaningcloud_config.update(
    #             enabled=enabled,
    #             license_key=license_key,
    #             score_tag=polarity.upper(),
    #             agreement=agreement.upper() if agreement else None,
    #             subjectivity=subjectivity.upper() if subjectivity else None,
    #             confidence=int(confidence) if confidence else None)

    #     else:
    #         # turn off MeaningCloud service if not enabled or wrongly
    #         # configured
    #         Settings.meaningcloud_config.update(enabled=False)

    # def set_use_yandex(self,
    #                    enabled=False,
    #                    API_key=None,
    #                    match_language=False,
    #                    language_code="en"):
    #     """ Set Yandex Translate API configuration """

    #     if API_key is None:
    #         API_key = os.environ.get("YANDEX_API_KEY")

    #     if enabled and API_key:
    #         Settings.yandex_config.update(
    #             enabled=enabled,
    #             API_key=API_key)

    #         if match_language is True and language_code:
    #             supported_langs = yandex_supported_languages()

    #             if (not supported_langs or
    #                     language_code.lower() not in supported_langs):
    #                 msg = ("Oh no! Failed to get the list of supported"
    #                        " languages by Yandex Translate :("
    #                        if not supported_langs else
    #                        "Oh no! The language with '{}' code is not"
    #                        " supported by Yandex Translate :/"
    #                        .format(language_code))
    #                 self.logger.info("{}\t~text language won't be matched"
    #                                  .format(msg))
    #                 match_language = False

    #         Settings.yandex_config.update(
    #             match_language=match_language if language_code else False,
    #             language_code=language_code.lower() if language_code else None)

    #     else:
    #         # turn off Yandex service if not enabled or wrongly configured
    #         Settings.yandex_config.update(enabled=False)

    # def interact_by_comments(self,
    #                          usernames=None,
    #                          posts_amount=10,
    #                          comments_per_post=1,
    #                          reply=False,
    #                          interact=False,
    #                          randomize=False,
    #                          media=None):
    #     """
    #      Like comments of people on posts, reply to them
    #     and also interact with those commenters
    #     """

    #     message = "Starting to interact by comments.."
    #     highlight_print(Settings, self.username, message, "feature", "info", self.logger)

    #     if not isinstance(usernames, list):
    #         usernames = [usernames]

    #     if media not in ["Photo", "Video", None]:
    #         self.logger.warning("Unkown media type- '{}' set at"
    #                             " Interact-By-Comments!\t~treating as any.."
    #                             .format(media))
    #         media = None

    #     # hold the current global values for differentiating at the end
    #     liked_init = self.liked_img
    #     already_liked_init = self.already_liked
    #     liked_comments_init = self.liked_comments
    #     commented_init = self.commented
    #     replied_to_comments_init = self.replied_to_comments
    #     followed_init = self.followed
    #     already_followed_init = self.already_followed
    #     inap_img_init = self.inap_img
    #     not_valid_users_init = self.not_valid_users

    #     overall_posts_count = 0
    #     self.quotient_breach = False
    #     like_failures_tracker = {"consequent": {"post_likes": 0,
    #                                             "comment_likes": 0},
    #                              "limit": {"post_likes": 5,
    #                                        "comment_likes": 10}}

    #     leave_msg = "\t~leaving Interact-By-Comments activity\n"

    #     # start the interaction!
    #     for s, username in enumerate(usernames):
    #         if self.quotient_breach:
    #             break

    #         message = "User: [{}/{}]".format(s + 1, len(usernames))
    #         highlight_print(Settings,
    #             self.username, message, "user iteration", "info", self.logger)

    #         validation, details = self.validate_user_call(username)
    #         if validation is not True:
    #             self.logger.info("--> Not a valid user: {}"
    #                              .format(details))
    #             self.not_valid_users += 1
    #             continue

    #         per_user_liked_comments = 0
    #         per_user_replied_to_comments = 0
    #         per_user_used_replies = []

    #         try:
    #             links = get_links_for_username(self.browser,
    #                                            self.username,
    #                                            username,
    #                                            posts_amount,
    #                                            self.logger,
    #                                            self.logfolder,
    #                                            randomize,
    #                                            media)
    #         except NoSuchElementException:
    #             self.logger.error("Element not found, skipping this user.")
    #             continue

    #         if links is False:
    #             continue

    #         else:
    #             if randomize:
    #                 random.shuffle(links)
    #             links = links[:posts_amount]
    #             overall_posts_count += len(links)

    #         for i, link in enumerate(links):
    #             if self.quotient_breach:
    #                 break

    #             elif (self.jumps["consequent"]["comments"]
    #                   >= self.jumps["limit"]["comments"]):
    #                 self.logger.warning(
    #                     "--> Comment quotient reached its peak!{}"
    #                     .format(leave_msg))
    #                 self.quotient_breach = True
    #                 # reset jump counter after a breach report
    #                 self.jumps["consequent"]["comments"] = 0
    #                 break

    #             elif (like_failures_tracker["consequent"]["post_likes"]
    #                   >= like_failures_tracker["limit"]["post_likes"]):
    #                 self.logger.warning(
    #                     "--> Too many failures to like posts!{}"
    #                     .format(leave_msg))
    #                 # this example shows helpful usage of
    #                 # quotient breach outside QS needs..
    #                 self.quotient_breach = True
    #                 break

    #             message = "Post: [{}/{}]".format(i + 1, len(links))
    #             highlight_print(Settings, self.username, message, "post iteration",
    #                             "info", self.logger)

    #             (inappropriate, user_name,
    #              is_video, reason, scope) = check_link(
    #                 self.browser,
    #                 link,
    #                 self.dont_like,
    #                 self.mandatory_words,
    #                 self.mandatory_language,
    #                 self.is_mandatory_character,
    #                 self.mandatory_character,
    #                 self.check_character_set,
    #                 self.ignore_if_contains,
    #                 self.logger)

    #             if inappropriate:
    #                 self.logger.info(
    #                     "--> Post not interacted. {}\n"
    #                     .format(reason.encode('utf-8')))
    #                 self.inap_img += 1
    #                 continue

    #             # go go!
    #             per_post_liked_comments = 0
    #             per_post_replied_to_comments = 0
    #             per_post_interacted_commenters = []

    #             # get comments (if any)
    #             comment_data = get_comments_on_post(self.browser,
    #                                                 self.username,
    #                                                 username,
    #                                                 comments_per_post,
    #                                                 link,
    #                                                 self.ignore_users,
    #                                                 randomize,
    #                                                 self.logger)
    #             if not comment_data:
    #                 self.logger.info("No interaction did happen.\n")
    #                 continue

    #             # like the post before interacting on comments
    #             image_like_state, msg = like_image(self.browser,
    #                                                user_name,
    #                                                self.blacklist,
    #                                                self.logger,
    #                                                self.logfolder,
    #                                                Settings)
    #             if image_like_state is True:
    #                 like_failures_tracker["consequent"]["post_likes"] = 0
    #                 self.liked_img += 1

    #             elif msg == "already liked":
    #                 self.already_liked += 1

    #             else:
    #                 self.logger.info(
    #                     "Can't interact by comments unless"
    #                     " the post is liked! :(\t~skipping this post\n")
    #                 like_failures_tracker["consequent"]["post_likes"] += 1
    #                 continue

    #             # perfect! now going to work with comments...
    #             for commenter, comment in comment_data:
    #                 if per_post_liked_comments >= comments_per_post:
    #                     break

    #                 elif (like_failures_tracker["consequent"]["comment_likes"]
    #                       >= like_failures_tracker["limit"]["comment_likes"]):
    #                     self.logger.warning(
    #                         "--> Too many failures to like comments!{}"
    #                         .format(leave_msg))
    #                     # this example shows helpful usage of
    #                     # quotient breach outside QS needs..
    #                     self.quotient_breach = True
    #                     break

    #                 # verify the comment content by sentiment analysis &
    #                 # language detection if enabled
    #                 text_analysis_state = text_analysis(comment,
    #                                                     "comment",
    #                                                     Settings,
    #                                                     self.logger)
    #                 if text_analysis_state is False:
    #                     # comment is inappropriate to be liked [and replied]
    #                     continue

    #                 # like the comment
    #                 comment_like_state, msg = like_comment(self.browser,
    #                                                        comment,
    #                                                        self.logger)
    #                 if comment_like_state is not True:
    #                     like_failures_tracker["consequent"][
    #                         "comment_likes"] += 1
    #                     continue

    #                 else:
    #                     per_post_interacted_commenters.append(commenter)
    #                     self.liked_comments += 1
    #                     per_user_liked_comments += 1
    #                     per_post_liked_comments += 1
    #                     like_failures_tracker["consequent"][
    #                         "comment_likes"] = 0

    #                     # send a reply to the comment if is appropriate
    #                     if (self.do_reply_to_comments and reply and
    #                             text_analysis_state is True):
    #                         do_reply_to_comment = (
    #                             self.reply_to_comments_percent
    #                             >= random.randint(0, 100))

    #                         comment_replies_base = (
    #                             self.comment_replies
    #                             + (self.video_comment_replies
    #                                if is_video else
    #                                self.photo_comment_replies))
    #                         # dismiss the already used replies per each user
    #                         comment_replies_base = [
    #                             reply for reply in comment_replies_base if
    #                             reply not in per_user_used_replies]

    #                         if do_reply_to_comment and comment_replies_base:
    #                             chosen_reply = random.choice(
    #                                 comment_replies_base)
    #                             # mention the commenter to make a reply :)
    #                             reply_msg = ["@{} {}".format(commenter,
    #                                                          chosen_reply)]

    #                             reply_to_comment_state, msg = comment_image(
    #                                 self.browser,
    #                                 commenter,
    #                                 reply_msg,
    #                                 self.blacklist,
    #                                 self.logger,
    #                                 self.logfolder,
    #                                 Settings)

    #                             if reply_to_comment_state is True:
    #                                 per_user_used_replies.extend(chosen_reply)
    #                                 self.replied_to_comments += 1
    #                                 self.commented += 1
    #                                 per_user_replied_to_comments += 1
    #                                 per_post_replied_to_comments += 1
    #                                 # reset jump counter after a successful
    #                                 # comment
    #                                 self.jumps["consequent"]["comments"] = 0

    #                             elif msg == "jumped":
    #                                 # will break the loop after
    #                                 # certain consecutive jumps
    #                                 self.jumps["consequent"]["comments"] += 1

    #             post_No_ending = ("st" if str(i + 1).endswith('1') else
    #                               "nd" if str(i + 1).endswith('2') else
    #                               "rd" if str(i + 1).endswith('3') else
    #                               "th" if str(i + 1).endswith('4') else '')
    #             post_No = "{}{}".format(str(i + 1), post_No_ending)

    #             # quick log after interacting on a post
    #             print('')
    #             self.logger.info("Finished interacting on {} post's comments!"
    #                              .format(post_No))
    #             self.logger.info("\tLiked comments: {}"
    #                              .format(per_post_liked_comments))
    #             self.logger.info("\tReplied to comments: {}\n"
    #                              .format(per_post_replied_to_comments))

    #             # standalone interaction with commenters whose
    #             # comment was liked on the post
    #             if interact and per_post_interacted_commenters:
    #                 with self.feature_in_feature("interact_by_users", True):
    #                     self.interact_by_users(per_post_interacted_commenters,
    #                                            self.user_interact_amount,
    #                                            self.user_interact_random,
    #                                            self.user_interact_media)

    #         # quick log after interacting with a user
    #         print('')
    #         self.logger.info(
    #             "Finished interacting on {} posts' comments of '{}'!"
    #             .format(len(links), username))
    #         self.logger.info("\tLiked comments: {}"
    #                          .format(per_user_liked_comments))
    #         self.logger.info("\tReplied to comments: {}\n"
    #                          .format(per_user_replied_to_comments))

    #     # full log after finishing whole work
    #     self.logger.info(
    #         "Finished interacting on {} posts' comments from {} users!"
    #         .format(overall_posts_count, len(usernames)))

    #     # find the feature-wide action sizes by taking a difference
    #     liked_img = (self.liked_img - liked_init)
    #     already_liked = (self.already_liked - already_liked_init)
    #     liked_comments = (self.liked_comments - liked_comments_init)
    #     replied_to_comments = (
    #         self.replied_to_comments - replied_to_comments_init)
    #     commented = ((self.commented - commented_init) - replied_to_comments)
    #     followed = (self.followed - followed_init)
    #     already_followed = (self.already_followed - already_followed_init)
    #     inap_img = (self.inap_img - inap_img_init)
    #     not_valid_users = (self.not_valid_users - not_valid_users_init)

    #     if self.liked_comments:
            # output results
            # self.logger.info("\tLiked comments: {}".format(liked_comments))
            # self.logger.info("\tReplied to comments: {}"
            #                  .format(replied_to_comments))
            # self.logger.info("\tLiked posts: {}".format(liked_img))
            # self.logger.info("\tAlready liked posts: {}".format(already_liked))
            # self.logger.info("\tCommented posts: {}".format(commented))
            # self.logger.info("\tFollowed users: {}".format(followed))
            # self.logger.info("\tAlready followed users: {}"
            #                  .format(already_followed))
            # self.logger.info("\tInappropriate posts: {}".format(inap_img))
            # self.logger.info("\tNot valid users: {}".format(not_valid_users))

    def is_mandatory_character(self, uchr):
        if self.aborting:
            return self
        try:
            return self.check_letters[uchr]
        except KeyError:
            return self.check_letters.setdefault(uchr,
                                                 self.mandatory_character in
                                                 unicodedata.name(uchr))

    def run_time(self):
        """ Get the time session lasted in seconds """

        real_time = time.time()
        run_time = (real_time - self.start_time)
        run_time = truncate_float(run_time, 2)

        return run_time

    def check_character_set(self, unistr):
        self.check_letters = {}
        if self.aborting:
            return self
        return all(self.is_mandatory_character(uchr)
                   for uchr in unistr
                   if uchr.isalpha())

@contextmanager
def smart_run(session):
    try:
        if session.login():
            yield
        else:
            print("Not proceeding as login failed")

    except (Exception, KeyboardInterrupt) as exc:
        if isinstance(exc, NoSuchElementException):
            # the problem is with a change in IG page layout
            log_file = "{}.html".format(time.strftime("%Y%m%d-%H%M%S"))
            file_path = os.path.join(gettempdir(), log_file)
            with open(file_path, "wb") as fp:
                fp.write(session.browser.page_source.encode("utf-8"))
            print("{0}\nIf raising an issue, "
                  "please also upload the file located at:\n{1}\n{0}"
                  .format('*' * 70, file_path))

        # provide full stacktrace (else than external interrupt)
        if isinstance(exc, KeyboardInterrupt):
            clean_exit("You have exited successfully.")
        else:
            raise

    finally:
        session.end()
