import yaml
import string
import random

from uploader import android
from uploader import utils

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--device", help="Device Name", required=True)

    args = parser.parse_args()

    with open('devices.yaml', 'r') as file:
        devices = yaml.safe_load(file)

    device = devices[args.device]
    android_device = android.MODELS[device['model']](
        device['name'],
        device['device_id'],
        utils.read_accounts_for_device(device['name']).itertuples(index=False),
    )

    android_device.connect()
    android_device.push_profile_pictures()

if __name__ == '__main__':
    main()
