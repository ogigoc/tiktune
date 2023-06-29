import re
import subprocess
import yaml
import os
import glob
import random
import multiprocessing as mp

from scenedetect import detect, ContentDetector
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
    def __init__(self, start, template, background, effect, effect_name, output_dir, background_filename=None, start_name=None):
        self.start = start
        if start_name:
            self.start_name = start_name
        else:
            self.start_name = self.start
        self.template = template
        self.background = background
        if not background_filename:
            self.background_filename = background.filename
        else:
            self.background_filename = background_filename
        self.effect = effect
        self.effect_name = effect_name
        self.output_dir = output_dir
        self.output_path = (
            f'{output_dir}/{str(round(self.start_name)).zfill(5)};{self.background_filename.split("/")[-1].replace("/", "").replace(";", "")};{self.template.filename.split("/")[-1]};'
            f'{self.effect_name}.mp4'
        )
    
    def write(self):
        if not os.path.isdir(self.output_dir):
            os.makedirs(self.output_dir)

        if os.path.exists(self.output_path):
            print(f"Skipping {self.output_path}")
            return

        print(f"Rendering {self.output_path}")
        result = CompositeVideoClip([
            self.effect(self.background.subclip(self.start, self.start + self.template.duration).without_audio()),
            self.template
        ], size=self.template.size)

        try:
            result.write_videofile(self.output_path)
        except IndexError:
            # Short by one frame, so get rid on the last frame:
            result = result.subclip(t_end=(result.duration - 1.0/result.fps))
            result.write_videofile(self.output_path)
            result.write_videofile(self.output_path)
        except Exception as e:
            raise e


def create_segments(campaign_name, step, bstart=3, bend=3, template="", background="", output_dir="results"):
    print(f"Loading templates for campaign {campaign_name}")
    template_paths = [template] if template else sorted(list(glob.glob(f'{DATA_DIR}/{campaign_name}/templates/*')))
    templates = [
        VideoFileClip(path, has_mask=True)
        for path in template_paths
    ]
    print(f"Found {len(templates)} templates for {campaign_name}")
    if not templates:
        raise Exception(f"No templates for {campaign_name}")

    print(f"Loading backgrounds for campaign {campaign_name}")
    background_paths = [background] if background else sorted(list(glob.glob(f'{DATA_DIR}/{campaign_name}/music_videos/*'))) 
    backgrounds = [
        VideoFileClip(path)
        for path in background_paths
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
                output_dir=f'{DATA_DIR}/{campaign_name}/{output_dir}',
            ))
            i += 1
            start += step
    
    return segments



