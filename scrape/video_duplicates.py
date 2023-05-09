import pandas as pd

# Read video data from 'videos_db.json'
# Join with accounts_db.json on 'account_id'
# create dataframe with video rows that have a duplicate file

videos = pd.read_json('videos_db.json', lines=True)
print(videos)
accounts = pd.read_json('accounts_db.json', lines=True)
# videos = videos.merge(accounts, how='left', left_on='account_id', right_on='id')
print(videos)

duplicate_files = videos[videos.duplicated(subset='file', keep=False)]
duplicate_files = duplicate_files.merge(accounts, how='left', left_on='account_id', right_on='id')

duplicate_files = duplicate_files.sort_values(by='file')
d = duplicate_files

print(duplicate_files[['file', 'time']])

import code
code.interact(local=locals())
