import ezsheets

SPREADSHEET_ID = "17g53mrN4NNg3hJokbwVhm20uvVnHk33WfkXE_ApMkSc"

if __name__ == "__main__":
    ss = ezsheets.Spreadsheet(SPREADSHEET_ID)
    print(ss.sheets)
    print('\n')
    print(ss[0])