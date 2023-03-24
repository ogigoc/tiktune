import pandas as pd
import gspread

gc = gspread.service_account('service_account.json')
sheet = gc.open("Tiktok Nalozi").sheet1
accounts = pd.DataFrame(sheet.get_all_records())
accounts.to_json('accounts_db.json', orient='records', lines=True)
