import os
import pathlib
import logging
from telegram.ext import Updater
from telegram.ext import Filters
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler

# This is the Telegram Bot that prints all input documents. It can print pdf and txt files.
# Before sending files for printing user must enter the password by command "/auth <password>".
# This implementation uses "lp -d <printer> <file>" to print files (see function "print_file").
# To adopt this for Windows - extend print_file function with something like https://stackoverflow.com/questions/4498099/silent-printing-of-a-pdf-in-python

# TODO: Set here printer name (Choose one from output of command 'lpstat -p'):
printer_name = "PRINTER_NAME"
# TODO: Set here your bot's token key (from Telegram BotFather)
token_key = ""
password = ""
file_size_limit = 64*1024*1024  # 64Mb

# Directory where files for printing should be saved
files_dir = "printed_files"
pathlib.Path(files_dir).mkdir(parents=True, exist_ok=True)

def print_file(file_path):
    os.system('lp -d {} {}'.format(printer_name, file_path))

# Configuring logging
log_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger()
logger.setLevel(logging.INFO)

file_handler = logging.FileHandler("printerbot.log")
file_handler.setFormatter(log_formatter)
logger.addHandler(file_handler)

console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
logger.addHandler(console_handler)


def start(bot, update):
    logger.info("User {} started...".format(update.message.from_user.username))
    bot.send_message(chat_id=update.message.chat_id, text="I'm a printer bot for Math circle! "
                                                          "Unicorns prance in the clearing. "
                                                          "You need to authorize by \"/auth <password>\" to print files.")

authorized_chats = set()


def auth_passed(update):
    return update.message.chat_id in authorized_chats


def authorize(bot, update, args):
    args = ''.join(args)

    if auth_passed(update):
        logger.info("User {} tried to authorize multiple times.".format(update.message.from_user.username))
        bot.send_message(chat_id=update.message.chat_id, text="You already authorized!")
        return

    if password == args:
        authorized_chats.add(update.message.chat_id)
        logger.info("User {} authorized.".format(update.message.from_user.username))
        bot.send_message(chat_id=update.message.chat_id, text="Now you can print files via sending.")
    else:
        logger.info("User {} entered wrong password: {}.".format(update.message.from_user.username, args))
        bot.send_message(chat_id=update.message.chat_id, text="Wrong password!")


def print_file(bot, update):
    if not auth_passed(update):
        bot.send_message(chat_id=update.message.chat_id, text="Please, pass authorization by \"/auth <password>\".")
        return

    file_id = update.message.document.file_id
    file_name = update.message.document.file_name
    file_size = update.message.document.file_size

    if file_size > file_size_limit:
        bot.send_message(chat_id=update.message.chat_id, text="File is too big ({} > {})!".format(file_size, file_size_limit))
        return

    bot.send_message(chat_id=update.message.chat_id, text="Downloading file...")

    file_path = files_dir + '/' + file_name

    logger.info("Downloading file {} from {}...".format(file_name, update.message.from_user.username))
    new_file = bot.get_file(file_id)
    new_file.download(file_path)
    logger.info("Downloaded  file {} from {}!".format(file_name, update.message.from_user.username))

    logger.info("Printing file {}...".format(file_path))
    print_file(file_path)

    logger.info("File {} sent for printing on {}!".format(file_path, printer_name))
    bot.send_message(chat_id=update.message.chat_id, text="File printed!")


updater = Updater(token=token_key)
dispatcher = updater.dispatcher

dispatcher.add_handler(CommandHandler('start', start))
dispatcher.add_handler(CommandHandler('auth', authorize, pass_args=True))
dispatcher.add_handler(MessageHandler(Filters.document, print_file))

logger.info("Listening...")
updater.start_polling()
