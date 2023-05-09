#!./env/bin/python
from datetime import datetime, timedelta
import time
import re
import requests
import gspread

CAMPAIGN_SHEET_NAME = 'TikTune Campaigns'
SERVICE_ACCOUNT_FILE = '../service_account.json'
TIKTOK_HASHTAG_URL = 'https://www.tiktok.com/tag/{}'
VIEW_COUNT_REGEX = r'>([\d\.]+[KMB]?) views<'

def parse_views_string(views_str):
    """
    Parses a string of views into an integer representing the number of views in thousands.
    """
    if views_str.endswith('K'):
        return int(float(views_str[:-1]))
    if views_str.endswith('M'):
        return int(float(views_str[:-1]) * 1000)
    if views_str.endswith('B'):
        return int(float(views_str[:-1]) * 1000000)
    return int(int(views_str) / 1000)

def update_hashtag_views():
    """
    Updates the current_reach column in the google sheet.
    Sheet column with the name of "tag" is the hashtag.
    Sheet column with the first row of "current_reach" is the current reach.
    """
    gc = gspread.service_account(filename=SERVICE_ACCOUNT_FILE)
    sh = gc.open(CAMPAIGN_SHEET_NAME)
    worksheet = sh.worksheet("Sheet1")
    rows = worksheet.get_all_records()

    for row in rows:
        hashtag = row['tag']
        current_reach = row['current_reach']

        # Skip rows with end date more then a two weeks age and that have already been completed
        if datetime.strptime(row['end'], '%d/%m/%Y') < datetime.now() - timedelta(days=14) and int(row['current_reach']) >= int(row['goal']):
            print(f'Skipping {hashtag} because end date is more then a week ago')
            continue

        url = TIKTOK_HASHTAG_URL.format(hashtag)
        print(f'Scraping {url}...')
        html = requests.get(url).text
        views_match = re.search(VIEW_COUNT_REGEX, html)

        if views_match is None:
            print(f'Failed to find views for {hashtag}')
            continue

        views_str = views_match.group(1)
        views = parse_views_string(views_str)

        if views != current_reach:
            row_num = rows.index(row) + 2  # add 2 to account for header row and 0-indexing
            worksheet.update_cell(row_num, list(row.keys()).index('current_reach') + 1, views)
            print(f'Updated current reach for {hashtag} to {views}')
        else:
            print(f'Current reach for {hashtag} is already up to date')

        time.sleep(1)
        
if __name__ == '__main__':
    update_hashtag_views()
