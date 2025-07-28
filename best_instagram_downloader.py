from functions import *
from riad_azz import get_instagram_media_links
from pymongo import MongoClient
import os
from dotenv import load_dotenv
import requests
import telebot
from datetime import datetime, timedelta

# === ENV and Bot Setup ===
load_dotenv()  # Load .env variables
BOT_TOKEN = os.getenv("BEST_INSTAGRAM_DOWNLOADER_BOT_API")
bot = telebot.TeleBot(BOT_TOKEN)

# === MongoDB Setup ===
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["quickgram"]
download_counts = db["download_counts"]
premium_users = db["premium_users"]

ADMIN_USER_ID = 6382917923  # <-- Replace this with your actual Telegram user ID!
DOWNLOAD_LIMIT = 20

# === Premium: Check if user is currently premium ===
def is_premium(user_id):
    user = premium_users.find_one({"user_id": user_id})
    if user and "premium_expiry" in user:
        expiry = user["premium_expiry"]
        # Ensure expiry is a datetime (Mongo may store as string; parse if needed)
        if isinstance(expiry, str):
            expiry = datetime.fromisoformat(expiry)
        return expiry > datetime.utcnow()
    return False

# === Generate Stars Invoice Link ===
def get_stars_invoice_link():
    API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/createInvoiceLink"
    payload = {
        "title": "Unlimited Premium",
        "description": "Unlimited downloads for 1 month.",
        "payload": "premium-monthly",
        "provider_token": "STARS",
        "currency": "USD",
        "prices": [{"label": "Monthly Unlimited", "amount": 79900}],
    }
    response = requests.post(API_URL, json=payload)
    data = response.json()
    if data.get("ok"):
        return data["result"]  # This is the invoice link
    else:
        print("Failed to create invoice:", data)
        return None

# === /start Command ===
@bot.message_handler(commands=['start'])
def start_command_handler(message):
    bot.send_message(message.chat.id, start_msg, parse_mode="Markdown", disable_web_page_preview=True)
    log(f"{bot_username} log:\n\nuser: {message.chat.id}\n\nstart command")

# === /help Command ===
@bot.message_handler(commands=['help'])
def help_command_handler(message):
    bot.send_message(message.chat.id, help_msg, parse_mode="Markdown", disable_web_page_preview=True)
    log(f"{bot_username} log:\n\nuser: {message.chat.id}\n\nhelp command")

# === /getid Command ===
@bot.message_handler(commands=['getid'])
def get_id_handler(message):
    bot.send_message(
        message.chat.id,
        f"Your Telegram user ID is: <code>{message.from_user.id}</code>",
        parse_mode="HTML"
    )

# === /privacy Command ===
@bot.message_handler(commands=['privacy'])
def privacy_message_handler(message):
    bot.send_message(message.chat.id, privacy_msg, parse_mode="Markdown", disable_web_page_preview=True)
    log(f"{bot_username} log:\n\nuser: {message.chat.id}\n\nprivacy command")

# === /premium Command: Send Stars Payment Button ===
@bot.message_handler(commands=['premium'])
def premium_command(message):
    invoice_link = get_stars_invoice_link()
    if not invoice_link:
        bot.send_message(message.chat.id, "⚠️ Sorry, something went wrong creating the payment link.")
        return
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton(
            text="Buy Premium (Stars)", url=invoice_link
        )
    )
    bot.send_message(
        message.chat.id,
        "🌟 Unlock unlimited downloads for just $7.99/month!\n\n"
        "Tap the button below to pay securely with Telegram Stars. You'll be upgraded instantly after payment!",
        reply_markup=markup
    )

# === Handle Spotify links (not supported) ===
@bot.message_handler(regexp=spotify_link_reg)
def spotify_link_handler(message):
    bot.send_message(
        message.chat.id,
        "This bot only supports Instagram links. Please send an Instagram post or reel link.\n\nIf you want to download from Spotify you can check out my other bot: @SpotSeekBot"
    )

