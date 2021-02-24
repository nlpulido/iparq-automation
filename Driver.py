# from test.py import iPARQtest

class Driver():
    
    def test(self):
        print('Hello World')

if __name__ == "__main__":
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
            break
        elif (userChoice == '2'):
            print("Loading Permit Creator...")
            break
        elif (userChoice == '3'):
            print('Exiting..')
            break
        else:
            print("Option not valid. Please try again.")