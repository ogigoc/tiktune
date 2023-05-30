from typing import Any
import yaml
import random
import logging
import os
import time
import subprocess
import re
from datetime import datetime
import requests

import uiautomator2
import adbutils

from uploader import utils


class UIAutomatorDevice():

    ATTRIBUTES_TO_OVERRIDE = [
        'app_start',
        'app_stop',
        'click',
        'drag',
        'dump_hierarchy',
        'open_url',
        'press',
        'push',
        'screen_off',
        'screenshot',
        'shell',
        'swipe',
        'swipe_ext',
        'unlock',
    ]

    def __init__(self, android_device):
        self.android_device = android_device
        self.retries = 3

        for i in range(3):
            try:
                self.connect()
                break
            except Exception as e:
                self.android_device.log.error(f"Failed to connect to device {self.android_device.name} {self.android_device.id} with error {e}")
                self.android_device.log.error(f"Retrying {i}...")

                if i == 2:
                    self.android_device.log.error(f"Failed all retries to connect to device {self.android_device.name} {self.android_device.id}")
                    raise e

    def connect(self):
        self.android_device.log.info(f"Connecting to device {self.android_device.name} {self.android_device.id}")
        # connect adb first
        if self.android_device.remote:
            self.android_device.log.info(f"Connecting adb to remote device {self.android_device.name} {self.android_device.id}")
            cmd = subprocess.run(f'adb connect {self.android_device.id}', shell=True)
            if cmd.returncode != 0:
                self.android_device.log.error(f"Failed to connect to device {self.android_device.name} {self.android_device.id} with output {cmd.stdout}")
                raise Exception(f"Failed to connect to device {self.android_device.name} {self.android_device.id} with output {cmd.stdout}")
        else:
            self.android_device.log.info(f"Connecting adb to usb device {self.android_device.name} {self.android_device.id}")
            cmd = subprocess.run(f'adb -s {self.android_device.id} reconnect', shell=True)
            if cmd.returncode != 0:
                self.android_device.log.error(f"Failed to connect to device {self.android_device.name} {self.android_device.id} with output {cmd.stdout}")
                raise Exception(f"Failed to connect to device {self.android_device.name} {self.android_device.id} with output {cmd.stdout}")
        
        # connect uiautomator2
        self.android_device.log.info(f"Connecting uiautomator2 to device {self.android_device.name} {self.android_device.id}")
        if self.android_device.remote:
            self.d = uiautomator2.connect(self.android_device.id)
        else:
            self.d = uiautomator2.connect_usb(self.android_device.id)
        self.d.jsonrpc.setConfigurator({"waitForIdleTimeout": 100, 'waitForSelectorTimeout': 100})
        self.d.healthcheck()

        self.android_device.log.info(f"Connected to device {self.android_device.name} {self.android_device.id}")

    def try_func(self, func, retries, *args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (adbutils.errors.AdbError, ConnectionResetError, RuntimeError, requests.exceptions.ConnectionError) as e:
            if isinstance(e, RuntimeError) and not re.search('USB device.*is offline', str(e)):
                raise e
            self.android_device.log.warning(f"{str(e.__class__)} Error: {e}")
            if retries > 0:
                self.android_device.log.warning(f"Retrying {retries} {str(func)} with args")
                time.sleep(1)
                if retries == 1:
                    time.sleep(15)
                self.connect()
                return self.try_func(func, retries-1, *args, **kwargs)
            else:
                self.android_device.log.error(f"Failed all retries to run {str(func)} with args {args} and kwargs {kwargs}")
                raise e

    def __getattr__(self, attr):
        if attr in self.ATTRIBUTES_TO_OVERRIDE:
            def wrapper(*args, **kwargs):
                return self.try_func(getattr(self.d, attr), self.retries, *args, **kwargs)
            return wrapper
        else:
            return getattr(self.d, attr)
        
    def __call__(self, *args, **kwargs):
        return self.try_func(self.d, self.retries, *args, **kwargs)


class AndroidDevice():
    ELEMENT_WAIT_TIMEOUT = 30
    TIKTOK_START_TIMEOUT = 120
    PLUS_X = 0.5
    DOWNLOADS_PATH = '/storage/self/primary/Download'
    CAMERA_PATH = '/storage/self/primary/DCIM/Camera'

    def __init__(self, name, id, accounts, interactive=False):
        self.name = name
        self.id = id
        self.remote = utils.is_ip_address(id)
        self.accounts = list(accounts)
        self.interactive = interactive

        self.d = None

        # init logger for this device
        self.log_dir = f"logs/{self.name}"
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        
        self.log = logging.getLogger(f"android.{self.name}")
        self.log.setLevel(logging.DEBUG)
        if self.log.hasHandlers():
            self.log.handlers.clear()
        formatter = logging.Formatter(f"%(asctime)s [%(levelname)s] {self.name} %(message)s")
        file_handler = logging.FileHandler(f"{self.log_dir}/main.log")
        file_handler.setFormatter(formatter)
        self.log.addHandler(file_handler)
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        self.log.addHandler(stream_handler)
    
    def __str__(self):
        return f"Device {self.model} {self.name} {self.id}"
    
    def log_state(self):
        self.log.info(f"Saving current state of device {self.name} {self.id}")
        logfile_name = f'{self.log_dir}/' + str(datetime.now()).split('.')[0].replace(' ', '_')
        open(f'{logfile_name}.xml', 'w').write(self.d.dump_hierarchy())
        self.d.screenshot(f'{logfile_name}.jpg')

    def connect(self):
        try:
            self.d = UIAutomatorDevice(self)
        except Exception as e:
            time.sleep(2)
            self.d = UIAutomatorDevice(self)
    
    def connected(self):
        return self.d is not None
    
    def unlock(self):
        self.log.info(f"Unlocking device {self.name} {self.id}")
        self.d.screen_off()
        time.sleep(5)
        self.d.unlock()
        time.sleep(5)
        self.log.info(f"Unlocked device {self.name} {self.id}")
        
    def lock(self):
        self.d.app_stop('com.zhiliaoapp.musically')
        self.d.screen_off()
        self.log.info(f"Locked device {self.name} {self.id}")

    def recover(self):
        try:
            self.log.debug(f"Running recover procedure...")

            # Don't allow contacts or other permissions.
            close_popup_button_re = "Don't allow|Not now|Close"

            close_button = self.d(textMatches=close_popup_button_re)
            if close_button.exists():
                close_button.click()
                return True

            # Cancel (edditing unposted video)
            popup_text = 'Keep editing your unposted video?'
            if self.d(text=popup_text).exists():
                self.log.info(f"Found popup with text {popup_text}")
                self.d(text='Cancel').click()
                return True

            # Follow friends dialog
            popup_text = 'Follow your friends'
            if self.d(text=popup_text).exists():
                self.log.info(f"Found popup with text {popup_text}")
                self.d.click(0.5, 0.11)
                return True

            popup_text = 'Introducing 10 minutes video'
            if self.d(text=popup_text).exists():
                self.log.info(f"Found popup with text {popup_text}")
                self.d(text='OK').click()
                return True

            popup_text = 'Community Guidelines Update'
            if self.d(text=popup_text).exists():
                self.log.info(f"Found popup with text {popup_text}")
                self.d(text='Got it').click()
                return True

            popup_text = 'Allow TikTok to access your contacts?'
            if self.d(text=popup_text).exists():
                self.log.info(f"Found popup with text {popup_text}")
                self.d(text='DENY').click()
                return True

            popup_text = 'Edit feature enhanced'
            if self.d(text=popup_text).exists():
                self.log.info(f"Found popup with text {popup_text}")
                self.d(clickable=True)[1].click()
                return True

            popup_text = 'View your friend.{0,3} posts'
            if self.d(textMatches=popup_text).exists():
                self.log.info(f"Found popup with text {popup_text}")
                self.d(clickable=True)[1].click()
                return True

            popup_text = 'Notifications keep you up to date!'
            if self.d(text=popup_text).exists():
                self.log.info(f"Found popup with text {popup_text}")
                self.d(text='Later').click()
                return True

            popup_text = 'Turn on notifications?'
            if self.d(text=popup_text).exists():
                self.log.info(f"Found popup with text {popup_text}")
                self.d(text='Not now').click()
                return True

            popup_text = 'Add TikTok camera shortcut'
            if self.d(text=popup_text).exists():
                self.log.info(f"Found popup with text {popup_text}")
                self.d(clickable=True)[1].click()
                return True

            popup_text = 'Privacy Policy Update'
            if self.d(text=popup_text).exists():
                self.log.info(f"Found popup with text {popup_text}")
                self.d(text="OK").click()
                return True
            
            popup_text = 'TikTok is better with friends!'
            if self.d(text=popup_text).exists():
                self.log.info(f"Found popup with text {popup_text}")
                self.d(text="Skip").click()
                time.sleep(1)
                self.d(text="Skip").click()
                return True

            popup_text = 'Failed to upload and has been saved to drafts.'
            if self.d(text=popup_text).exists():
                self.log.info(f"Found popup with text {popup_text}")
                self.d(className='android.widget.ImageView', index=3)[-1].click()
                return True
            
            popup_text = 'Add to Home screen?'
            if self.d(text=popup_text).exists():
                self.log.info(f"Found popup with text {popup_text}")
                self.d(text='Cancel').click()
                return True
                   
            popup_text = 'Add to Home screen'
            if self.d(text=popup_text).exists():
                self.log.info(f"Found popup with text {popup_text}")
                self.d(text='CANCEL').click()
                return True
            
            popup_text = 'Family Pairing.*'
            if self.d(textMatches=popup_text).exists():
                self.log.info(f"Found popup with text {popup_text}")
                self.d(text='Not interested').click()
                return True
            
            popup_text = 'Attention'
            if self.d(text=popup_text).exists():
                self.log.info(f"Found popup with text {popup_text}")
                self.d(text='OK').click()
                return True
            
            popup_text = 'Install update to keep device secure'
            if self.d(text=popup_text).exists():
                self.log.info(f"Found popup with text {popup_text}")
                self.d(text='Remind me later').click()
                return True
                        
            popup_text = 'Allow TikTok to take pictures and record video?'
            if self.d(text=popup_text).exists():
                self.log.info(f"Found popup with text {popup_text}")
                self.d(text='ALLOW').click()
                return True
            
            popup_text = 'Allow TikTok to access photos, media and files on your device?'
            if self.d(text=popup_text).exists():
                self.log.info(f"Found popup with text {popup_text}")
                self.d(text='ALLOW').click()
                return True
                        
            popup_text = 'Allow TikTok to record audio?'
            if self.d(text=popup_text).exists():
                self.log.info(f"Found popup with text {popup_text}")
                self.d(text='ALLOW').click()
                return True
                        
            popup_text = 'Use USB for'
            if self.d(text=popup_text).exists():
                self.log.info(f"Found popup with text {popup_text}")
                self.d(text='Cancel').click()
                return True
            
            self.log.debug(f"Didn't find any popup to close")
            return False
        except (adbutils.errors.AdbError, ConnectionResetError, RuntimeError, requests.exceptions.ConnectionError) as e:
            if isinstance(e, RuntimeError) and not re.search('USB device.*is offline', str(e)):
                raise e
            self.log.error(f"Recovery failed {str(e.__class__)} Error: {e}")
            raise e
    
    def shell(self, cmd):
        self.log.info(f"Running adb shell {cmd}")
        output, code = self.d.shell(cmd)
        if code != 0:
            self.log.error(f"Failed to adb shell {cmd} with output {output}")
            raise Exception(f"Failed to run {cmd} with output {output}")

    def try_shell(self, cmd):
        try:
            self.shell(cmd)
        except:
            pass

    def select(self, timeout=ELEMENT_WAIT_TIMEOUT, retry=3, **kwargs):
        self.log.debug(f"Selecting {utils.params_to_string(kwargs)}")
        try:
            element = self.d(**kwargs)
            if element.exists():
                return element

            current_time = time.time()
            end = current_time + timeout
            try_recovery = current_time + (timeout / 2)

            while time.time() < end:
                if time.time() > try_recovery and self.recover():
                    self.log.debug(f"Recovered from popup")

                element = self.d(**kwargs)
                if element.exists():
                    self.log.debug(f"Element {utils.params_to_string(kwargs)} exists returning")
                    return element
                time.sleep(1)
        except (adbutils.errors.AdbError, ConnectionResetError, RuntimeError, requests.exceptions.ConnectionError) as e:
            if isinstance(e, RuntimeError) and not re.search('USB device.*is offline', str(e)):
                raise e
            self.log.warning(f"Select {str(e.__class__)} Error: {e}")
            if retry > 0:
                self.log.warning(f"Retrying select {retry}")
                time.sleep(1)
                self.d.connect()
                if retry == 1:
                    time.sleep(15)
                return self.select(timeout=timeout, retry=retry-1, **kwargs)
            else:
                self.log.error(f"Failed all retries to select {utils.params_to_string(kwargs)}[{idx}]")
                raise e

        raise Exception(f"Element {utils.params_to_string(kwargs)} not found")
    
    def exists(self, timeout, **kwargs):
        self.log.debug(f"Checking if {utils.params_to_string(kwargs)} exists")
        try:
            self.select(timeout=timeout, **kwargs)
            return True
        except:
            return False
    
    def click(self, message="", idx=None, timeout=ELEMENT_WAIT_TIMEOUT, retry=1, **kwargs):
        message_alternatives = [
            'description',
            'text',
            'textMatches',
            'resourceId',
            'resourceIdMatches',
        ]
        if not message:
            for alternative in message_alternatives:
                if alternative in kwargs:
                    message = kwargs[alternative]
                    break
        if not message:
            raise Exception(f"Click called without message and no {', '.join(message_alternatives)} in kwargs")

        self.log.info(f"Clicking {message} with selector {utils.params_to_string(kwargs)}[{idx}]")
        try:
            element = self.select(timeout=timeout, **kwargs)
            if idx is not None:
                element = element[idx]

            self.log.debug(f"Clicking element {utils.params_to_string(kwargs)}[{idx}]")
            element.click()
            time.sleep(0.1)
        except uiautomator2.exceptions.UiObjectNotFoundError as e:
            self.log.warning(f"Element {utils.params_to_string(kwargs)} exists but cannot be clicked")
            if retry:
                self.log.warning(f"Retrying click on {utils.params_to_string(kwargs)}")
                self.recover()
                return self.click(message=message, idx=idx, timeout=timeout, retry=retry-1, **kwargs)
            else:
                self.log.error(f"Element {utils.params_to_string(kwargs)} exists but cannot be clicked")
                raise e
        except (adbutils.errors.AdbError, ConnectionResetError, RuntimeError, requests.exceptions.ConnectionError) as e:
            if isinstance(e, RuntimeError) and not re.search('USB device.*is offline', str(e)):
                raise e
            self.log.warning(f"Click {str(e.__class__)} Error: {e}")
            if retry > 0:
                self.log.warning(f"Retrying click {retry} {message}")
                time.sleep(1)
                if retry == 1:
                    time.sleep(15)
                self.d.connect()
                return self.click(message=message, idx=idx, timeout=timeout, retry=retry-1, **kwargs)
            else:
                self.log.error(f"Failed all retries to click {message} with selector {utils.params_to_string(kwargs)}[{idx}]")
                raise e


    def click_exists(self, message="", idx=0, timeout=ELEMENT_WAIT_TIMEOUT, **kwargs):
        try:
            self.click(message=message, idx=idx, timeout=timeout, **kwargs)
            return True
        except:
            return False

    def transfer_file(self, file_path, delete=True):
        file_name = os.path.basename(file_path)
        self.log.info(f"Transferring file {file_path} to device")
        
        if delete:
            self.log.info(f"Deleting all downloads...")
            self.try_shell(f'rm {self.DOWNLOADS_PATH}/*')
            self.try_shell(f'rm {self.CAMERA_PATH}/*')

        self.log.info(f"Pushing  file {file_path} to device...")
        self.d.push(file_path, f'{self.DOWNLOADS_PATH}/{file_name}')
        time.sleep(1)

        self.log.info(f"Frocing media scan...")
        self.shell(f'am broadcast -a android.intent.action.MEDIA_SCANNER_SCAN_FILE -d "file://{self.DOWNLOADS_PATH}/{file_name}"')
        time.sleep(5)
    
    def transfer_video(self, video_path):
        self.log.error(f"Transfer video called on base device class, this needs to be implemented in each device class")
        raise Exception(f"Transfer video called on base device class, this needs to be implemented in each device class")
    
    def switch_to_account(self, account):
        self.click(timeout=self.TIKTOK_START_TIMEOUT, text='Profile')

        account_names = [account.username for account in self.accounts] + [account.name for account in self.accounts]
        account_names_re = '|'.join(account_names)
        self.log.debug(f"Getting account switcher with regex {account_names_re}")
        try:
            current_account = self.select(textMatches=account_names_re)[0].get_text()
        except uiautomator2.exceptions.UiObjectNotFoundError:
            self.log.warn(f"Account switcher not found, trying again")
            time.sleep(1)
            current_account = self.select(textMatches=account_names_re)[0].get_text()
        self.log.info(f"Current account is {current_account}")

        if current_account != account.name:
            self.log.info(f"Switching account to {account.username}")
            self.log.info(f"Clicking account switcher")
            self.click(idx=0, textMatches=account_names_re)
            self.click(textMatches=f'{account.username}|{account.name}')
            time.sleep(6)
            self.log.info(f"Switched account to {account.username}")
            self.log.info("Waiting for profile to appear")
            self.select(timeout=self.TIKTOK_START_TIMEOUT, text='Profile')
            time.sleep(2)

    def add_overlay_text(self, text):
        self.log.info(f"Adding overlay text {text}")
        self.click(text='Text')
        time.sleep(2)
        self.log.info(f"Setting text to {text}")
        self.select(focused=True).set_text(text)
        self.click("Text outline", idx=0, index=0, className='android.widget.ImageView', clickable=True)
        self.click(text='Done')
        self.log.info(f"Draging text to top")
        self.d.drag(
            0.5,
            0.4,
            0.5,
            0.2 + random.uniform(-0.03, 0.03),
            0.15 + random.uniform(0, 0.05),
        )

    def open_tiktok(self):
        self.log.info(f"Opening TikTok...")
        self.d.app_stop('com.zhiliaoapp.musically')
        self.d.app_start("com.zhiliaoapp.musically", 'com.ss.android.ugc.aweme.splash.SplashActivity')

        try:
            self.select(timeout=self.TIKTOK_START_TIMEOUT, text='Profile')
            time.sleep(1)
        except Exception as e:
            self.log.info(f"Opening TikTok...")
            self.d.app_stop('com.zhiliaoapp.musically')
            time.sleep(2)
            self.d.app_start("com.zhiliaoapp.musically", 'com.ss.android.ugc.aweme.splash.SplashActivity')
            self.select(timeout=self.TIKTOK_START_TIMEOUT, text='Profile')
            time.sleep(1)

    def upload_video_internal(self, account, video, title, tags, sound_url, sound_name, overlay_text=''):
        self.log.info(f"Starting upload of video {video} to account {account.username}")

        if not self.connected():
            self.connect()

        self.unlock()

        self.transfer_video(video)

        self.open_tiktok()

        self.switch_to_account(account)

        if sound_url:
            self.log.info(f"Opening sound {sound_name} {sound_url}")
            self.d.open_url(sound_url)
            if self.exists(timeout=self.TIKTOK_START_TIMEOUT, text='Use this sound'):
                self.click(timeout=self.TIKTOK_START_TIMEOUT, text='Use this sound')
            else:
                self.log.info(f"Sound url did not open or does not exist, opening again")
                self.d.open_url(sound_url)
                self.click(timeout=self.TIKTOK_START_TIMEOUT, text='Use this sound')

        else:
            self.log.info(f"Clicking + button")
            self.d.click(self.PLUS_X, self.PLUS_Y)
            self.log.info(f"Wait for upload button")
            if not self.exists(timeout=10, text='Upload'):
                self.log.error(f"Upload button not found, clicking + again")
                self.d.click(self.PLUS_X, self.PLUS_Y)

        self.click(text='Upload')
        self.click(text='Videos')
        time.sleep(2)
        self.click(idx=0, textMatches='\d\d:\d\d', resourceIdMatches='com.zhiliaoapp.musically.*')

        if sound_url:
            self.click(message='Sound Name', timeout=120, textMatches=f'{sound_name}.*')
            self.click(text='Volume')
            self.log.info(f"Setting original sound volume to 100%")
            self.select(className='android.widget.SeekBar')[0].click(offset=self.ORIGINAL_SOUND_OFFSET)
            time.sleep(0.5)
            self.log.info(f"Setting added sound volume to 1%")
            self.select(className='android.widget.SeekBar')[1].click(offset=self.ADDED_SOUND_OFFSET)
            time.sleep(0.5)
            self.click(text='Done')

        if overlay_text:
            self.add_overlay_text(overlay_text)

        self.click(timeout=self.TIKTOK_START_TIMEOUT, text='Next')

        title_with_tags = title + ' ' + ' '.join(['#' + t for t in tags])
        self.log.info(f"Setting title to {title_with_tags}")
        self.select(textMatches="(Describe your post|Share your thoughts|Share what).*").set_text(title_with_tags)
        time.sleep(10)
        self.log.info(f"Pressing back")
        self.d.press('back')

        self.click(text='Post', idx=-1)

        self.click_exists(timeout=6, text='Post video')
        self.click_exists(timeout=6, textMatches='Post [nN]ow')

        time.sleep(10)

        try:
            end = time.time() + 300
            while time.time() < end and self.exists(timeout=5, textMatches="\d+%", resourceIdMatches="com.zhiliaoapp.musically.*"):
                percentage = self.select(textMatches='\d+%', resourceIdMatches='com.zhiliaoapp.musically.*').get_text()
                self.log.info(f"Waiting for upload to complete {percentage}")
                time.sleep(5)
            # Wait one minute for potential video open.
            if len(self.d(text='0')) == 3:
                self.log.info(f"Video opened!")
                self.log.info(f"Video upload complete for {account.username}!")
                return
        except Exception as e:
            self.log.error(f"Error waiting for video open: {e}")
        
        time.sleep(60)
        self.log.info(f"Video upload complete for {account.username}!")
        return True

    def upload_video(self, account, video, title, tags, sound_url, sound_name, overlay_text=''):
        try:
            self.log.info(f"Uploading video {video} to account {account.username}")
            return self.upload_video_internal(account, video, title, tags, sound_url, sound_name, overlay_text=overlay_text)
        except adbutils.errors.AdbError as e:
            self.log.error(f"AdbError uploading video {video} to account {account.username}: {e}")
            self.log.exception(f"AdbError uploading video {video} to account {account.username}: {e}")
            raise Exception(f"AdbError: {e}")
        except Exception as e:
            self.log.error(f"Error uploading video {video} to account {account.username}: {e}")
            self.log.exception(f"Error uploading video {video} to account {account.username}: {e}")
            self.log_state()
            raise e
        
    def create_gmail(self, username, password, name):
        self.log.info(f"Starting gmail account creation with {username}")

        if not self.connected():
            self.connect()

        self.unlock()

        self.log.info(f"Opening Gmail...")
        self.d.app_stop('com.google.android.gm')
        self.d.app_start('com.google.android.gm', use_monkey=True)

        if self.exists(timeout=20, resourceIdMatches='com.google.android.gm:id/(selected_account_disc_gmail|identity_disc_menu_item)'):        
            self.click(timeout=self.TIKTOK_START_TIMEOUT, resourceIdMatches='com.google.android.gm:id/(selected_account_disc_gmail|identity_disc_menu_item)')
            if not self.exists(timeout=10, text='Add another account'):
                for i in range(10):
                    self.d.swipe_ext('up')
            self.click(text='Add another account')
            first = False
        else:
            self.log.info(f"No accounts yet, creating first account")
            if self.exists(timeout=20, text='GOT IT'):
                self.click(text='GOT IT')
            self.click(text='Add an email address')
            first = True
        
        self.click(text='Google')
        self.click(text='Create account')
        if not self.exists(timeout=6, text='For myself'):
            self.click(text='Create account')
        self.click(text='For myself')
        self.log.info(f"Setting username to {username}")
        self.select(resourceId='firstName').set_text(name)
        time.sleep(3)
        self.log.info("Pressing back to remove keyboard")
        self.d.press('back')
        time.sleep(2)
        self.click(text='Next')

        random_day = str(random.randint(1, 28))
        self.log.info(f"Setting day to {random_day}")
        self.select(resourceId='day').set_text(random_day)

        self.click(resourceId='month')
        self.click(text=random.choice([
            'January',
            'February',
            'March',
            'April',
            'May',
            'June',
            # 'July',
            # 'August',
            # 'September',
            # 'October',
            # 'November',
            # 'December',
        ]))
        
        random_year = str(random.randint(1990, 2005))
        self.log.info(f"Setting year to {random_year}")
        self.select(resourceId='year').set_text(random_year)
        self.click(resourceId='gender')
        self.click(text=random.choice(['Male', 'Female']))
        self.click(text='Next')

        if self.exists(timeout=10, text='Create your own Gmail address'):
            self.click(text='Create your own Gmail address')

        self.select(className='android.widget.EditText')[0].set_text(username)
        time.sleep(3)
        self.log.info("Pressing back to remove keyboard")
        self.d.press('back')
        time.sleep(2)
        self.click(text='Next')
        time.sleep(2)

        self.select(className='android.widget.EditText')[0].set_text(password)
        time.sleep(3)
        self.log.info("Pressing back to remove keyboard")
        self.d.press('back')
        time.sleep(2)
        self.click(text='Next')

        if not self.exists(timeout=10, text='Skip'):
            self.log.info(f"Not possible to skip phone number exiting...")
            self.log_state()
            self.d.app_stop('com.google.android.gm')
            self.lock()

        self.click(text='Skip')

        self.click(text='Next')

        time.sleep(2)
        if self.exists(timeout=10, text='Next'):
            self.click(text='Next')
            time.sleep(2)

        self.log.info(f"Swiping to the end of the page")
        for i in range(6):
            self.d.swipe_ext('up')
        self.click(text='I agree')

        if first:
            self.click("Backup", checked=True, clickable=True)
            if self.exists(timeout=10, text='More'):
                self.click(text='More')
            self.click(text='Accept')

        time.sleep(20)
        self.lock()
        self.log.info(f"Succesfully created gmail account {username}")

    def scroll_feed(self, minutes, account):
        self.log.info(f"Scrolling feed for {minutes} minutes")

        if not self.connected():
            self.connect()

        self.unlock()

        self.open_tiktok()

        self.switch_to_account(account)

        self.click(text='Home')
        
        end = time.time() + (minutes * 60)
        while time.time() < end:
            time.sleep(random.uniform(1.2, 15))

            if self.exists(timeout=0.1, text='What languages do you understand?'):
                self.click(text='More languages')
                for i in range(20):
                    self.d.swipe_ext('up')
                self.click(text='српски')
                self.click(text='Confirm')

            if self.exists(timeout=0.1, text='How do you feel about the video you just watched?'):
                self.click(text='Cancel')

            # self.recover()
            self.log.info(f"Next video")
            self.d.swipe(
                0.4 + random.uniform(-0.05, 0.05),
                0.6 + random.uniform(-0.05, 0.05),
                0.4 + random.uniform(-0.05, 0.05),
                0.4 + random.uniform(-0.05, 0.05),
                0.03,
            )
        
        self.lock()

    def interact(self):
        if not self.connected():
            self.connect()

        import code
        code.interact(local=dict(globals(), **locals())) 
    
    def push_profile_pictures(self):
        images_dir = 'profile_images'
        self.log.info(f"Transfering random images from {images_dir}")
        for i in range(3):
            random_image = random.choice(os.listdir(images_dir))
            self.transfer_file(os.path.join(images_dir, random_image), delete=False)
        


class LM_K200EMW(AndroidDevice):
    ORIGINAL_SOUND_OFFSET = (0.48, 0.5)
    ADDED_SOUND_OFFSET = (0.049, 0.5)
    PLUS_Y = 0.915
    MODEL = 'LM-K200EMW'

    def transfer_video(self, video_path):
        super().transfer_file(video_path)
        video_name = os.path.basename(video_path)
        
        self.log.info(f"Starting files app...")
        self.d.app_stop('com.google.android.apps.nbu.files')
        self.d.app_start('com.google.android.apps.nbu.files', '.home.HomeActivity')
        self.click(text='Downloads')

        time.sleep(3)

        self.log.info(f"Checking if video exists on device...")
        if not self.exists(timeout=1, text=video_name) and not self.exists(timeout=1, text='‎' + video_name):
            self.log.error(f"Video {video_path} transfered but not found in files.")
            raise Exception(f"Video {video_path} transfered but not found in files.")
        
        self.log.info(f"Video found in files!, done!")

    def setup_apn(self):
        self.d.app_stop('com.android.settings')
        self.d.app_start('com.android.settings')
        self.click(text='Network and Internet')
        self.click(text='Mobile network')
        self.click(text='Advanced')
        self.click(text='Access Point Names')
        self.click(description='New APN')
        self.click(text='Name')
        self.select(focused=True).set_text('globltel')
        self.click(text='OK')
        self.click(text='APN')
        self.select(focused=True).set_text('globltel')
        self.click(text='OK')
        self.click(description='More options')
        self.click(text='Save')
        time.sleep(2)

    def install_tiktok(self):
        self.d.open_url('https://play.google.com/store/apps/details?id=com.zhiliaoapp.musically')
        if self.exists(timeout=10, text='Terms of Service'):
            self.click(text='Accept')
        self.click(description='Install')


    def create_tiktok_account(self, email, username, name, password):
        try:
            if not self.connected():
                self.connect()

            # self.unlock()

            self.log.info(f"Starting TikTok account creation with {email}, {username}, {name}")
            self.push_profile_pictures()
            self.open_tiktok()

            self.click(timeout=self.TIKTOK_START_TIMEOUT, text='Profile')


            # account_names = [account.username for account in self.accounts] + [account.name for account in self.accounts]
            # account_names_re = '|'.join(account_names)
            # self.log.debug(f"Getting account switcher with regex {account_names_re}")
            # try:
            #     current_account = self.select(textMatches=account_names_re)[0].get_text()
            # except uiautomator2.exceptions.UiObjectNotFoundError:
            #     self.log.warn(f"Account switcher not found, trying again")
            #     time.sleep(1)
            #     current_account = self.select(textMatches=account_names_re)[0].get_text()
            # self.log.info(f"Current account is {current_account}")

            # self.click(text='Sign up')
            self.click(text='Use phone or email')
            self.click(text='Email')
            self.select(focused=True).set_text(email)
            time.sleep(3)
            self.d.press('back')
            self.click(text='Next')
            time.sleep(3)
            self.select(focused=True).set_text(password)
            time.sleep(3)
            self.d.press('back')
            self.click(text='Next')
            self.d.swipe(0.2, 0.8, 0.2, 0.5, 0.3)
            self.d.swipe(0.5, 0.8, 0.5, 0.5, 0.3)
            self.d.swipe(0.8, 0.8, 0.8, 0.99, 0.022)
            self.d.swipe(0.8, 0.8, 0.8, 0.99, 0.5)
            self.click(text='Next')
            self.select(focused=True).set_text(name)
            self.click(text='Continue')
            self.click(text='Confirm')
            self.click(text='Skip')

            # confirm email
            self.d.app_stop('com.google.android.gm')
            self.d.app_start('com.google.android.gm', use_monkey=True)

            self.click(timeout=self.TIKTOK_START_TIMEOUT, resourceIdMatches='com.google.android.gm:id/(selected_account_disc_gmail|identity_disc_menu_item)')
            self.click(text=email)
            if self.exists(timeout=10, text='Verify your email address with TikTok'):
                self.click(text='Verify your email address with TikTok')
            else:
                self.d.press('back')
                self.click(text='Verify your email address with TikTok')
            self.click(text='Verify your email address')
            self.click(text='Open TikTok')

            self.log.info(f"Successfully created TikTok account {username}")
            self.log.info(','.join([self.name, username, name, email, password]))
        except Exception as e:
            self.log.exception(f"Error creating TikTok account {username}: {e}")
            import code
            code.interact(local=dict(globals(), **locals()))

class RedmiNote8T(AndroidDevice):
    ORIGINAL_SOUND_OFFSET = (0.482, 0.5)
    ADDED_SOUND_OFFSET = (0.044, 0.5)
    PLUS_Y = 0.915
    MODEL = 'RedmiNote8T'

    def transfer_video(self, video_path):
        super().transfer_file(video_path)
        video_name = os.path.basename(video_path)
        
        self.log.info(f"Starting files app...")
        self.d.app_stop('com.miui.videoplayer')
        self.d.app_start('com.miui.videoplayer')
        self.click(text='Local')

        time.sleep(3)
        self.log.info("Swiping down")
        self.d.swipe_ext('down')

        if not self.exists(timeout=10, text=video_name):
            self.log.error(f"Video {video_path} transfered but not found in files.")
            raise Exception(f"Video {video_path} transfered but not found in files.")
        
        self.log.info(f"Video found in files!, done!")


class SM_J730F(AndroidDevice):
    ORIGINAL_SOUND_OFFSET = (0.482, 0.5)
    ADDED_SOUND_OFFSET = (0.041, 0.5)
    PLUS_Y = 0.95
    MODEL = 'SM-J730F'

    def transfer_video(self, video_path):
        super().transfer_file(video_path)
        video_name = os.path.basename(video_path)
        
        self.log.info(f"Starting files app...")
        self.d.app_stop('com.sec.android.app.myfiles')
        self.d.app_start('com.sec.android.app.myfiles')
        self.click(text='Videos')
        self.click(text='Download')

        if not self.exists(timeout=10, text=video_name) and not self.exists(timeout=10, text='‎' + video_name):
            self.log.error(f"Video {video_path} transfered but not found in files.")
            raise Exception(f"Video {video_path} transfered but not found in files.")

        self.log.info(f"Video found in files!, done!")

class SM_J710FN(AndroidDevice):
    ORIGINAL_SOUND_OFFSET = (0.482, 0.5)
    ADDED_SOUND_OFFSET = (0.049, 0.5)
    PLUS_Y = 0.95
    MODEL = 'SM-J710FN'

    def transfer_video(self, video_path):
        super().transfer_file(video_path)
        video_name = os.path.basename(video_path)
        
        self.log.info(f"Starting files app...")
        self.d.app_stop('com.sec.android.app.myfiles')
        self.d.app_start('com.sec.android.app.myfiles')
        self.click(text='Videos')
        self.click(text='Download')

        if not self.exists(timeout=10, text='‎' + video_name) and not self.exists(timeout=30, text=video_name):
            self.log.error(f"Video {video_path} transfered but not found in files.")
            raise Exception(f"Video {video_path} transfered but not found in files.")

        self.log.info(f"Video found in files!, done!")


class SM_J730G_DS(AndroidDevice):
    ORIGINAL_SOUND_OFFSET = (0.482, 0.5)
    ADDED_SOUND_OFFSET = (0.041, 0.5)
    PLUS_Y = 0.95
    MODEL = 'SM-J730G/DS'

    def transfer_video(self, video_path):
        super().transfer_file(video_path)
        video_name = os.path.basename(video_path)
        
        self.log.info(f"Starting files app...")
        self.d.app_stop('com.sec.android.app.myfiles')
        self.d.app_start('com.sec.android.app.myfiles')
        self.click(text='Videos')
        self.click(text='Download')

        if not self.exists(timeout=10, text=video_name) and not self.exists(timeout=10, text='‎' + video_name):
            self.log.error(f"Video {video_path} transfered but not found in files.")
            raise Exception(f"Video {video_path} transfered but not found in files.")

        self.log.info(f"Video found in files!, done!")


class SM_J700H(AndroidDevice):
    ORIGINAL_SOUND_OFFSET = (0.482, 0.5)
    ADDED_SOUND_OFFSET = (0.049, 0.5)
    PLUS_Y = 0.95
    MODEL = 'SM-J700H'

    def transfer_video(self, video_path):
        super().transfer_file(video_path)
        video_name = os.path.basename(video_path)
        
        self.log.info(f"Starting files app...")
        self.d.app_stop('com.sec.android.app.myfiles')
        self.d.app_start('com.sec.android.app.myfiles')
        self.click(text='Videos')

        if not self.exists(timeout=20, text=video_name):
            self.log.error(f"Video {video_path} transfered but not found in files.")
            raise Exception(f"Video {video_path} transfered but not found in files.")

        self.log.info(f"Video found in files!, done!")

MODELS = {
    'LM-K200EMW': LM_K200EMW,
    'RedmiNote8T': RedmiNote8T,
    'SM-J730F': SM_J730F,
    'SM-J710FN': SM_J710FN,
    'SM-J730G/DS': SM_J730G_DS,
    'SM-J700H': SM_J700H,
}

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--device", help="Name of the device to connect to", required=True)

    with open('devices.yaml', 'r') as file:
        devices = yaml.safe_load(file)

    args = parser.parse_args()
    device = devices[args.device]

    android_device = MODELS[device['model']](
        device['name'],
        device['device_id'],
        utils.read_accounts_for_device(device['name']).itertuples(index=False),
    )

    android_device.interact()

if __name__ == '__main__':
    main()
