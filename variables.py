import os
from dotenv import load_dotenv

import instaloader
from instaloader import *

import re
import requests
import traceback # to print error traceback
import telebot

import json
import urllib.parse

# we use dotenv to use os.getenv() instead of os.environ[]
# and read from '.env' in current folder instead of '/etc/environment'
# more guide:
# https://dev.to/jakewitcher/using-env-files-for-environment-variables-in-python-applications-55a1
load_dotenv()

# env variables
bot_token = os.getenv('BEST_INSTAGRAM_DOWNLOADER_BOT_API')
log_channel_id = os.getenv('INSTAGRAM_DOWNLOADER_LOG_CHANNEL_ID') # set to False if not needed

# initialize bot
bot = telebot.TeleBot(bot_token)

# settings
bot_username = "@igramdloadbot"
caption_trail = "\n\n\n" + bot_username
session_file_name = "session" # any name change should apply to .gitignore too

# warp socks proxy
warp_proxies = os.environ["WARP_PROXIES"]
warp_proxies = json.loads(warp_proxies)

# regex
insta_post_or_reel_reg = r"(?:https?://)?(?:www\.)?instagram\.com/(p|reel)/([a-zA-Z0-9_-]{5,20})(?:/)?(?:\?[^ ]*)?"
spotify_link_reg = r'(?:https?://)?open\.spotify\.com/(track|album|playlist|artist)/[a-zA-Z0-9]+'

# messages
start_msg = '''Hi😃👋
Send an instagram link to download.

It can be a post link like this:
https://www.instagram.com/p/DFx\_jLuACs3

Or it can be a reel link like this:
https://www.instagram.com/reel/C59DWpvOpgF'''

help_msg = '''How can I help?
Here are the commands you can use:

/start — Get started or see a welcome message.

/help — View this help message anytime.

/getid — See your unique user ID.

/privacy — Read the privacy policy.

If you have questions, feedback, or run into any issues, just send a message or use one of the commands above. Im here to help!'''

privacy_msg = '''This bot only stores the minimum information needed to make your experience awesome. Your data is never shared, sold, or used for advertising. We dont read your private messages or access your files.

If you have questions or concerns about your privacy, just ask or contact the creator directly!'''

end_msg = '''If you like the bot you can support me by giving a star [here](https://github.com/asteriasmoons/best-instagram-downloader) ⭐

We are currently working on implementing the premium plans. The download limit per day is 20. Have a wonderful day and enjoy your art!'''

fail_msg = '''Sorry, my process wasn't successful.
But you can try again another time or with another link.'''

wrong_pattern_msg = '''wrong pattern.
You should send an instagram post or reel link.'''

reel_msg = '''reel links are not supported at the moment.
You can send post links instead.'''
