#!/bin/bash
[ -z "$1" ] && { echo "Usage: $0 <tiktok_username>"; exit 1; }

google-chrome-stable --user-data-dir=profiles --profile-directory=$1 https://www.tiktok.com/@$1
# google-chrome-stable --user-data-dir=profiles --profile-directory=$1 https://www.tiktok.com/login/phone-or-email/email?redirect_url=https%3A%2F%2Fwww.tiktok.com%2F%40$1
