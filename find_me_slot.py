from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options

import re
import smtplib
import time
import yaml

SETTINGS_FILE = "settings.yaml"

cfg = {}
with open(SETTINGS_FILE,"r") as yamlf:
    cfg = yaml.load(yamlf, Loader=yaml.SafeLoader)

OPEN_BROWSER = cfg['OPEN_BROWSER']
CHROMEDRIVER = "./chromedriver"

MAIN_SITE = "https://instacart.com"
SHOP_SITE = "https://www.instacart.com/store/{}/info?tab=delivery"

LOGIN_BUTTON = "//button"
SITE_LOGIN_BUTTON = '//button[@type="submit"]'
EMAIL_FIELD_ID = "nextgen-authenticate.all.log_in_email"
PASSWD_FIELD_ID = "nextgen-authenticate.all.log_in_password"
DELIVERY_UNAVAIL_FIELD = '//h1'
DELIVERY_AVAIL_FIELD = '//div/div/div/div[@tabindex="-1"]'
DELIVERY_UNAVAILABLE_MSG = 'No delivery times available'
PICKUP_UNAVAILABLE_MSG = 'No pickup times available'

SHOPS = cfg['SHOPS']

INSTACART_EMAIL = cfg['INSTACART_EMAIL']
INSTACART_PASSWD = cfg['INSTACART_PASSWD']
SENDER_GMAIL_ID = cfg['SENDER_GMAIL_ID']
SENDER_GMAIL_PWD = cfg['SENDER_GMAIL_PWD']
RECEIVER_GMAIL_ID = cfg['RECEIVER_GMAIL_ID']

GMAIL_SMTP = 'smtp.gmail.com'
GMAIL_SMTP_PORT = 587

WAIT_FOR_MAIN_SITE = 5
WAIT_FOR_LOGIN_PAGE = 5
WAIT_FOR_INPUT = 2
WAIT_FOR_LOGGING_IN = 10
WAIT_FOR_NEXT_SHOP = 5
WAIT_FOR_SHOP_LOAD = 10

ROUND_WAIT_TIME = 3*60 # 3 minutes
ROUND_COUNT = 160 # Roughly 8 hours

class BrowseForMe:

    def __init__(self):
        opts = Options()
        if OPEN_BROWSER == 0:
            opts.headless = True
        self.browser = webdriver.Chrome(CHROMEDRIVER, options=opts)


    def login(self):
        self.browser.get(MAIN_SITE)
        time.sleep(WAIT_FOR_MAIN_SITE)

        login_btn = self.browser.find_element_by_xpath(LOGIN_BUTTON)
        if not login_btn:
            print("FAILED TO LOCATE LOGIN BUTTON ON MAIN PAGE")
            self.close_and_quit()
        login_btn.click()
        time.sleep(WAIT_FOR_LOGIN_PAGE)

        email_field =self.browser.find_element_by_id(EMAIL_FIELD_ID)
        if not email_field:
            print("FAILED TO LOCATE EMAIL FIELD ON LOGIN PAGE")
            self.close_and_quit()
        email_field.send_keys(INSTACART_EMAIL)
        time.sleep(WAIT_FOR_INPUT)

        passwd_field =self.browser.find_element_by_id(PASSWD_FIELD_ID)
        if not passwd_field:
            print("FAILED TO LOCATE PASSWORD FIELD ON LOGIN PAGE")
            self.close_and_quit()
        passwd_field.send_keys(INSTACART_PASSWD)
        time.sleep(WAIT_FOR_INPUT)

        login_btn =self.browser.find_element_by_xpath(SITE_LOGIN_BUTTON)
        if not login_btn:
            print("FAILED TO LOCATE LOGIN BUTTON ON MAIN PAGE")
            self.close_and_quit()
        login_btn.click()
        time.sleep(WAIT_FOR_LOGGING_IN)


    def reload_page(self,shop):
        time.sleep(WAIT_FOR_SHOP_LOAD)
        self.browser.get(SHOP_SITE.format(shop))
        time.sleep(WAIT_FOR_SHOP_LOAD)


    def check_availability(self):
        delivery_available_maybe = False
        try:
            message = \
            self.browser.find_element_by_xpath(DELIVERY_UNAVAIL_FIELD).text
        except NoSuchElementException as exception:
            # If this <h1> tag isn't available on page I am assuming there might
            # be delivery times available
            delivery_available_maybe = True
        
        # Leaving this commented block in case if we have distinguish
        # the type of unavailability No delivery / No pickups we can use it.
        # if not delivery_available_maybe:
        #     match = re.search(DELIVERY_UNAVAILABLE_MSG, message)
        #     # Some stores have pick up only(Sprouts),
        #     # check for that message as well
        #     if not match:
        #         match = re.search(PICKUP_UNAVAILABLE_MSG, message)

        #     if match:
        #         print("Not available")
        #     else:
        #         print("Delivery available")
        #     continue
        return delivery_available_maybe


    def check_times(self):
        available_elems = None
        try:
            available_elems = \
            self.browser.find_elements_by_xpath(DELIVERY_AVAIL_FIELD)
        except NoSuchElementException as exception:
            print("CANNOT GET DELIVERY TIMES, WILL TRY AGAIN")
            return None

        if not available_elems:
            print("CANNOT GET DELIVERY TIMES, WILL TRY AGAIN")
            return None

        message = ""
        for elem in available_elems:
            message += elem.text
            message += "\n"

        return message


    def send_email(self, message):
        if cfg['SENDER_GMAIL_ID'] and cfg['SENDER_GMAIL_PWD'] and \
            cfg['RECEIVER_GMAIL_ID']:
            self.email(message)


    def check_all_stores(self):
        for shop in SHOPS:
            self.reload_page(shop)

            if not self.check_availability():
                # If not available keep reload and keep checking
                continue

            message =  self.check_times()
            if not message:
                # Unable to figure out times, lets keep trying
                continue

            print(message)
            self.send_email(message)

            self.close_and_quit()


    def close_and_quit(self):
        self.browser.close()
        quit()


    def loop_till_you_shop(self):

        for round in range(ROUND_COUNT):
            self.check_all_stores()
            print("Round :", round+1)
            time.sleep(ROUND_WAIT_TIME)


    def email(self, message):
        # establishing connection to the gmail server with domain name and port. 
        # This differs with each email provider
        connection = smtplib.SMTP(GMAIL_SMTP,GMAIL_SMTP_PORT)
        
        # say hello to the server
        connection.ehlo()
        
        # starting encrypted TLS connection
        connection.starttls()
        
        # log into gmail server with your main address and password
        connection.login(SENDER_GMAIL_ID, SENDER_GMAIL_PWD)
        
        # sending mail to yourself informing you about the price of camera
        connection.sendmail(SENDER_GMAIL_ID, RECEIVER_GMAIL_ID, message)
        
        # ending connection
        connection.quit()

if __name__ == '__main__':
    browse = BrowseForMe()
    browse.login()
    browse.loop_till_you_shop()

