import time
import re

import pandas as pd
import requests

accounts_db = '../accounts_db.json'
TIKTOK_USER_URL = 'https://www.tiktok.com/@{}'
AUTHOR_ID_REGEX = r'\"authorId\":\"(\d+)\"'

def fillin_author_id():
    """
    Fills in the author_id field in the accounts file.
    Only for accounts that are active and don't have author_id.
    """
    # add some logging to this

    accounts = pd.read_json(accounts_db, lines=True, dtype={'user_id': int})

    print(f"Fetching author ids for {len(accounts[accounts.active & (accounts.user_id == '')])} accounts...")

    for i, account in accounts.iterrows():
        print(f"{i+1}\t", end='')
        if not account.active or account.user_id:
            print(f"\tSkipping {account.username}")
            continue
        url = TIKTOK_USER_URL.format(account.username)
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Failed to fetch {url} with status {response.status_code}")
            continue

        matches = re.findall(AUTHOR_ID_REGEX, response.text)
        if not matches:
            print(f"Failed to find author ID in {url}")
            continue

        author_id = matches[0]
        print(f"Found author id {author_id} for {account.username}")
        accounts.loc[i, 'user_id'] = int(author_id)

        accounts.to_json(accounts_db, lines=True, orient='records')
        time.sleep(1)

    print("Done.")
    print("Copy these author ids to the google sheet user_id column.")
    print(accounts.user_id.to_string(index=False))
    print("Copy these author ids to the google sheet user_id column.")

if __name__ == '__main__':
    fillin_author_id()
