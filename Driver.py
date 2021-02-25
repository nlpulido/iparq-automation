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
        browser = self.driver

        print("Please login to your iPARQ account through the browser that has launched. You have 15 seconds to login.")

        # Wait Until the URL changes noting a successful login
        WebDriverWait(browser, 60).until(EC.title_contains("iParq"))

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
            driver.setUp()
            driver.tearDown()
            break
        elif (userChoice == '2'):
            print("Loading Permit Creator...")
            driver.setUp()
            driver.tearDown()
            break
        elif (userChoice == '3'):
            print('Exiting..')
            break
        else:
            print("Option not valid. Please try again.")