# === Main Handler: Instagram Download with Premium & Limit Logic ===
@bot.message_handler(regexp=insta_post_or_reel_reg)
def post_or_reel_link_handler(message):
    user_id = message.from_user.id

    # === Premium/Limit Logic ===
    if user_id == ADMIN_USER_ID or is_premium(user_id):
        # Admin or valid premium users have no limits!
        pass
    else:
        # Standard users: enforce download limit
        user = download_counts.find_one({"user_id": user_id})
        count = user["download_count"] if user else 0

        if count >= DOWNLOAD_LIMIT:
            bot.send_message(
                message.chat.id,
                f"You've reached the free download limit of {DOWNLOAD_LIMIT}! 🚫\n\nTo continue, please use /premium to upgrade."
            )
            return
        else:
            download_counts.update_one(
                {"user_id": user_id},
                {"$inc": {"download_count": 1}},
                upsert=True
            )

    # === Usual Instagram Download Logic (unchanged) ===
    try:
        log(f"{bot_username} log:\n\nuser:\n{message.chat.id}\n\n✅ message text:\n{message.text}")
        guide_msg_1 = bot.send_message(message.chat.id, "Ok wait a few moments...")
        post_shortcode = get_post_or_reel_shortcode_from_link(message.text)
        print(post_shortcode)

        if not post_shortcode:
            log(f"{bot_username} log:\n\nuser: {message.chat.id}\n\n🛑 error in getting post_shortcode")
            return  # post shortcode not found

        media_links, caption = get_instagram_media_links(post_shortcode)

        # todo: fix later if possible and don't let it to happen in the first place
        # if they are both empty and the riad_azz returned this error:
        # "Error extracting media info: 'NoneType' object has no attribute 'get'"
        if (not media_links) and (not caption):
            raise Exception("riad_azz returned nothing")

        # caption handling
        if caption is None:
            caption = ''
        while len(caption) + len(caption_trail) > 1024:
            caption = caption[:-1]
        caption = caption + caption_trail

        media_list = []
        for idx, item in enumerate(media_links):
            if item['type'] == 'video':
                if idx == 0:
                    media = telebot.types.InputMediaVideo(item['url'], caption=caption)
                else:
                    media = telebot.types.InputMediaVideo(item['url'])
            else:
                if idx == 0:
                    media = telebot.types.InputMediaPhoto(item['url'], caption=caption)
                else:
                    media = telebot.types.InputMediaPhoto(item['url'])
            media_list.append(media)

        def chunk_list(lst, n):
            for i in range(0, len(lst), n):
                yield lst[i:i + n]

        if len(media_list) == 1:
            media = media_list[0]
            if isinstance(media, telebot.types.InputMediaPhoto):
                bot.send_photo(message.chat.id, media.media, caption=media.caption)
            else:
                bot.send_video(message.chat.id, media.media, caption=media.caption)
        else:
            for chunk in chunk_list(media_list, 10):
                print(chunk)
                bot.send_media_group(message.chat.id, chunk)
        bot.send_message(message.chat.id, end_msg, parse_mode="Markdown", disable_web_page_preview=True)
        try_to_delete_message(message.chat.id, guide_msg_1.message_id)
        return
    except Exception as e:
        try:
            try_to_delete_message(message.chat.id, guide_msg_1.message_id)
        except:
            pass
        log(f"{bot_username} log:\n\nuser: {message.chat.id}\n\n🛑 error in main body: {str(e)}")
        bot.send_message(message.chat.id, fail_msg, parse_mode="Markdown", disable_web_page_preview=True)
        # import traceback
        # traceback.print_exc() # print error traceback

# === Handle Successful Payment ===
@bot.message_handler(content_types=['successful_payment'])
def handle_successful_payment(message):
    user_id = message.from_user.id
    # Set premium expiry to 30 days from now (UTC)
    expiry = datetime.utcnow() + timedelta(days=30)
    # Store expiry as ISO string for Mongo compatibility
    premium_users.update_one(
        {"user_id": user_id},
        {"$set": {"user_id": user_id, "premium_expiry": expiry.isoformat()}},
        upsert=True
    )
    bot.send_message(
        message.chat.id,
        "🎉 Thank you for your purchase! You are now a premium user for 1 month. Unlimited downloads are unlocked."
    )

# === Fallback for Wrong Pattern ===
@bot.message_handler(func=lambda message: True)
def wrong_pattern_handler(message):
    log(f"{bot_username} log:\n\nuser: {message.chat.id}\n\n❌wrong pattern: {message.text}")
    bot.send_message(message.chat.id, wrong_pattern_msg, parse_mode="Markdown", disable_web_page_preview=True)

bot.infinity_polling()