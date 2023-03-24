import requests

TELEGRAM_BOT_URL = 'https://api.telegram.org/bot6040627117:AAEFVO_1WkBFBIF9cwAjroI1wYmvubyRncQ/sendMessage'

def send_message(message):
    r = requests.post(
        url=TELEGRAM_BOT_URL,
        data={'chat_id': 5080692312, 'text': message}
    )

if __name__ == '__main__':
    send_message('Test message')
