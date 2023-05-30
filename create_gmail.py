import yaml
import string
import random
import logging

from uploader import android2 as android
from uploader import utils
import password_creator

# log to file and stdout
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh = logging.FileHandler('create_gmail.log')
fh.setLevel(logging.INFO)
fh.setFormatter(formatter)
log.addHandler(fh)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(formatter)
log.addHandler(ch)

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--device", help="Device Name", required=True)

    args = parser.parse_args()

    # read list of names

    name = random.choice([
        line.strip()
        for line in open('imena.txt', 'r').readlines()
    ])
    username = name.lower() + ''.join(random.choice(string.ascii_lowercase) for i in range(4))
    password = password_creator.create(username)

    log.info(f"Creating gmail {args.device} {name} {username}")

    with open('devices.yaml', 'r') as file:
        devices = yaml.safe_load(file)
    device = devices[args.device]
    android_device = android.MODELS[device['model']](
        device['name'],
        device['device_id'],
        utils.read_accounts_for_device(device['name']).itertuples(index=False),
    )

    try:
        android_device.create_gmail(username, password, name)
        log.info(f"Successfully created gmail {args.device} {name} {username}@gmail.com")
    except Exception as e:
        log.exception(f"Error {args.device} {name} {username}: {str(e)}")
    
if __name__ == '__main__':
    main()