def create_segments_scenes(campaign_name, template, background, cut_timings, n, output_dir="results.scenes"):
    if not os.path.isdir(f'{DATA_DIR}/{campaign_name}/{output_dir}'):
        os.makedirs(f'{DATA_DIR}/{campaign_name}/{output_dir}')
    existing_clips = os.listdir(f'{DATA_DIR}/{campaign_name}/{output_dir}')
    results = 0
    if existing_clips:
        results = max([int(re.search(r'(\d{5});', clip).group(1)) for clip in existing_clips])

    print(f"Loading background and breaking into scenes")
    scenes = detect(background, ContentDetector())
    print(f"Found {len(scenes)} scenes")

    print(f"Remobing short scenese")
    max_timing = max([end - start for start, end in zip(cut_timings, cut_timings[1:])])
    print(f"Max timing: {max_timing}")
    print(f"Scene 1 length: {scenes[0][1].get_seconds() - scenes[0][0].get_seconds()}")
    scenes = [
        scene
        for scene in scenes
        if scene[1].get_seconds() - scene[0].get_seconds() > max_timing
    ]
    print(f"{len(scenes)} scenes left")

    if len(scenes) < len(cut_timings) - 1:
        raise Exception(f"Not enough scenes for {len(cut_timings)} cuts")

    scene_idxs = list(range(len(scenes)))
    
    permutations = set()
    template = VideoFileClip(template, has_mask=True)

    while results < n:
        random.shuffle(scene_idxs)
        random_perm = tuple(scene_idxs)
        if random_perm in permutations:
            print("Used permutation, skipping")
            continue

        permutations.add(random_perm)
        # check if permutation is valid
        if any(
            not (end - start < scenes[random_perm[i]][1].get_seconds() - scenes[random_perm[i]][0].get_seconds())
            for i, (start, end) in enumerate(zip(cut_timings, cut_timings[1:]))
        ):
            print("Invalid permutation, skipping")
            continue
        
        # create segment
        # background_video = VideoFileClip(background)
        # scene_segments = [
        #     background_video.subclip(scenes[random_perm[i]][0].get_seconds(), scenes[random_perm[i]][0].get_seconds() + (cut_timings[i + 1] - cut_timings[i]))
        #     for i in range(len(cut_timings) - 1)
        # ]

        filtergraph = ';'.join(
            [f"[0:v]trim=start={scenes[random_perm[i]][0].get_seconds()}:end={scenes[random_perm[i]][0].get_seconds() + (cut_timings[i + 1] - cut_timings[i])},setpts=PTS-STARTPTS[v{i}];"
            f"[0:a]atrim=start={scenes[random_perm[i]][0].get_seconds()}:end={scenes[random_perm[i]][0].get_seconds() + (cut_timings[i + 1] - cut_timings[i])},asetpts=PTS-STARTPTS[a{i}]" for i in range(len(cut_timings) - 1)]
        ) + ';' + ''.join([f"[v{i}][a{i}]" for i in range(len(cut_timings) - 1)]) + f"concat=n={len(cut_timings) - 1}:v=1:a=1[outv][outa]"

        # Run FFmpeg command with the built filtergraph
        subprocess.call(['ffmpeg', '-i', background, '-filter_complex', filtergraph, '-map', '[outv]', '-map', '[outa]', 'template_cuts_tmp.mp4', '-y'])
        import time
        time.sleep(1)

        # concatenate
        result = VideoFileClip('template_cuts_tmp.mp4')
        print("Concatenated durations")
        print(result.duration)
        print(template.duration)

        # result.write_videofile('test.mp4')
        # quit()

        segment = Segment(
            start=0,
            template=template,
            background=result,
            effect=EFFECTS["full_zoom"],
            effect_name="full_zoom",
            output_dir=f'{DATA_DIR}/{campaign_name}/{output_dir}',
            background_filename=background.split('/')[-1].split('.')[0],
            start_name=results,
        )
        
        # os.remove('template_cuts_tmp.mp4')

        segment.write()
        results += 1
        print(f"Created {results} segments")

        
                



    

    


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

def time_to_seconds(time_str):
    parts = time_str.split(':')

    hours = int(parts[0])
    minutes = int(parts[1])
    seconds = int(parts[2])
    milliseconds = float(f'0.{parts[3]}')

    total_seconds = (hours * 3600) + (minutes * 60) + seconds + milliseconds
    return total_seconds

def process_campaign(campaign_name, step, template="", background="", output_dir="results", function="simple", n=100, bstart=0, bend=0):
    print(f"Processing campaign {campaign_name}")
    if function == "simple":
        segments = create_segments(campaign_name, step=step, template=template, background=background, output_dir=output_dir, bstart=bstart, bend=bend)
    elif function == "scenes":
        # read campaign cut timings
        with open('../campaigns.yaml', 'r') as file:
            campaign = yaml.safe_load(file)[campaign_name]
            try:
                template_dict = next(t for t in campaign['templates'] if t['path'] == template)
            except StopIteration:
                raise Exception(f"Template {template} not found in campaign {campaign_name}")
            timings = [
                time_to_seconds(time)
                for time in template_dict['timings']
            ]
            print(f"Cut timings: {timings}")

        segments = create_segments_scenes(campaign_name, template=template, background=background, output_dir=output_dir, cut_timings=timings, n=n)
    else:
        raise Exception(f"Unknown function {function}")
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
    parser.add_argument("-t", "--template", help="Template video path", default="")
    parser.add_argument("-b", "--background", help="Background video path", default="")
    parser.add_argument("-o", "--output", help="Output directory name", default="results")
    parser.add_argument("-f", "--function", help="Fucntion to apply to create segments", default="simple")
    parser.add_argument("-n", "--number", help="Number of videos to create", default=100, type=int)
    parser.add_argument("--bstart", help="Start time of the background video in seconds", default=3, type=int)
    parser.add_argument("--bend", help="End time of the background video in seconds", default=3, type=int)

    # parser.add_argument("-f", "--offset", help="Skip more seconds at begining of background video", default=0, type=int)
    args = parser.parse_args()

    if args.campaign == 'all':
        all()
    else:
        process_campaign(args.campaign, step=args.step, template=args.template, background=args.background, output_dir=args.output, function=args.function, n=args.number, bstart=args.bstart, bend=args.bend)


if __name__ == '__main__':
    main()
