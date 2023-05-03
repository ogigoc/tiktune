import random
import subprocess
from datetime import datetime
import time
import traceback
from urllib.parse import quote
import yaml
import logging as log
log.basicConfig(
    level=log.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        log.FileHandler("tms.log"),
        log.StreamHandler()
    ]
)
import uiautomator2

# MUST_WAIT_ORIGINAL = uiautomator2.UiObject.must_wait
INTERACTIVE = False
ELEMENT_WAIT_TIMEOUT = 30
TIKTOK_START_TIMEOUT = 120

def recover(d):
    # Don't allow contacts or other permissions.
    close_popup_button_re = "Don't allow|Not now"

    close_button = d(textMatches=close_popup_button_re)
    if close_button.exists():
        close_button.click()
        return True

    # Cancel (edditing unposted video)
    if d(text='Keep editing your unposted video?').exists():
        d(text='Cancel').click()
        return True

    # Follow friends dialog
    if d(text='Follow your friends').exists():
        d(clickable=True)[1].click()
        return True

    if d(text='Introducing 10 minutes video').exists():
        d(text='OK').click()
        return True

    if d(text='Community Guidelines Update').exists():
        d(text='Got it').click()
        return True

    if d(text='Allow TikTok to access your contacts?').exists():
        d(text='DENY').click()
        return True

    if d(text='Edit feature enhanced').exists():
        d(clickable=True)[1].click()
        return True

    if d(textMatches='View your friend.{0,3} posts').exists():
        d(clickable=True)[1].click()
        return True

    if d(text='Notifications keep you up to date!').exists():
        d(text='Later').click()
        return True

    if d(text='Turn on notifications?').exists():
        d(text='Not now').click()
        return True

    if d(text='Add TikTok camera shortcut').exists():
        d(clickable=True)[1].click()
        return True

    if d(text='Privacy Policy Update').exists():
        d(text="OK").click()
        return True

    return False

def record_screen(d, device):
    output_path = f"uploader/logs/video/{device}_{str(datetime.now()).split('.')[0].replace(' ', '_')}.mp4"
    log.info(f"Recording screen for {device} to {output_path}")
    d.screenrecord(output_path)

def log_state(d):
    logfile_name = 'uploader/logs/all/' + str(datetime.now()).split('.')[0].replace(' ', '_')
    # dump xml
    open(f'{logfile_name}.xml', 'w').write(d.dump_hierarchy())
    d.screenshot(f'{logfile_name}.jpg')


