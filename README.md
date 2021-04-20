# iPARQ Automation Project
Currently, this project serves to validate permit PSID's, prices, & names are correctly recorded in the "iPARQ Permit Creation Template."

# Usage
You've finished making the new permits for the upcoming year & want to verify them using a script that's fast & accurate. Here's the steps to set up the program:

## Step #1. Set Up / Installation
1. Download & Install the following:
    - [Python (latest version)](https://www.python.org/downloads/)
    - [Selenium (for Python)](https://www.selenium.dev/downloads/)

2. Open Command Prompt (windows) or terminal (mac) as administrator.
    - Enter the following into the window: `pip install webdriver-manager`
    - if the command above doesn't work try: `pip3 install webdriver-manager`

## Step #2. Usage
1. Open a Command Prompt (windows) or terminal (mac) with the unzipped folder:
    - [How to Open a terminal window for a specific folder](https://www.groovypost.com/howto/open-command-window-terminal-window-specific-folder-windows-mac-linux/) 

2. After opening it, run the following command:
    - `python Driver.py`
    - if the command above doesn't work, use `python3 Driver.py`

3. After the window opens, go ahead and log in.

4. After logging in, refer back to the command line/terminal window and respond "Y" to the prompts.

5. You can go ahead and view all the permits being verified one by one.

6. If there's an error, the program will stop. Reference the google sheet & iparq to verify that both are made correctly.