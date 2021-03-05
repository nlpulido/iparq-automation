import ezsheets

SPREADSHEET_ID = "17g53mrN4NNg3hJokbwVhm20uvVnHk33WfkXE_ApMkSc"

if __name__ == "__main__":
    ss = ezsheets.Spreadsheet(SPREADSHEET_ID)
    print("\n")

    # how we access sheets
    main_portal_fall_2021_2022 = ss["Main Portal Fall (2021-2022)"]

    # how we write into columns
    # main_portal_fall_2021_2022['A4'] = "001"

    # how we read from columns
    # print("get: " + main_portal_fall_2021_2022.get("F4"))

    # how we read directly from columns
    # prices = main_portal_fall_2021_2022.getColumn('F')
    # for i, value in enumerate(prices):
    #     if (value != ''):
    #         print(value)

    # how we read row by row (of those rows that aren't blank)
    rows = main_portal_fall_2021_2022.getRows()
    for i, row in enumerate(rows):
        if (row[1] != ''):
            print(row)
