import pandas as pd

videos = pd.read_json('videos_joined.json', lines=True)

for camp, group in videos.sort_values(['campaign', 'play_count']).groupby('campaign'):
    print(camp)
    for i, vid in group.sort_values('play_count', ascending=False).head(10).iterrows():
        print(vid.play_count, vid.url)
    # print(group.sort_values('play_count', ascending=False).head(10)[['campaign', 'play_count', 'url']].values)


# import code
# code.interact(local=locals())
