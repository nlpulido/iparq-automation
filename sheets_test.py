import ezsheets

SPREADSHEET_ID = "17g53mrN4NNg3hJokbwVhm20uvVnHk33WfkXE_ApMkSc"

if __name__ == "__main__":
    ss = ezsheets.Spreadsheet(SPREADSHEET_ID)
    print("\n")

    main_portal_fall_2021_2022 = ss[3]

    print("get: " + main_portal_fall_2021_2022.get("A4"))
    main_portal_fall_2021_2022['A4'] = "001"
    print("get: " + main_portal_fall_2021_2022.get("A4"))

