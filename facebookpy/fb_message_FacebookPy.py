# imports
from facebookpy import FacebookPy
from facebookpy import smart_run

#from facebookpy.message_users_friends_util import message_users_friends
from .file_manager import set_workspace
from facebookpy import settings
import os
import datetime

import random


class FacebookBot:
    def __init__(self, username=None, password=None, userid=None, userlist=False, access=None, message=None, interact_users=None, friend_by_list=True, message_user_friends=None, comments=None):
        self.username = username
        self.password = password
        self.userid = userid
        self.access = access
        self.userlist = userlist
        self.message = message
        self.interact_users = interact_users
        self.friend_by_list = friend_by_list
        self.message_user_friends = message_user_friends
        self.comments = comments
# set workspace folder at desired location (default is at your home folder)

    def facebook_start(self):
        set_workspace(path=os.getcwd())#"C:\\Users\\HP"

        # get an FacebookPy session!
        session = FacebookPy(username=self.username, password=self.password, userid=self.userid, headless_browser=False)
        if datetime.date.today() < datetime.date(2021, 11, 16):

            with smart_run(session):
                """ Activity flow """
                session.login()
                # general settings
                session.set_dont_include(["friend1", "friend2", "friend3"])

                # activity
                # session.like_by_tags(["natgeo"], amount=10)

                #session.set_relationship_bounds(enabled=True, potency_ratio=None, delimit_by_numbers=True, max_followers=7500, max_following=3000, min_followers=25, min_following=25, min_posts=1)
                session.set_user_interact(amount=3, randomize=True, percentage=80,
                                        media='Photo')
                # session.set_do_like(enabled=True, percentage=90)
                #session.set_do_follow(enabled=True, percentage=40, times=1)
                #session.set_dont_like(['#politics', '[startswith', ']endswith', 'broadmatch'])

                if self.interact_users:
                    if self.message:
                        session.message_group_users(self.interact_users, self.message)
                    session.like_comment(self.interact_users, self.comments)

                """if self.message:
                    if self.userlist:
                        listing = []
                        for line in open('files\\users.txt', 'r'):
                            listing.append(line)
                        random_list = random.sample(listing, len(listing))
                        if len(random_list)<25:
                            random_list=listing
                        session.open_message_to_user(random_list, self.message)
                    else:
                        listing = []
                        for line in open('files\\default_users.txt', 'r'):
                            listing.append(line)
                        random_list = random.sample(listing, 25)
                        if len(random_list)<25:
                            random_list=listing
                        session.open_message_to_user(random_list, self.message)"""


                if self.friend_by_list:
                    """ Select users form a list of a predefined targets..."""
                    if self.userlist:
                        listing = []
                        for line in open('files\\users.txt', 'r'):
                            listing.append(line)
                        targets = listing#['christine.turel','blane.oroark.395', 'acemilia', 'JohnnyBergmanJr', 'greg.harper.718']
                        number = random.randint(len(listing)-2, len(listing))
                        random_targets = targets

                        if len(targets) <= number:
                            random_targets = targets
                        else:
                            random_targets = random.sample(targets, number)

                        session.friend_by_list(friendlist=random_targets, times=1, sleep_delay=600, interact=True)
                    else:
                        listing = []
                        for line in open('files\\default_users.txt', 'r'):
                            listing.append(line)
                        targets = listing#['christine.turel','blane.oroark.395', 'acemilia', 'JohnnyBergmanJr', 'greg.harper.718']
                        number = random.randint(15, 25)
                        random_targets = targets

                        if len(targets) <= number:
                            random_targets = targets
                        else:
                            random_targets = random.sample(targets, number)

                        session.friend_by_list(friendlist=random_targets, times=1, sleep_delay=600, interact=True)

                #session.friend('user1', daysold=365, max_pic = 100, sleep_delay=600, interact=False)
                #['christine.turel', 'acemilia', 'JohnnyBergmanJr', 'greg.harper.718']
                
                #session.follow_by_list(followlist=random_targets, times=1, sleep_delay=600, interact=True)

                #session.follow_likers(random_targets, photos_grab_amount = 2, follow_likers_per_photo = 3, randomize=True, sleep_delay=600, interact=False)


"""if __name__ == "__main__":
    FacebookBot.facebook_start()"""