def uiobject_func_wrapper(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except uiautomator2.exceptions.UiObjectNotFoundError as e:
            log.info(f"Intercepted UIObjectNotFound exception for function {func.__name__}")
            d = args[0].session

            if recover(d):
                log.info(f"\tRecovered!")
                time.sleep(1)
                return func(*args, **kwargs)
            else:
                log.warning(f"\tDid not recover...")
                log_state(d)

                # TODO send telegram
                if INTERACTIVE:
                    import code
                    code.interact(local=locals())
                raise e
    return wrapper


uiautomator2.UiObject.must_wait = uiobject_func_wrapper(uiautomator2.UiObject.must_wait)
uiautomator2.UiObject.click = uiobject_func_wrapper(uiautomator2.UiObject.click)


def retry(func, times=3):
    def wrapper(*args, **kwargs):
        for i in range(times):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                log.warning(f"{func.__name__} failed {i}")

                # get device reference
                d = None
                
                if args and type(args[0]) != uiautomator2.Device:
                    d = args[0]
                if 'd' in kwargs and type(kwargs['d']) == uiautomator2.Device:
                    d = kwargs['d']

                # Reached end of retries.
                if i == times - 1:
                    # dump xml
                    # with open('dump.xml', 'w') as file:
                    #     file.write(d.dump_hierarchy())
                    # TODO send telegram
                    if d:
                        log_state(d)
                    raise e

                # here we retry, also try to recover from popups and other problems
                if d:
                    recover(d)
                else:
                    log.warning(f"Cannot recover in retry, no device argument.")
    return wrapper



@retry
def switch_to_account(d, username, display_name):
    log.info("Opening tiktok app")
    d.app_stop('com.zhiliaoapp.musically')
    d.app_start("com.zhiliaoapp.musically", 'com.ss.android.ugc.aweme.splash.SplashActivity') # start with package name
    time.sleep(3)

    select(d, timeout=TIKTOK_START_TIMEOUT, text='Profile').click()
    time.sleep(10)

    recover(d)
    account_switcher = d(index=0, className='android.widget.TextView', clickable=True, textMatches='.{3,}')[0]
    account_text = account_switcher.get_text()
    log.info(f"Currently on account: {account_text}")
    if account_text == display_name:
        log.info(f"Already at on account {display_name}")
        return
    else:
        account_switcher.click()
        d(textMatches=f"{display_name}|{username}").click()
        log.info(f"Switched to new account {username}")
    
@retry
def upload_latest_video_to_sound(d, title, tags, sound_url, sound_name, device):
    
    
    title = title + ' ' + ' '.join(['#' + t for t in tags])

    if sound_url:
        log.info(f"Opening sound {sound_url}")
        d.open_url(sound_url)
        time.sleep(3)

        d(text='Use this sound').click()
    else:
        log.info("Opening tiktok app")
        d.app_stop('com.zhiliaoapp.musically')
        d.app_start("com.zhiliaoapp.musically", 'com.ss.android.ugc.aweme.splash.SplashActivity') # start with package name
        time.sleep(3)

        log.info('Clicking upload button')
        select(d, timeout=TIKTOK_START_TIMEOUT, index=2, className='android.widget.FrameLayout')[-1].click()

    # "upload" button
    d(text='Upload').click()

    d(text='Videos').click()
    time.sleep(2)

    # Click first video
    d(textMatches='\d\d:\d\d')[0].click()
    time.sleep(30)

    # if device == 'redminote':
    #     d(text='Next').click()

    if sound_url:
        time.sleep(5)
        log.info(f"Clicking sound name {sound_name}")
        d(textMatches=f'{sound_name}.*').click()

        d(text='Volume').click()
        time.sleep(3)

        if device == 'redminote':
            log.info("Set original sound to 100%")
            d.click(685, 1728)
            log.info("Set added sound to 1%")
            d.click(350, 1934)
        elif device == 'j7ana_6':
            log.info("Set original sound to 100%")
            d.click(680, 1460)
            log.info("Set added sound to 1%")
            d.click(336, 1656)
        elif device.startswith('j7pro'):
            log.info("Set original sound to 100%")
            d(className='android.widget.SeekBar')[0].click(offset=(0.485, 0.5))
            log.info("Set added sound to 1%")
            d(className='android.widget.SeekBar')[1].click(offset=(0.041, 0.5))
        elif device.startswith('j7'):
            log.info("Set original sound to 100%")
            d.click(466, 929)
            log.info("Set added sound to 1%")
            d.click(256, 1079)
        elif device.startswith('k22'):
            log.info("Set original sound to 100%")
            d(className='android.widget.SeekBar')[0].click(offset=(0.48, 0.5))
            log.info("Set added sound to 1%")
            d(className='android.widget.SeekBar')[1].click(offset=(0.049, 0.5))
        else:
            raise Exception(f"Unsupported device {device}")

        d(text='Done').click()

    d(text='Next').click()

    d(textMatches="(Describe your post|Share your thoughts|Share what).*").set_text(title)
    time.sleep(10)
    d.press('back')
    time.sleep(3)

    # log.info('Disable save to device')
    # d(text='Save to device').click()

    log.info('Posting video')
    d(text='Post')[-1].click()
    time.sleep(5)

    if d(text='Post video').exists():
        d(text='Post video').click()

    time.sleep(5)

    if d(textMatches='Post [nN]ow').exists():
        d(textMatches='Post [nN]ow').click()
    
    time.sleep(40)

@retry
def get_link(d):
    # wait for video to be opened
    log.info("Waiting for video to open!")
    good = False
    for i in range(30):
        if len(d(text='0')) == 3:
            good = True
            break
        time.sleep(1)
    
    if not good:
        d(text='Profile').click()
        d(index=0, className="androidx.recyclerview.widget.RecyclerView").child()[0].click()

    log.info(f"Video opened!")

    # Save linka
    d(index=5, clickable=True, focusable=True).click()
    d(text='Copy link').click()

    d(textMatches='Find friends|Find related content')[0].click()
    time.sleep(1)
    d(focused=True).long_click()
    d(textMatches='Paste|PASTE').click()

    link = d(focused=True).get_text()
    log.info(link)
    return link

@retry
def transfer_video(d, video_path, device):
    video_name = video_path.split('/')[-1]
    if device == 'redminote':
        d.push(video_path, f'/sdcard/DCIM/Camera/{video_name}')

        d.app_stop('com.miui.videoplayer')
        d.app_start('com.miui.videoplayer')
        d(text='Local').click()

        @retry
        def refresh_videos(d):
            time.sleep(2)
            d.swipe_ext('down')
            time.sleep(2)

            if not d(text=video_name).exists():
                raise Exception(f"Video {video_path} transfered but not found in files.")

        refresh_videos(d)
    elif device.startswith('j7'):
        log.info(f"Deleting all downloaded videos...")
        d.shell('rm /storage/self/primary/Download/*')
        d.shell('rm /storage/self/primary/DCIM/Camera/*')

        url = f'http://100.115.146.73:8080/{quote(video_path)}'
        # log.info(url)
        # quit()
        log.info(f"Fetching new video on url {url}")
        d.open_url(url)
        time.sleep(10)

        log.info(f"Clicking Download button if it exists...")
        if d(text='Download').exists():
            log.info(f"It exists, clicking...")
            d(text='Download').click()
        time.sleep(10)
        
        d.open_url('http://about:blank')
        time.sleep(10)

        log.info("Opening files app...")
        d.app_stop('com.sec.android.app.myfiles')
        d.app_start('com.sec.android.app.myfiles')
        log.info("Clicking videos...")
        d(text='Videos').click()

        if not device.startswith('j7old'):
            log.info("Clicking Download...")
            d(text='Download').click()

        if not d(text=video_name).exists() and not d(text='‎' + video_name).exists():
            raise Exception(f"Video {video_path} transfered but not found in files.")

        log.info(f"Video found in files!, done!")

        # import code
        # code.interact(local=locals())
        # >>> d.shell('ls storage/self/primary/DCIM/Camera').output.replace('\n', ' ')
    elif device.startswith('k22'):
        log.info(f"Deleting all downloaded videos...")
        d.shell('rm /storage/self/primary/Download/*')
        d.shell('rm /storage/self/primary/DCIM/Camera/*')
        time.sleep(1)
        
        log.info(f"Pushing  video {video_path} to device...")
        d.push(video_path, f'/storage/self/primary/Download/{video_name}')

        log.info(f"Frocing media scan...")
        time.sleep(1)
        output, code = d.shell(f'am broadcast -a android.intent.action.MEDIA_SCANNER_SCAN_FILE -d "file:///storage/self/primary/Download/{video_name}"')
        log.info(f"Media scan done! with code {code} and output {output}")
        time.sleep(2)
        
        d.app_stop('com.google.android.apps.nbu.files')
        d.app_start('com.google.android.apps.nbu.files', '.home.HomeActivity')
        d(text='Downloads').click()

        time.sleep(5)

        if not d(text=video_name).exists() and not d(text='‎' + video_name).exists():
            # # try internal storag first
            # log.info(f"Video not found in downloads, trying internal storage...")
            # d.app_stop('com.google.android.apps.nbu.files')
            # d.app_start('com.google.android.apps.nbu.files', '.home.HomeActivity')
            # d.swipe_ext('up')
            # d(text='Internal Storage').click()
            # d(text='Download').click()

            # if not d(text=video_name).exists() and not d(text='‎' + video_name).exists():
            raise Exception(f"Video {video_path} transfered but not found in files.")

        log.info(f"Video found in files!, done!")

    else:
        raise Exception(f"Unsupported device {device}")


@retry
def unlock(d):
    d.screen_off()
    time.sleep(5)
    d.unlock()
    time.sleep(5)
    
    # output, code = d.shell(f'dumpsys window policy | grep isStatusBarKeyguard')
    # if 'isStatusBarKeyguard=false' not in output:
    #     log.warn(f"Unlock failed")
    #     raise Exception(f"Device not unlocked")


def select(d, timeout=ELEMENT_WAIT_TIMEOUT, **kwargs):
    log.debug(f"Selecting {params_to_string(kwargs)}")

    if d(**kwargs).exists():
        return d(**kwargs)

    end = time.time() + timeout

    while time.time() < end:
        if recover(d):
            log.info(f"Recovered from popup")
        
        if d(**kwargs).exists():
            return d(**kwargs)
        
        time.sleep(1)

    raise Exception(f"Element {params_to_string(kwargs)} not found")


def upload_video(account, video, title, tags, sound_url, sound_name, device_id, device):
    d = uiautomator2.connect(device_id) # connect to device
    d.implicitly_wait(30)
    d.jsonrpc.setConfigurator({"waitForIdleTimeout": 100, 'waitForSelectorTimeout': 100})

    recording = False
    try:
        if not account.name:
            raise Exception(f"Account name empty")

        log.info(f"Connecting to adb...")
        adb_connect(device_id)
        time.sleep(1)

        if device == 'j7':
            record_screen(d, device)
            recording = True

        log.info(f"Unlocking device {device}")
        unlock(d)
        
        log.info(f"Transfering video {video} to device {d}")
        transfer_video(d, video, device)
        time.sleep(3)
                
        log.info(f"Switching tiktok to account {account.username},{account.name}")
        switch_to_account(d, account.username, account.name)
        time.sleep(10)

        log.info(f"Uploading video...")
        upload_latest_video_to_sound(d, title, tags, sound_url, sound_name, device)

        if recording:
            d.screenrecord.stop()
            recording = False

        return d
    except Exception as e:
        if recording:
            d.screenrecord.stop()
            recording = False
        log.info(f"Upload failed with {e}")

        log_state(d)

        traceback.print_exc()
        raise e

    if recording:
        d.screenrecord.stop()
        recording = False


def cleanup(d):
    d.app_stop('com.zhiliaoapp.musically')
    d.screen_off()

def params_to_string(params):
    string_values = [
        v[0].upper() + v[1:] if v in {'true', 'false'} else int(v) if v.isnumeric() else f'"{v}"'
        for v in [str(val) for val in params.values()]
    ]
    return f'({", ".join(str(k) + "=" + str(v) for k,v in zip(params.keys(), string_values))})'


def find(d, nodes):
    for node in nodes.split('\n'):
        elems = dict([
            [elem.split('=')[0], elem.split('=')[1][1:-1]]
            for elem in node.split(' ')
            if '=' in elem
        ])

        useful = {
            'index': 'index',
            'class': 'className',
            'checkable': 'checkable',
            'checked': 'checked',
            'clickable': 'clickable',
            'enabled': 'enabled',
            'focusable': 'focusable',
            'focused': 'focused',
            'scrollable': 'scrollable',
            'selected': 'selected',
        }

        params = {
            useful[key]: val
            for key, val in elems.items()
            if key in useful
        }

        print(f'd{params_to_string(params)}')
        print(len(d(**params)))
        print()


# def sign_up():
#     d(text='Use phone or email').click()
#     d(text='Email').click()
#     d.send_keys('dijana@fireweb.site')
#     d(text='Next').click()
#     d.send_keys('droga123di.')
#     d(text='Next').click()

#     import random
#     for i in range(random.randint(0, 30)):
#     d(className='android.view.View')[-1].swipe('down')

#     d(text='Next').click()
#     d.send_keys('Dijana Music')

@retry
def adb_connect(device_id):
    cmd = subprocess.run(f'adb connect {device_id}', shell=True)
    cmd.check_returncode()


def next_video(d):
    d.swipe(
        0.4 + random.uniform(-0.05, 0.05),
        0.6 + random.uniform(-0.05, 0.05),
        0.4 + random.uniform(-0.05, 0.05),
        0.4 + random.uniform(-0.05, 0.05),
        0.03,
    )


def infi_scroll(d):
    while True:
        time.sleep(random.uniform(1.2, 8))
        log.info(f"Scrolling...")
        next_video(d)

def main():
    global INTERACTIVE
    INTERACTIVE=True

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--device", help="Name of the device to connect to", required=True)

    with open('devices.yaml', 'r') as file:
        devices = yaml.safe_load(file)

    args = parser.parse_args()

    device_id = devices[args.device]['device_id']

    adb_connect(device_id)

    d = uiautomator2.connect(device_id) # connect to device
    # d.app_start("com.zhiliaoapp.musically", 'com.ss.android.ugc.aweme.splash.SplashActivity')
    d.implicitly_wait(8)

    import code
    code.interact(local=dict(globals(), **locals())) 



    class Account:
        def __init__(self, username, name):
            self.username = username
            self.name = name
    upload_video(Account(username='bambiguza', name='Bambi GUza'), 'zoo20.mp4', 'Test title', ['test'], "Srce luduje", 'https://www.tiktok.com/music/Srce-luduje-7206151702318189317')


if __name__ == '__main__':
    main()
