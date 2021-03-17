import os
import time
import unittest
import logging
import re
import pandas as pd
import tkinter
import ezsheets
from tkinter import filedialog
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.expected_conditions import element_to_be_clickable
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait


class Driver():

    # Set up our Selenium Web Driver before we start any automation process
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
        self.browser = self.driver

        print("Please login to your iPARQ account through the browser that has launched. You have 1 minute to login.")

        # Wait Until the URL changes noting a successful login
        WebDriverWait(self.browser, 60).until(EC.title_contains("iParq"))

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

    # create permits for the main portal
    def create_permits_main_portal(self, ss):
        # Navigate to the Permit Creation Page
        self.browser.get(self.PERMIT_TYPES)

        # Find the permit table
        permit_table = WebDriverWait(self.browser, 5).until(lambda d: d.find_element(By.ID, 'st_setuppermittypes'))

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

        # Get the rows of the spreadsheet object
        curr_sheet = ss["Sheet1"]
        rows = curr_sheet.getRows()

        # Define each column's index
        permit_price_column = 5
        permit_name_column = 7
        permit_term_column = 8
        permit_clone_column = 9

        # Go through the rows and extract the information
        # for i, row in enumerate(rows):
        #     # skip the header entries 
        #     if (row[1] != '' and i > 2):
        #         current_permit_name = row[permit_name_column]
        #         print("Permit name: " + current_permit_name)
        #         print("Corresponding unique ID: " + permits.get(current_permit_name))

        # Test a single row
        current_row = rows[3]
        current_permit_name = current_row[permit_name_column]
        current_permit_term = current_row[permit_term_column]
        current_permit_price = current_row[permit_price_column]
        current_permit_clone_name = current_row[permit_clone_column]

        print("\n##########")
        print("Creating Permit for the following: " + current_permit_name + ", " + current_permit_term)
        print("Price: " + current_permit_price)
        print("Cloning: " + current_permit_clone_name)
        print("##########\n")

        # Navigate to the permit page of this row
        self.browser.get(self.PERMIT_SESSIONS + "master_ID=" + permits.get(current_permit_name))

        # Find the permit table
        permit_table = WebDriverWait(self.browser, 5).until(lambda d: d.find_element(By.ID, 'st_setuppermitsessions'))

        # Grab all the term elements in the table (in rows)
        term_elements = permit_table.find_elements(By.TAG_NAME, "tr")

        # Iterate through term elements and find the current session
        for term_element in term_elements:
            # Get the unique ID for the current permit
            permit_class_name = term_element.get_attribute('class')

            # filter out only the active permits (non-deleted)
            if (('rollover' in permit_class_name) and ('st_deleted' not in permit_class_name)):
                name_col = term_element.find_elements(By.TAG_NAME, "td")[0]
                name_span = name_col.find_elements(By.TAG_NAME, "span")[2]
                name_input = name_span.find_element(By.TAG_NAME, "b")

                if (current_permit_clone_name == name_input.get_attribute("innerHTML")):
                    break
        
        # find the unique term ID based off our match
        match = re.search("\d{5}", permit_class_name)
        permit_term_unique_id = match.group()

        # click on the tab of the permit term
        self.browser.get(self.PERMIT_SESSIONS + "session_ID=" + permit_term_unique_id)

        # visit the link to clone the permit
        self.browser.get(self.PERMIT_SESSIONS + "session_ID=" + permit_term_unique_id + "&clone=1")

        # find the cloned permit databox
        cloned_permit = WebDriverWait(self.browser, 5).until(lambda d: d.find_element(By.ID, 'databox'))

        # Permit Sales Name
        name_row = cloned_permit.find_elements(By.TAG_NAME, 'tr')[1]
        name_element = name_row.find_elements(By.TAG_NAME, 'td')[1]
        name_input_form = name_element.find_element_by_tag_name('input')
        name_input_form.send_keys(current_permit_term)
        alert = WebDriverWait(self.browser, 10).until(EC.alert_is_present())
        self.browser.switch_to.alert.accept()

        # Permit Design Group
        design_group_row = cloned_permit.find_elements(By.TAG_NAME, 'tr')[2]
        # make sure you accept the popup after out of name context. It only triggers once you leave context
        alert = WebDriverWait(self.browser, 10).until(EC.alert_is_present())
        self.browser.switch_to.alert.accept()
        dropdown_parent = design_group_row.find_elements(By.TAG_NAME, 'td')[1]
        dropdown_menu = dropdown_parent.find_element_by_tag_name('select')
        # dropdown_menu.select(something here)
        # alert = WebDriverWait(self.browser, 5).until(EC.alert_is_present())
        # self.browser.switch_to.alert.accept()

        # Permit Price
        price_row = cloned_permit.find_elements(By.TAG_NAME, 'tr')[4]
        price_element = price_row.find_elements(By.TAG_NAME, 'td')[1]
        price_input_form = price_element.find_element_by_tag_name('input')
        price_input_form.clear()
        price_input_form.send_keys(current_permit_price)

        time.sleep(10)

    def tearDown(self):
        self.driver.close()

if __name__ == "__main__":
    driver = Driver()

    while True:

        # Print the Menu of commands
        print("""
                Main Menu
                1. Verify Newly Made Permits
                2. Create New Permits
                3. Exit\n""")

        # Poll for user's choice
        userChoice = input("Enter a number to perform a command: ")

        if (userChoice == "1"):
            print("Loading New Permit Verify Test...")
            main_portal_path = None
            affiliate_portal_path = None

            # Set up our Selenium WebDriver
            driver.setUp()

            # Poll input
            test_main_portal = input("\nWould you like to test the Main Portal? (Y/N)\n")
            if (test_main_portal == "Y"):
                main_portal_path = filedialog.askopenfilename()
                driver.set_main_portal_path(main_portal_path)

                print("Testing Main Portal!")

                driver.test_map_main_portal()

            test_affiliate_portal = input("\nWould you like to test the Affiliate Portal? (Y/N)\n")
            if (test_affiliate_portal == "Y"):

                affiliate_portal_path = filedialog.askopenfilename()
                driver.set_affiliate_portal_path(affiliate_portal_path)

                print("Testing Affiliate Portal!")

                driver.test_map_affiliate_portal()

            if (main_portal_path == None and affiliate_portal_path == None):
                print("\nIn order to run the tests, either a Main Portal CSV File or a Affiliate Portal CSV File must be inputted. Please try again.\n")

            # Tear Down once finished
            driver.tearDown()
            break
        elif (userChoice == '2'):
            print("Loading Permit Creator...")

            ss = ezsheets.Spreadsheet("1-ef8OVvVqXzUDfoFHTt7RQF4M_MLrswSnF4j9991yFo")

            # Set up our Selenium WebDriver
            driver.setUp()

            # Create permits for the main portal
            driver.create_permits_main_portal(ss)

            # Tear Down once finished
            driver.tearDown()

            break
        elif (userChoice == '3'):
            print('Exiting..')
            break
        else:
            print("Option not valid. Please try again.")