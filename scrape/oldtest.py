from TikTokApi import TikTokApi

# Watch https://www.youtube.com/watch?v=-uCt1x8kINQ for a brief setup tutorial
with TikTokApi() as api:
    user = api.user(username='editsbysarah.x')
    for vid in user.videos(1):
        print(vid)
