import os
import glob
import random
import multiprocessing as mp

from moviepy.editor import *
from moviepy import *
from moviepy.video.fx.all import *

def low_zoom(clip):
    return clip.resize(height=1080).set_position("center")

def full_zoom(clip):
    return clip.resize(height=1920).set_position("center")

def no_zoom(clip):
    return clip.resize(width=1080).set_position("center")

def blackwhitex(clip):
    return clip.fx(blackwhite)

# def color(clip):
#     return clip.fx(colorx, 2)

def triple(clip):
    return CompositeVideoClip([
        clip.resize(height=640).fx(blackwhite).set_position(('center', 'top')),
        clip.resize(height=640).fx(blackwhite).set_position(('center', 'bottom')),
        clip.resize(height=640).set_position('center'),
    ], size = (1080, 1920))

def upsidedown(clip):
    return clip.rotate(180)

def mirror(clip):
    return clip.fx(mirror_x)


EFFECTS = {
    'low_zoom': low_zoom,
    'full_zoom': full_zoom,
    'triple': triple,
    'low_zoom_blackwhite': lambda c: low_zoom(blackwhitex(c)),
    'full_zoom_blackwhite': lambda c: full_zoom(blackwhitex(c)),
    'low_zoom_mirror': lambda c: low_zoom(mirror(c)),
    'no_zoom': no_zoom,
}
DATA_DIR = 'data'


class Segment():
    def __init__(self, start, template, background, effect, effect_name, output_dir):
        self.start = start
        self.template = template
        self.background = background
        self.effect = effect
        self.effect_name = effect_name
        self.output_dir = output_dir
        self.output_path = (
            f'{output_dir}/{str(self.start).zfill(5)};{self.background.filename.split("/")[-1].replace("/", "").replace(";", "")};{self.template.filename.split("/")[-1]};'
            f'{self.effect_name}.mp4'
        )
    
    def write(self):
        if not os.path.isdir(self.output_dir):
            os.makedirs(self.output_dir)

        if not os.path.exists(self.output_path):
            print(f"Rendering {self.output_path}")
            result = CompositeVideoClip([
                self.effect(self.background.subclip(self.start, self.start + self.template.duration).without_audio()),
                self.template
            ], size=self.template.size)
            result.write_videofile(self.output_path)
        else:
            print(f"Skipping {self.output_path}, exists.")


def create_segments(campaign_name, step, bstart=3, bend=3):
    print(f"Loading templates for campaign {campaign_name}")
    templates = [
        VideoFileClip(path, has_mask=True)
        for path in sorted(list(glob.glob(f'{DATA_DIR}/{campaign_name}/templates/*')))
    ]
    print(f"Found {len(templates)} templates for {campaign_name}")
    if not templates:
        raise Exception(f"No templates for {campaign_name}")

    print(f"Loading backgrounds for campaign {campaign_name}")
    backgrounds = [
        VideoFileClip(path)
        for path in sorted(list(glob.glob(f'{DATA_DIR}/{campaign_name}/music_videos/*')))
    ]
    print(f"Found {len(backgrounds)} backgrounds for {campaign_name}")
    if not backgrounds:
        raise Exception(f"No backgrounds for {campaign_name}")

    segments = []
    effects = list(EFFECTS.items())

    for background in backgrounds:
        start = bstart
        i = 0
        while (temp := templates[i % len(templates)]).duration + start < background.duration - bend:
            segments.append(Segment(
                start=start,
                template=temp,
                background=background,
                effect=effects[i % len(effects)][1],
                effect_name=effects[i % len(effects)][0],
                output_dir=f'{DATA_DIR}/{campaign_name}/results',
            ))
            i += 1
            start += step
    
    return segments
    


# def apply(template_dir, music_video_path, results_dir, offset=0):
#     if not os.path.exists(results_dir):
#         os.makedirs(results_dir)

#     background_name = music_video_path.split('/')[-1].split('.')[0]

#     template_paths = sorted(list(glob.glob(f'{template_dir}/*')))
#     template_names = [template_path.split('/')[-1].split('.')[0] for template_path in template_paths]
#     templates = [VideoFileClip(template_path, has_mask=True) for template_path in template_paths]
#     ntemplates = len(templates)
#     templates_durs = [template.duration for template in templates]
    
#     music_video = VideoFileClip(music_video_path)

#     # if music_video.h != 1080:
#     #     raise Exception(f"Unexpected music video size {music_video.size}")
#     for template in templates:
#         if template.size != [1080, 1920]:
#             raise Exception(f"Unexpected template size {template.size}")

#     music_video = music_video.subclip(10 + offset, music_video.duration - 10)

#     start = 0
#     number = 0
#     itemplate = 0
#     while start + templates_durs[itemplate] < music_video.duration:
#         itemplate = number % ntemplates
#         number += 1
#         for ename, effect in EFFECTS.items():
#             result_path = f"{results_dir}/{background_name};{template_names[itemplate]};{ename};{number}.mp4"

#             if not os.path.exists(result_path):
#                 result = CompositeVideoClip([effect(music_video.subclip(start, start + templates_durs[itemplate]).without_audio()), templates[itemplate]], size=templates[itemplate].size)
#                 result.write_videofile(result_path, threads=6)    
        
#             start += 1


# def all():
#     CAMPAIGNS = [
#         # 'pazljivo',
#         # 'yugofreestyle2',
#         # '10jeali',
#         'dance',
#         'jalabrat',
#     ]
#     for campaign in CAMPAIGNS:
#         results_dir = f'data/{campaign}/results/'

#         if not os.path.exists(results_dir):
#             os.makedirs(results_dir)

#         for music_video_path in glob.glob(f'data/{campaign}/music_videos/*'):
#             print(f"Applying tempaltes on {music_video_path}")
#             apply(f'data/{campaign}/templates', music_video_path, results_dir)

# def process_segments(i, queue):
#     print(f"Starting process {i}...")
#     while not queue.empty():
#         segment = queue.pop()
#         segment.write()
#     print(f"Ending process {i}...")


def process_campaign(campaign_name, step):
    print(f"Processing campaign {campaign_name}")
    segments = create_segments(campaign_name, step=step)
    print(f"Creating {len(segments)} clips")
    random.seed(101010102)
    random.shuffle(segments)

    # queue = mp.Queue()
    # for segment in segments:
    #     queue.put(segment)

    # with mp.Pool(processes) as pool:
    #     pool.map(process_segments, list(zip(range(processes), [q] * processes)))

    for segment in segments:
        segment.write()


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--campaign", help="Name of the campaign", required=True)
    parser.add_argument("-s", "--step", help="How many seconds between start of each video", default=2, type=float)

    # parser.add_argument("-m", "--music_video", help="Music video path")
    # parser.add_argument("-f", "--offset", help="Skip more seconds at begining of background video", default=0, type=int)
    args = parser.parse_args()

    if args.campaign == 'all':
        all()
    else:
        process_campaign(args.campaign, step=args.step)


if __name__ == '__main__':
    main()
