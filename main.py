# ---------- INSTALLATION REQUIREMENTS ---------- #
'''
    pip install python-dotenv
    pip install python-telegram-bot
'''
# ---------- INSTALLATION REQUIREMENTS ---------- #

# ---------- SECURE APIs AND IDs ---------- #
from typing import Final
from dotenv import load_dotenv
import os

load_dotenv()

# Load the hidden environment variables
TOKEN: Final = os.getenv("BOT_TOKEN")
BOT_USERNAME: Final = os.getenv("BOT_USERNAME")
SHEET_ID: Final = os.getenv("SHEET_ID")

# ---------- SECURE API TOKEN ---------- #

# ---------- IMPORT TELEGRAM API ---------- #

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

import re

from telegram import Bot

# ---------- IMPORT TELEGRAM API ---------- #

# ---------- DATABASE SETUP ---------- #

import sqlite3

class Database:
    
    # creates and connects the local database
    def __init__(self):
        self.connection = sqlite3.connect('username_data.db')
        self.cursor = self.connection.cursor()

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS tag (
            tag_name TEXT,
            username TEXT,
            user_id TEXT
        )
        """)

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS ids (
            user_id TEXT PRIMARY KEY,
            username TEXT
        )
        """)
        self.connection.commit()

    # store user id
    def store_user_id(self, user_id, username):
        self.connection = sqlite3.connect('username_data.db')
        self.cursor = self.connection.cursor()
        self.cursor.execute("""
        DELETE FROM ids
        WHERE username = '{}'
        """.format(username))
        self.connection.commit()

        self.cursor.execute("""
        INSERT INTO ids VALUES
        ('{}', '{}')
        """.format(user_id, '@' + username))
        self.connection.commit()

    # get user id given username
    # IMPORTANT! get_user_id returns a list, so you may want to use index[0]
    def get_user_id(self, username):
        self.connection = sqlite3.connect('username_data.db')
        self.cursor = self.connection.cursor()
        self.cursor.execute("""
        SELECT user_id
        FROM ids
        WHERE username = '{}'
        """.format(username))
        temp = self.cursor.fetchone()
        return temp

    # returns connected ids in a tag
    def get_tag_ids(self, tag_name):
        self.connection = sqlite3.connect('username_data.db')
        self.cursor = self.connection.cursor()
        self.cursor.execute("""
        SELECT user_id
        FROM tag
        WHERE tag_name = '{}'
        """.format(tag_name))
        tag_ids = [row[0] for row in self.cursor.fetchall()]
        return tag_ids

    # modifies the tags with usernames but stores their id
    # IMPORTANT! user must /start the bot first because it needs their id
    def setup_tag(self, tag_name, usernames):
        self.connection = sqlite3.connect('username_data.db')
        self.cursor = self.connection.cursor()
        self.cursor.execute("""
        DELETE FROM tag
        WHERE tag_name = '{}'
        """.format(tag_name))
        self.connection.commit()

        for username in usernames:
            temp = self.get_user_id(username)
            user_id = temp[0]
            self.cursor.execute("""
            INSERT OR IGNORE INTO tag VALUES
            ('{}', '{}', '{}')
            """.format(tag_name, username, user_id))
        self.connection.commit()

    # returns the usernames connected in a tag
    def get_tag_usernames(self, tag_name):
        self.connection = sqlite3.connect('username_data.db')
        self.cursor = self.connection.cursor()
        self.cursor.execute("""
        SELECT username 
        FROM tag
        WHERE tag_name = '{}'
        """.format(tag_name))
        tag_usernames = [row[0] for row in self.cursor.fetchall()]
        return tag_usernames

    # returns the database of tags in the chat
    def view_tags(self):
        self.connection = sqlite3.connect('username_data.db')
        self.cursor = self.connection.cursor()
        self.cursor.execute("""
        SELECT DISTINCT tag_name
        FROM tag
        """)
        tags = [row[0] for row in self.cursor.fetchall()]
        return tags

    # closes the connection to the database
    def close_connection(self):
        self.connection.close()
         
# ---------- DATABASE SETUP ---------- #

# ---------- BOT CODE ---------- #

# ---------- CODE OF COMMANDS ---------- #

