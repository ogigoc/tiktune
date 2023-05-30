import re

import pandas as pd
ACCOUNTS_DB = 'accounts_db.json'

def is_ip_address(s):
    return re.fullmatch(r'(\d{1,3}\.){3}\d{1,3}', s) is not None

def params_to_string(params):
    string_values = [
        v[0].upper() + v[1:] if v in {'true', 'false'} else int(v) if v.isnumeric() else f'"{v}"'
        for v in [str(val) for val in params.values()]
    ]
    return f'({", ".join(str(k) + "=" + str(v) for k,v in zip(params.keys(), string_values))})'

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

def read_accounts_for_device(device):
    accounts = pd.read_json(ACCOUNTS_DB, lines=True)
    return accounts[accounts.device == device]
