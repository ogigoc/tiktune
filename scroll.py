"""Scroll the tiktok feed on a given device for a given number of minutes"""
import logging
import random
import yaml
import time

import pandas as pd

import telegram
from uploader import android
from uploader import utils

log = logging.getLogger(__name__)

ACCOUNTS_DB = 'accounts_db.json'


def scroll_feed(android_device, minutes, account, silent=False):
        log.info(f"Scrolling feed for account {account.username} for {minutes} minutes")
        try:
            android_device.scroll_feed(minutes, account)
        except Exception as e:
            error_message = f"Error while scrolling feed, but continuing: {str(e)}"
            log.error(error_message)
            log.exception(error_message)
            
            try:
                log.info("Trying to lock device...")
                android_device.connect()
                android_device.log_state()
                android_device.lock()
            except Exception as e:
                error_message = f"Error while locking device: {str(e)}"
                log.error(error_message)
                log.exception(error_message)

            if not silent:
                telegram.send_message('SCROLL ERROR ' + android_device.name + ' ' + error_message)
            raise e

def main():
    try:
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument("-d", "--device", help="Device Name", required=True)
        parser.add_argument("-m", "--minutes", help="Number of minutes to scroll", required=True, type=int)
        parser.add_argument("-a", "--account", help="Account username to use", required=True)
        parser.add_argument("-s", "--silent", action=argparse.BooleanOptionalAction, help="Do not send telegram messages", default=True)
        
        args = parser.parse_args()

        # Send message at start.
        if not args.silent:
            telegram.send_message(f"SCROLL STARTED {args.device}")

        log.info("\n")
        log.info('Starting scroll job...')
        # Load data
        log.info("Reading devices...")
        with open('devices.yaml', 'r') as file:
            devices = yaml.safe_load(file)
        log.info('Reading accounts...')
        accounts = pd.read_json(ACCOUNTS_DB, lines=True)

        if args.device not in devices:
            raise Exception(f"Unknown device {args.device}")

        device = devices[args.device]

        android_device = android.MODELS[device['model']](
            device['name'],
            device['device_id'],
            utils.read_accounts_for_device(device['name']).itertuples(index=False),
        )
        active_accounts = accounts[accounts.device == args.device]

        if args.account == 'all':
            for account in active_accounts.sample(frac=1).itertuples(index=False):
                minutes = args.minutes + random.uniform(-args.minutes * 0.2, args.minutes * 0.2)
                try:
                    scroll_feed(android_device, minutes, account, silent=args.silent)
                except Exception as e:
                    log.error(f"Error while scrolling feed for account {account.username}: {str(e)}")
                    log.warning(f"Trying next account...")
                log.info(f"Finished scrolling feed for account {account.username} for {minutes} minutes")
                log.info(f"Waiting 5-10 minutes")
                time.sleep((5 + random.randint(1, 6)) * 60)
        else:
            account = list(accounts[(accounts.device == args.device) & (accounts.username == args.account)].itertuples(index=False))[0]
            if not account:
                error_message = f"Account {args.account} not found for device {args.device}"
                log.error(error_message)
                if not args.silent:
                    telegram.send_message('SCROLL ERROR ' + android_device.name + ' ' + error_message)
                raise Exception(error_message)

            scroll_feed(android_device, args.minutes, account, silent=args.silent)
        

        if not args.silent:
            telegram.send_message(f"SCROLL SUCCESS {args.device}")
    except Exception as e:
        if not args.silent:
            telegram.send_message(f"SCROLL ERROR {android_device.name} {str(e)}")
        raise e


if __name__ == '__main__':
    main()
