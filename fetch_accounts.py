#!./env/bin/python
import pandas as pd
import gspread

print("Fetching account sheet...")
gc = gspread.service_account('service_account.json')
sheet = gc.open("Tiktok Nalozi").sheet1
accounts = pd.DataFrame(sheet.get_all_records())
accounts = accounts.applymap(lambda x: True if x == 'TRUE' else False if x == 'FALSE' else x)
accounts.to_json('accounts_db.json', orient='records', lines=True)

print("Done.")
