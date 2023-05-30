
from scenedetect import detect, ContentDetector
scene_list = detect('data/vasaklinka/music_videos/vasa_klinka.webm', ContentDetector())

def get_scenes(video_path):
    scene_list = detect(video_path, ContentDetector())
    # scenes = []
    print(scene_list)
    # for scene in scene_list:
    #     scenes.append(scene[1].get_frames())
    # return scenes
    return scene_list


scenes = get_scenes('data/vasaklinka/music_videos/vasa_pazljivo.webm')

print(scenes)

import code
code.interact(local=locals())