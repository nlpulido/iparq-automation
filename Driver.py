import os
import unittest
import logging
import re
import ezsheets
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.expected_conditions import element_to_be_clickable
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.events import EventFiringWebDriver, AbstractEventListener
from selenium.webdriver.common.keys import Keys

class AlertListener(AbstractEventListener):
    def after_change_value_of(self, element, driver):
        driver.switch_to.alert.accept()

class Driver(unittest.TestCase):

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
    def test_map_main_portal(self, ss, term):

        print('### CHECKING MAIN PORTAL ###')

        ########## 1. LOGIN ##########

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

        # Get the rows of the spreadsheet object
        curr_sheet = ss[term]
        rows = curr_sheet.getRows()

        ########## 2. LOAD IN CSV FILE FOR COMPARISONS & ITERATE THROUGH EACH PERMIT ##########
        for i, row in enumerate(rows):

            # Grab values from the Google Sheet
            permit_psid = row[0]
            permit_price = row[5]
            permit_name = row[7]
            permit_term = row[8]

            if ((permit_name != '') and (i > 2)):
                # Grab the unique ID from our local hashtable
                permit_class_name = None
                permit_name_unique_id = permits[permit_name]
                permit_term_unique_id = None

                # visit the permit sessions for our current permit
                browser.get(self.PERMIT_SESSIONS + "master_ID=" + permit_name_unique_id)

                # Find the permit table
                permit_table = WebDriverWait(browser, 5).until(lambda d: d.find_element(By.ID, 'st_setuppermitsessions'))

                # Grab all the term elements in the table (in rows)
                term_elements = permit_table.find_elements(By.TAG_NAME, "tr")

                print("Current Session(" + permit_psid +") : " + permit_name + " " + permit_term)

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
    def test_map_affiliate_portal(self, ss, term):

        print('### CHECKING AFFILIATE PORTAL ###')

        ########## 1. LOGIN ##########

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

        # Get the rows of the spreadsheet object
        curr_sheet = ss[term]
        rows = curr_sheet.getRows()

        ########## 2. LOAD IN CSV FILE FOR COMPARISONS & ITERATE THROUGH EACH PERMIT ##########
        for i, row in enumerate(rows):

            # Grab values from the Google Sheet
            permit_psid = row[0]
            permit_price = row[5]
            permit_name = row[7]
            permit_term = row[8]

            if ((permit_name != '') and (i > 2)):
                # Grab the unique ID from our local hashtable
                permit_class_name = None
                permit_name_unique_id = permits[permit_name]
                permit_term_unique_id = None

                # visit the permit sessions for our current permit
                browser.get(self.PERMIT_SESSIONS + "master_ID=" + permit_name_unique_id)

                # Find the permit table
                permit_table = WebDriverWait(browser, 5).until(lambda d: d.find_element(By.ID, 'st_setuppermitsessions'))

                # Grab all the term elements in the table (in rows)
                term_elements = permit_table.find_elements(By.TAG_NAME, "tr")

                print("Current Session(" + permit_psid +") : " + permit_name + " " + permit_term)

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
        curr_sheet = ss["Main Portal Fall (2021-2022)"]
        rows = curr_sheet.getRows()

        # Go through the rows and extract the information (THIS IS IF WE WANTED TO DO IT FOR EVERY PERMIT)
        # for i, row in enumerate(rows):
        #     # skip the header entries 
        #     if (row[1] != '' and i > 2):
        #         current_permit_name = row[permit_name_column]
        #         print("Permit name: " + current_permit_name)
        #         print("Corresponding unique ID: " + permits.get(current_permit_name))

        # Test a single row
        current_row = rows[3]
        current_permit_name = current_row[7]
        current_permit_term = current_row[8]
        current_permit_price = current_row[5]
        current_permit_clone_term = current_row[9]
        current_permit_sales_start = current_row[10]
        current_permit_sales_end = current_row[11]
        current_permit_valid_start = current_row[12]
        current_permit_valid_end = current_row[13]
        current_permit_psid = current_row[0]

        print("\n##########")
        print("Creating Permit for the following: " + current_permit_name + ", " + current_permit_term)
        print("Price: " + current_permit_price)
        print("Cloning: " + current_permit_clone_term)
        print("##########\n")

        # Navigate to the permit page of this row
        self.browser.get(self.PERMIT_SESSIONS + "master_ID=" + permits.get(current_permit_name))

        # Find the permit table
        permit_table = WebDriverWait(self.browser, 5).until(lambda d: d.find_element(By.ID, 'st_setuppermitsessions'))

        # Grab all the term elements in the table (in rows)
        term_elements = permit_table.find_elements(By.TAG_NAME, "tr")

        # create a map of each permit term and their unique id's
        permit_terms = {}

        # Iterate through term elements and find the current session
        for term_element in term_elements:
            # Get the unique ID for the current permit
            permit_class_name = term_element.get_attribute('class')

            # filter out only the active permits (non-deleted)
            if (('rollover' in permit_class_name) and ('st_deleted' not in permit_class_name)):
                name_col = term_element.find_elements(By.TAG_NAME, "td")[0]
                name_span = name_col.find_elements(By.TAG_NAME, "span")[2]
                name_input = name_span.find_element(By.TAG_NAME, "b")
                curr_permit_term_name = name_input.get_attribute("innerHTML")

                # use regular expressions to grab the unique permit id
                match = re.search("\d{5}", permit_class_name)
                permit_term_unique_id = match.group()

                # put the corresponding unique id and permit class name in our map
                permit_terms.update({curr_permit_term_name.strip():permit_term_unique_id})

        if (current_permit_term not in permit_terms):

            # visit the link to clone the permit
            self.browser.get(self.PERMIT_SESSIONS + "session_ID=" + permit_terms.get(current_permit_clone_term) + "&clone=1")

            # find the cloned permit databox
            cloned_permit = WebDriverWait(self.browser, 5).until(lambda d: d.find_element(By.ID, 'databox'))

            # Permit Sales Name
            name_row = cloned_permit.find_elements(By.TAG_NAME, 'tr')[1]
            name_element = name_row.find_elements(By.TAG_NAME, 'td')[1]
            name_input_form = name_element.find_element_by_tag_name('input')
            name_input_form.send_keys(current_permit_term)
            name_input_form.send_keys(Keys.TAB)
            name_alert = WebDriverWait(self.browser, 5).until(EC.alert_is_present())
            self.browser.switch_to.alert.accept()

            # Permit Design Group
            design_group_row = cloned_permit.find_elements(By.TAG_NAME, 'tr')[2]
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

            # Permit Sales Start Date
            sales_start_date_row = cloned_permit.find_elements(By.TAG_NAME, 'tr')[7]
            sales_start_date_element = sales_start_date_row.find_elements(By.TAG_NAME, 'td')[1]
            sales_start_date_input_form = sales_start_date_element.find_element_by_tag_name('input')
            sales_start_date_input_form.clear()
            sales_start_date_input_form.send_keys(current_permit_sales_start)

            # Permit Sales End Date
            sales_end_date_row = cloned_permit.find_elements(By.TAG_NAME, 'tr')[8]
            sales_end_date_element = sales_end_date_row.find_elements(By.TAG_NAME, 'td')[1]
            sales_end_date_input_form = sales_end_date_element.find_element_by_tag_name('input')
            sales_end_date_input_form.clear()
            sales_end_date_input_form.send_keys(current_permit_sales_end)

            # Permit Valid Start Date
            valid_start_date_row = cloned_permit.find_elements(By.TAG_NAME, 'tr')[12]
            valid_start_date_element = valid_start_date_row.find_elements(By.TAG_NAME, 'td')[1]
            valid_start_date_input_form = valid_start_date_element.find_element_by_tag_name('input')
            valid_start_date_input_form.clear()
            valid_start_date_input_form.send_keys(current_permit_valid_start)

            # Permit Valid End Date
            valid_end_date_row = cloned_permit.find_elements(By.TAG_NAME, 'tr')[13]
            valid_end_date_element = valid_end_date_row.find_elements(By.TAG_NAME, 'td')[1]
            valid_end_date_input_form = valid_end_date_element.find_element_by_tag_name('input')
            valid_end_date_input_form.clear()
            valid_end_date_input_form.send_keys(current_permit_valid_end)

            # Add Session Buttons
            add_session_btn = cloned_permit.find_element(By.XPATH, '//*[@id="ps_submit"]/table/tbody/tr[44]/td[2]/span/a')
            add_session_btn.click()

            # Wait till the Permit PSID appears
            permit_psid = WebDriverWait(self.browser, 10).until(lambda d: d.find_element(By.XPATH, '//*[@id="databox"]/table/tbody/tr[1]/td/span/b')).innerHTML

            # use regular expressions to grab the unique permit id
            permit_psid_match = re.search("\d{5}", permit_psid)
            permit_term_unique_psid = permit_psid_match.group()

            # write the permit PSID to the google sheet
            current_permit_psid = permit_term_unique_psid
            print("permit_term_unique_psid: " + permit_term_unique_psid)
            print("current_permit_psid: " + current_permit_psid)

            time.sleep(3)

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
            print("Please make sure that the iPARQ Permit Creation Template is the Google Sheet that you used.")

            # Set up our Selenium WebDriver
            driver.setUp()

            main_portal_path = False
            affiliate_portal_path = False
            term = ""

            # Poll input
            term = input("\nPlease enter the exact name of the portal you'd like to verify. (For example: Fall (2021-2022)) \n")

            test_main_portal = input("\nWould you like to test the Main Portal? (Y/N)\n")
            if (test_main_portal == "Y"):
                main_portal_path = True
                ss = ezsheets.Spreadsheet("1WOto59_8sdDg1_4Zd52UAteDmusdW1F5WdtBbGhpouk")
                print("Testing Main Portal!")
                driver.test_map_main_portal(ss, term)

            test_affiliate_portal = input("\nWould you like to test the Affiliate Portal? (Y/N)\n")
            if (test_affiliate_portal == "Y"):
                affiliate_portal_path = True
                ss = ezsheets.Spreadsheet("1WOto59_8sdDg1_4Zd52UAteDmusdW1F5WdtBbGhpouk")
                print("Testing Affiliate Portal!")
                driver.test_map_affiliate_portal(ss, term)

            if (main_portal_path == None and affiliate_portal_path == None):
                print("\nIn order to run the tests, either a Main Portal CSV File or a Affiliate Portal CSV File must be inputted. Please try again.\n")

            # Tear Down once finished
            driver.tearDown()
            break
        elif (userChoice == '2'):
            print("Loading Permit Creator...")
            print("Sorry, that functionality has been taken out!")

            # ss = ezsheets.Spreadsheet("1WOto59_8sdDg1_4Zd52UAteDmusdW1F5WdtBbGhpouk")

            # # Set up our Selenium WebDriver
            # driver.setUp()

            # # Create permits for the main portal
            # driver.create_permits_main_portal(ss)

            # # Tear Down once finished
            # driver.tearDown()

            break
        elif (userChoice == '3'):
            print('Exiting..')
            break
        else:
            print("Option not valid. Please try again.")