from datetime import datetime
import os
import time
import json

import requests
import pandas as pd

USER_POSTS_ENDPOINT = "https://scraptik.p.rapidapi.com/user-posts"
API_KEYS = [
    '0451f517a1msh2c9364871a27d44p17a616jsn208f4ae81458',
    '353ac5d36amsh07aafabd66ebf02p1b50a9jsn77d0071bb128',
    # '658491cebemshf233eca18c0c2b5p16800bjsn5acea6080d8b',
    'f59be74f09msh492de900bf392c8p14dde4jsn9f382bf2ea66',
    'df851f55bemshc19b9039c27dab3p151bbajsn268253b92dc3',
    '6e93e5bf84msh2ad5025586776d6p134ebdjsn356f9da2bfee',
    'ac914fa92fmsh0f837bd1d4668b0p103599jsn5b66d805e836',
]
API_KEY_IDX = 0

HEADERS = {
    "X-RapidAPI-Host": "scraptik.p.rapidapi.com"
}
RESULTS_DIR = 'data'

def get_posts(user_id):
    global API_KEY_IDX
    headers = HEADERS
    headers['X-RapidAPI-Key'] = API_KEYS[API_KEY_IDX]

    response = requests.get(USER_POSTS_ENDPOINT, headers=HEADERS, params={
        "user_id": user_id,
        "max_cursor":"0",
        "count":100
    })

    if response.status_code == 429 and 'You have exceeded the MONTHLY quota for TikTok' in response.json()['message']:
        API_KEY_IDX += 1
        if API_KEY_IDX >= len(API_KEYS):
            raise Exception("All api keys exasuted.")
        print(f"Key limit reached swithcing to next key {API_KEY_IDX + 1}")
        return get_posts(user_id)
    
    return response


def main():
    accounts = pd.read_json('../accounts_db.json', lines=True, dtype={'user_id': str}).fillna('')
    today = datetime.today().strftime('%Y-%m-%d')
    print(f"Fetching results for date {today}")

    for i, account in accounts.iterrows():
        print(f"{i+1}\t", end='')
        if not account.user_id:
            print(f"Account {account.username} doesn't have user_id, skipping...")
            continue

        if account.active_lately == 'ne':
            print(f"Inactive account {account.username} skipping...")
            continue

        if not account.active:
            print(f"Account {account.username} is not active, skipping...")
            continue

        result_path = f"{RESULTS_DIR}/{today}:{account.username}.json" 
        if os.path.exists(result_path):
            print(f"Account {account.username} already has results, skipping...")
            continue

        print(f"Fetching videos for {account.username} to {result_path}")
        response = get_posts(account.user_id)
        # response = requests.get(USER_POSTS_ENDPOINT, headers=HEADERS, params={
        #     "user_id": account.user_id,
        #     "max_cursor":"0",
        #     "count":1000
        # })

        if response.status_code != 200:
            raise Exception(f"Response returned status: {response.status_code} response: {response.text}")
        
        data = response.json()

        if 'status_code' in data:
            if data['status_code'] != 0:
                raise Exception(f"Error: status_code {data['status_code']} in response {response.text[:100]}")
        elif not data['success']:
            raise Exception(f"Error in response {response.text[:100]}")
        
        with open(result_path, 'w') as file:
            json.dump(data, file, indent=2)
        
        # Api rate limit
        time.sleep(1)
            
        
if __name__ == '__main__':
    main()
