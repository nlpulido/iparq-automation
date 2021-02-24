import os
import time
import unittest
import logging
import re
import pandas as pd
import tkinter
from tkinter import filedialog
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.expected_conditions import element_to_be_clickable
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
  
# inherit TestCase Class and create a new test class 
class iPARQTest(unittest.TestCase):
  
    # initialization of webdriver & login information
    def setUp(self): 
        
        # Load Chrome Options & remove logging errors from command line output
        self.options = webdriver.ChromeOptions()
        self.options.add_argument("--log-level=3")
        # self.options.add_argument("--headless")
        os.environ["WDM_LOG_LEVEL"] = str(logging.WARNING)

        # Load Chrome Driver
        self.driver = webdriver.Chrome(ChromeDriverManager().install(), options=self.options)

        # Set up Constants
        self.IPARQ_ADMIN_URL = "https://admin.thepermitstore.com/?client_ID=83"
        self.PERMIT_TYPES = "https://admin.thepermitstore.com/setup/permittypes.php"
        self.PERMIT_SESSIONS = "https://admin.thepermitstore.com/setup/permitsessions.php?permission_"
        self.AFFILIATE_PORTAL = "https://admin.thepermitstore.com/setup/switch_client.php?table=switch&edit=155"

        # get the client side permit store
        self.driver.get(self.IPARQ_ADMIN_URL)

        # get driver
        browser = self.driver

        print("Please login to your iPARQ account through the browser that has launched. You have 15 seconds to login.")

        # Wait Until the URL changes noting a successful login
        WebDriverWait(browser, 60).until(EC.title_contains("iParq"))

    def set_main_portal_path(self, main_portal_path):
        self.MAIN_PORTAL_CSV = main_portal_path

    def set_affiliate_portal_path(self, affiliate_portal_path):
        self.AFFILIATE_PORTAL_CSV = affiliate_portal_path

    # test case: test all the permits in the main portal
    def test_map_main_portal(self):

        print('### CHECKING MAIN PORTAL ###')

        ########## 1. LOGIN ##########
        # Load Dataframe of main portal information
        self.df = pd.read_csv(self.MAIN_PORTAL_CSV)

        # get driver
        browser = self.driver

        # Navigate to the Permit Creation Page
        browser.get(self.PERMIT_TYPES)

        # Find the permit table
        permit_table = WebDriverWait(browser, 5).until(lambda d: d.find_element(By.ID, 'st_setuppermittypes'))

        # Grab all the permit elements in the table (in rows)
        permit_elements = permit_table.find_elements(By.TAG_NAME, "tr")

        # Define our permit name map
        permits = {}

        # Build a map of each permit's unique id
        for permit_element in permit_elements:
            # Get the unique ID for the current permit
            permit_class_name = permit_element.get_attribute('class')

            # filter out only the active permits (non-deleted)
            if (('rollover' in permit_class_name) and ('st_deleted' not in permit_class_name)):
                name_col = permit_element.find_elements(By.TAG_NAME, "td")[0]
                name_span = name_col.find_elements(By.TAG_NAME, "span")[3]
                name_input = name_span.find_element(By.NAME, "name")
                permit_name = name_input.get_attribute('value')

                # find the unique permit ID 
                match = re.search("\d{4}", permit_class_name)
                permit_name_unique_id = match.group()

                permits.update({permit_name.strip():permit_name_unique_id})

        ########## 2. LOAD IN CSV FILE FOR COMPARISONS & ITERATE THROUGH EACH PERMIT ##########
        for index, row in self.df.iterrows():
            
            # Initialize the Columns
            permit_name = str(row['PERMIT NAME'])
            permit_term = str(row['PERMIT TERM'])
            permit_psid = str(row['PSID'])
            permit_price = str(int(row['PERMIT AMOUNT']))
            permit_class_name = None
            permit_name_unique_id = permits[permit_name]
            permit_term_unique_id = None

            print("\n----- Checking Permit: " + permit_name + " -----")

            # visit the permit sessions for our current permit
            browser.get(self.PERMIT_SESSIONS + "master_ID=" + permit_name_unique_id)

            # Find the permit table
            permit_table = WebDriverWait(browser, 5).until(lambda d: d.find_element(By.ID, 'st_setuppermitsessions'))

            # Grab all the term elements in the table (in rows)
            term_elements = permit_table.find_elements(By.TAG_NAME, "tr")

            print("Current Session: " + permit_name + " " + permit_term)

            # Iterate through term elements and find the current session
            for term_element in term_elements:
                # Get the unique ID for the current permit
                permit_class_name = term_element.get_attribute('class')

                # filter out only the active permits (non-deleted)
                if (('rollover' in permit_class_name) and ('st_deleted' not in permit_class_name)):
                    name_col = term_element.find_elements(By.TAG_NAME, "td")[0]
                    name_span = name_col.find_elements(By.TAG_NAME, "span")[2]
                    name_input = name_span.find_element(By.TAG_NAME, "b")

                    if (permit_term == name_input.get_attribute("innerHTML")):
                        break
            
            # find the unique term ID based off our match
            match = re.search("\d{5}", permit_class_name)
            permit_term_unique_id = match.group()

            # visit the permit sessions
            browser.get(self.PERMIT_SESSIONS + "session_ID=" + permit_term_unique_id)

            # Find the PSID data in the databox
            current_permit = WebDriverWait(browser, 5).until(lambda d: d.find_element(By.ID, 'databox'))
            psid_span = current_permit.find_element(By.TAG_NAME, "span").find_element(By.TAG_NAME, "b").get_attribute("innerHTML")
            iPARQ_psid = re.search("\d{5}", psid_span).group()

            # Find the permit price in the data box
            price_row = current_permit.find_elements(By.TAG_NAME, 'tr')[5]
            price_element = price_row.find_elements(By.TAG_NAME, 'td')[1].get_attribute('innerHTML')
            iPARQ_price = re.search("\d+", price_element).group()

            self.assertEqual(iPARQ_psid, permit_psid)
            self.assertEqual(iPARQ_price, permit_price)

    # test case: test all the permits in the affiliate portal
    def test_map_affiliate_portal(self):

        print('### CHECKING AFFILIATE PORTAL ###')

        ########## 1. LOGIN ##########

        # Load Dataframe of permit information
        self.df = pd.read_csv(self.AFFILIATE_PORTAL_CSV)

        # get driver
        browser = self.driver

        # Switch to the affiliates portal
        browser.get(self.AFFILIATE_PORTAL)

        # Navigate to the Permit Creation Page
        browser.get(self.PERMIT_TYPES)

        # Find the permit table
        permit_table = WebDriverWait(browser, 5).until(lambda d: d.find_element(By.ID, 'st_setuppermittypes'))

        # Grab all the permit elements in the table (in rows)
        permit_elements = permit_table.find_elements(By.TAG_NAME, "tr")

        # Define our permit name map
        permits = {}

        # Build a map of each permit's unique id
        for permit_element in permit_elements:
            # Get the unique ID for the current permit
            permit_class_name = permit_element.get_attribute('class')

            # filter out only the active permits (non-deleted)
            if (('rollover' in permit_class_name) and ('st_deleted' not in permit_class_name)):
                name_col = permit_element.find_elements(By.TAG_NAME, "td")[0]
                name_span = name_col.find_elements(By.TAG_NAME, "span")[3]
                name_input = name_span.find_element(By.NAME, "name")
                permit_name = name_input.get_attribute('value')

                # find the unique permit ID 
                match = re.search("\d{4}", permit_class_name)
                permit_name_unique_id = match.group()

                permits.update({permit_name.strip():permit_name_unique_id})

        ########## 2. LOAD IN CSV FILE FOR COMPARISONS & ITERATE THROUGH EACH PERMIT ##########
        for index, row in self.df.iterrows():
            
            # Initialize the Columns
            permit_name = str(row['PERMIT NAME'])
            permit_term = str(row['PERMIT TERM'])
            permit_psid = str(row['PSID'])
            permit_price = str(int(row['PERMIT AMOUNT']))
            permit_class_name = None
            permit_name_unique_id = permits[permit_name]
            permit_term_unique_id = None

            print("\n----- Checking Permit: " + permit_name + " -----")

            # visit the permit sessions for our current permit
            browser.get(self.PERMIT_SESSIONS + "master_ID=" + permit_name_unique_id)

            # Find the permit table
            permit_table = WebDriverWait(browser, 5).until(lambda d: d.find_element(By.ID, 'st_setuppermitsessions'))

            # Grab all the term elements in the table (in rows)
            term_elements = permit_table.find_elements(By.TAG_NAME, "tr")

            print("Current Session: " + permit_name + " " + permit_term)

            # Iterate through term elements and find the current session
            for term_element in term_elements:
                # Get the unique ID for the current permit
                permit_class_name = term_element.get_attribute('class')

                # filter out only the active permits (non-deleted)
                if (('rollover' in permit_class_name) and ('st_deleted' not in permit_class_name)):
                    name_col = term_element.find_elements(By.TAG_NAME, "td")[0]
                    name_span = name_col.find_elements(By.TAG_NAME, "span")[2]
                    name_input = name_span.find_element(By.TAG_NAME, "b")

                    if (permit_term == name_input.get_attribute("innerHTML")):
                        break
            
            # find the unique term ID based off our match
            match = re.search("\d{5}", permit_class_name)
            permit_term_unique_id = match.group()

            # visit the permit sessions
            browser.get(self.PERMIT_SESSIONS + "session_ID=" + permit_term_unique_id)

            # Find the PSID data in the databox
            current_permit = WebDriverWait(browser, 5).until(lambda d: d.find_element(By.ID, 'databox'))
            psid_span = current_permit.find_element(By.TAG_NAME, "span").find_element(By.TAG_NAME, "b").get_attribute("innerHTML")
            iPARQ_psid = re.search("\d{5}", psid_span).group()

            # Find the permit price in the data box
            price_row = current_permit.find_elements(By.TAG_NAME, 'tr')[5]
            price_element = price_row.find_elements(By.TAG_NAME, 'td')[1].get_attribute('innerHTML')
            iPARQ_price = re.search("\d+", price_element).group()

            self.assertEqual(iPARQ_psid, permit_psid)
            self.assertEqual(iPARQ_price, permit_price)

    # cleanup method called after every test performed 
    def tearDown(self):
        self.driver.close() 
  
# execute the script 
# if __name__ == "__main__":
#     main_portal_path = None
#     affiliate_portal_path = None
#     username = None
#     password = None
#     test = iPARQTest()
    
#     # set up our driver with our username and password
#     test.setUp()

#     # Poll input
#     test_main_portal = input("\nWould you like to test the Main Portal? (Y/N)\n")
#     if (test_main_portal == "Y"):
#         main_portal_path = filedialog.askopenfilename()
#         test.set_main_portal_path(main_portal_path)
#         print("Testing Main Portal!")
#         test.test_map_main_portal()

#     test_affiliate_portal = input("\nWould you like to test the Affiliate Portal? (Y/N)\n")
#     if (test_affiliate_portal == "Y"):
#         affiliate_portal_path = filedialog.askopenfilename()
#         test.set_affiliate_portal_path(affiliate_portal_path)
#         print("Testing Affiliate Portal!")
#         test.test_map_affiliate_portal()
    
#     if (main_portal_path == None and affiliate_portal_path == None):
#         print("\nIn order to run the tests, either a Main Portal CSV File or a Affiliate Portal CSV File must be inputted. Please try again.\n")

#     test.tearDown()
#     # unittest.main(warnings='ignore')