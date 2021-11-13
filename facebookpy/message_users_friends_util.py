import time
import traceback
from .messaging_util import open_message


def message_users_friends(browser, userid, username, logger, logfolder, message):
        browser.get("https://web.facebook.com/{}/friends".format(userid))
        time.sleep(2)
        try:
            for i in range(10):
                # self.browser.execute_script("window.scrollTo(0, " + str(1000+i*1000) + ")")
                browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)

            profile_as = browser.find_elements_by_css_selector("li > div > div > div.uiProfileBlockContent > div > div:nth-child(2) > div > a")

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

                browser.get(profile)
                open_message(browser, "profile", username, profile, None, logger, logfolder, message)

        except Exception as e:
                traceback.print_exc()