# starts the bot with a welcoming message
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user
    user_id = user.id
    username = user.username

    # Store the user ID and username in the database
    db.store_user_id(user_id, username)
    db.close_connection()

    await update.message.reply_text(f"Welcome, {user.username}! Glee says hi")

# modifies the tag with usernames
async def setup_tag_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text
    processed_text: str = text

    if ('@' in processed_text):
        tags = extract_words_with_at_symbol(text)

    tag_name = tags[0]
    usernames = tags[1:]

    db.setup_tag(tag_name, usernames)
    db.close_connection()

    await update.message.reply_text("tags updated")

# shows the current tags in the chat
async def view_tags_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    tags = db.view_tags()
    db.close_connection()

    tags_text = ' '.join(tags)
    await update.message.reply_text(tags_text)

# shows the usernames connected in a tag
async def view_tag_usernames(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text: str = update.message.text
    processed_text: str = text
    tag_usernames = []

    if ('@' in processed_text):
        tags = extract_words_with_at_symbol(text)

    for tag in tags:
        tag_usernames.extend(db.get_tag_usernames(tag))
    db.close_connection()

    tag_usernames_processed = ' '.join(tag_usernames)
    await update.message.reply_text(tag_usernames_processed)

# shows database to users
async def view_database_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    # Connect to the database
    connection = sqlite3.connect('username_data.db')
    cursor = connection.cursor()

    # Fetch the table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    # Iterate over the tables
    for table in tables:
        table_name = table[0]
        print(f"Table: {table_name}")

        # Fetch the rows from the table
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()

        # Print the rows
        for row in rows:
            print(row)

        print()  # Add an empty line between tables

    # Close the connection
    connection.close()

    await update.message.reply_text("""
    Database printed successfully. Note that only devs have access to the console.
    """)

# ---------- CODE OF COMMANDS ---------- #

# ---------- MESSAGE HANDLER ---------- #

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    #check whether user is in group chat or private chat
    message_type: str = update.message.chat.type
    text: str = update.message.text

    print(f'User ({update.message.chat.id}) in {message_type}: "text"')

    #NOTE: if commented, bot does not have to be mentioned to work in a group
    '''
    if (message_type == 'group'):
        if BOT_USERNAME in text:
            new_text: str = text.replace(BOT_USERNAME, '').strip()
            response: str = handle_response(new_text)
        else:
            return
    else:
    '''
    if ("@" in text):
        user_ids = []
        tags = extract_words_with_at_symbol(text)

        for tag in tags:
            user_ids.extend(db.get_tag_ids(tag))
        db.close_connection()

        # Generate mention tags for each user ID
        mention_tags = [f'<a href="tg://user?id={user_id}">.</a>' for user_id in user_ids]
        mention_message = ''.join(mention_tags)
        await update.effective_chat.send_message(
            text = mention_message,
            parse_mode = ParseMode.HTML
        )
        

# ---------- MESSAGE HANDLER ---------- #

# ---------- DEBUGGER ---------- #
async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Update {update} caused error {context.error}')

# ---------- DEBUGGER ---------- #

# ---------- ASSISTING FUNCTIONS IN CODE OF COMMANDS ---------- #

# Function to create the db instance if it doesn't exist
def create_db_instance():
    global db
    if db is None:
        db = Database()

# returns a list of words with an @ symbol
def extract_words_with_at_symbol(text):
    pattern = r'@\w+'
    words = re.findall(pattern, text)

    return words

# ---------- ASSISTING FUNCTIONS IN CODE OF COMMANDS ---------- #

if __name__ == '__main__':
    app = Application.builder().token(TOKEN).build()

    # CREATES THE DATABASE
    db = None
    create_db_instance()

    # COMMANDS
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('setuptag', setup_tag_command))
    app.add_handler(CommandHandler('viewtags', view_tags_command))
    app.add_handler(CommandHandler('viewtagusernames', view_tag_usernames))
    app.add_handler(CommandHandler('viewdatabase', view_database_command))

    #Messages
    app.add_handler(MessageHandler(filters.TEXT, handle_message))
    
    # ERRORS
    app.add_error_handler(error)

    # POLLS THE BOT
    print("Polling...")
    app.run_polling(poll_interval=3)

# ---------- BOT CODE ---------- #



