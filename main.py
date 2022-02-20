from Credentials.credentials import Admin
from DB.my_db import DB
from telegram.ext import Updater, MessageHandler, Filters, CommandHandler
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_watson import LanguageTranslatorV3
import time
import telegram
import logging

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


class Bot:
    def __init__(self):
        self._token = Admin().credentials()["telegram"]["telegram_bot_token"]
        self.ibm_api_key = Admin().credentials()["ibm_keys"]["ibm_api_key"]
        self.url = Admin().credentials()["ibm_keys"]["url"]
        self.first_lang = Admin().credentials()["language_translation"]["first_lang"]
        self.second_lang = Admin().credentials()["language_translation"]["second_lang"]
        self.first_lang_code = Admin().credentials()["language_translation"]["first_lang_code"]
        self.second_lang_code = Admin().credentials()["language_translation"]["second_lang_code"]
        self.first_group = Admin().credentials()["group_ids"]["first"]
        self.second_group = Admin().credentials()["group_ids"]["second"]
        self.ignore_words = Admin().credentials()["telegram"]["ignored_words"]
        self.lt = LanguageTranslatorV3(version='2018-05-01', authenticator=IAMAuthenticator(self.ibm_api_key))
        self.lt.set_service_url(self.url)

    def translation_(self, _lang, text):
        try:
            if _lang == 0:
                trans = self.lt.translate(text=[text], model_id=self.first_lang_code).get_result()
                return trans['translations'][0]['translation']

            elif _lang == 1:
                trans = self.lt.translate(text=[text], model_id=self.second_lang_code).get_result()
                return trans['translations'][0]['translation']

        except Exception as e:
            print(e)

    def start(self, update, context):
        user = update.message.from_user.first_name
        context.bot.send_message(update.message.from_user.id,
                                 text=f"*Hi {user}*, I am a translation bot, I can translate cross "
                                      f"groups post from `{self.first_lang} to {self.second_lang}` or"
                                      f" `vice-versa`", parse_mode="Markdown")

        try:
            # Retrieving selected groups names from given chat_id's of both groups
            first_grop_name = context.bot.get_chat(chat_id=self.first_group)['title']
            second_grop_name = context.bot.get_chat(chat_id=self.second_group)['title']

            # Formatted names of both groups, if both names are not clickable then invalid chat_id's provided or bot is
            # not added as admin in both groups.
            formatted_first_group_name = context.bot.get_chat(chat_id=self.first_group)["invite_link"]
            formatted_second_group_name = context.bot.get_chat(chat_id=self.second_group)["invite_link"]

            dev = "[developer](tg://user?id=1114526265)"
            github = "[Github](https://github.com/abhisheksurela79)"
            # self-promotion ☜(⌒▽⌒)☞ , feel free to remove or edit 🤗'
            context.bot.send_message(update.message.from_user.id,
                                     text=f"If you like my work you can greet me anytime, {dev}, or you can check "
                                          f"my {github} profile", parse_mode="Markdown", disable_web_page_preview=True)

        except telegram.error.BadRequest:
            time.sleep(2)
            context.bot.send_message(update.message.from_user.id,
                                     text="Failed to retrieve the group information, please check your current"
                                          " settings", parse_mode="Markdown")

    def from_user(self, new_update, new_context):  # Get name of the user
        user_name = "Name"
        if new_update.message.from_user.last_name is not None:
            user_name = new_update.message.from_user.first_name + " " + new_update.message.from_user.last_name

        elif new_update.message.from_user.last_name is None:
            user_name = new_update.message.from_user.first_name

        return user_name

    def text(self, update, context):
        name = self.from_user(update, context)
        message_id_1 = 0
        message_id_2 = 0

        if update.message.reply_to_message is not None:  # Update is reply of previous message.
            if update.message.chat.id == self.first_group:  # Post is coming from Ch1
                message_id_1 = update.message.message_id
                message = context.bot.send_message(
                    self.second_group, text=f"*From {name}:* {self.translation_(0, update.message.text)}",
                    reply_to_message_id=DB().find_id(1, update.message.reply_to_message.message_id),
                    parse_mode="Markdown")

                message_id_2 = message.message_id

            elif update.message.chat.id == self.second_group:  # Post is coming from Ch2
                message_id_2 = update.message.message_id
                message = context.bot.send_message(
                    self.first_group, text=f"*From {name}:* {self.translation_(1, update.message.text)}",
                    reply_to_message_id=DB().find_id(2, update.message.reply_to_message.message_id),
                    parse_mode="Markdown")

                message_id_1 = message.message_id

        else:
            if update.message.chat.id == self.first_group:
                message_id_1 = update.message.message_id
                message = context.bot.send_message(
                    self.second_group, text=f"*From {name}:* {self.translation_(0, update.message.text)}",
                    parse_mode="Markdown")

                message_id_2 = message.message_id

            elif update.message.chat.id == self.second_group:
                message_id_2 = update.message.message_id
                message = context.bot.send_message(
                    self.first_group, text=f"*From {name}:* {self.translation_(1, update.message.text)}",
                    parse_mode="Markdown")

                message_id_1 = message.message_id

        DB().add_new_data(message_id_1, message_id_2)  # saving post id

    def photo(self, update, context):
        name = self.from_user(update, context)
        message_id_1 = 0
        message_id_2 = 0

        if update.message.reply_to_message is not None:  # Update is reply of previous message.
            if update.message.chat.id == self.first_group:  # Post is coming from Ch1
                message_id_1 = update.message.message_id

                if update.message.caption is None:
                    message = context.bot.send_photo(
                        self.second_group, photo=update.message.photo[-1].file_id,
                        caption=f"*From {name}*",
                        reply_to_message_id=DB().find_id(1, update.message.reply_to_message.message_id),
                        parse_mode="Markdown")

                    message_id_2 = message.message_id

                elif update.message.caption is not None:
                    message = context.bot.send_photo(
                        self.second_group, photo=update.message.photo[-1].file_id,
                        caption=f"*From {name}:* {self.translation_(1, update.message.caption)}",
                        reply_to_message_id=DB().find_id(1, update.message.reply_to_message.message_id),
                        parse_mode="Markdown")

                    message_id_2 = message.message_id

            elif update.message.chat.id == self.second_group:  # Post is coming from Ch2
                message_id_2 = update.message.message_id

                if update.message.caption is None:
                    message = context.bot.send_photo(
                        self.first_group, photo=update.message.photo[-1].file_id, caption=f"*From {name}*",
                        reply_to_message_id=DB().find_id(2, update.message.reply_to_message.message_id),
                        parse_mode="Markdown")

                    message_id_1 = message.message_id

                elif update.message.caption is not None:
                    message = context.bot.send_photo(
                        self.first_group, photo=update.message.photo[-1].file_id,
                        caption=f"*From {name}:* {self.translation_(1, update.message.caption)}",
                        reply_to_message_id=DB().find_id(2, update.message.reply_to_message.message_id),
                        parse_mode="Markdown")

                    message_id_1 = message.message_id

        else:
            if update.message.chat.id == self.first_group:
                message_id_1 = update.message.message_id

                if update.message.caption is None:
                    message = context.bot.send_photo(
                        self.second_group, photo=update.message.photo[-1].file_id,
                        caption=f"*From {name}*", parse_mode="Markdown")

                    message_id_2 = message.message_id

                elif update.message.caption is not None:
                    message = context.bot.send_photo(
                        self.second_group, photo=update.message.photo[-1].file_id,
                        caption=f"*From {name}:* {self.translation_(0, update.message.caption)}",
                        parse_mode="Markdown")

                    message_id_2 = message.message_id

            elif update.message.chat.id == self.second_group:
                message_id_2 = update.message.message_id

                if update.message.caption is None:
                    message = context.bot.send_photo(
                        self.first_group, photo=update.message.photo[-1].file_id,
                        caption=f"*From {name}*", parse_mode="Markdown")

                    message_id_1 = message.message_id

                elif update.message.caption is not None:
                    message = context.bot.send_photo(
                        self.first_group, photo=update.message.photo[-1].file_id,
                        caption=f"*From {name}:* {self.translation_(1, update.message.caption)}",
                        parse_mode="Markdown")

                    message_id_1 = message.message_id

        DB().add_new_data(message_id_1, message_id_2)  # saving post id

    def doc(self, update, context):
        name = self.from_user(update, context)
        message_id_1 = 0
        message_id_2 = 0

        if update.message.reply_to_message is not None:  # Update is reply of previous message.
            if update.message.chat.id == self.first_group:  # Post is coming from Ch1
                message_id_1 = update.message.message_id

                if update.message.caption is None:
                    message = context.bot.send_document(
                        self.second_group, document=update.message.document.file_id,
                        caption=f"*From {name}*",
                        reply_to_message_id=DB().find_id(1, update.message.reply_to_message.message_id),
                        parse_mode="Markdown")

                    message_id_2 = message.message_id

                elif update.message.caption is not None:
                    message = context.bot.send_document(
                        self.second_group, document=update.message.document.file_id,
                        caption=f"*From {name}:* {self.translation_(0, update.message.caption)}",
                        reply_to_message_id=DB().find_id(1, update.message.reply_to_message.message_id),
                        parse_mode="Markdown")

                    message_id_2 = message.message_id

            elif update.message.chat.id == self.second_group:  # Post is coming from Ch2
                message_id_2 = update.message.message_id

                if update.message.caption is None:
                    message = context.bot.send_document(
                        self.first_group, document=update.message.document.file_id,
                        caption=f"*From {name}*",
                        reply_to_message_id=DB().find_id(2, update.message.reply_to_message.message_id),
                        parse_mode="Markdown")

                    message_id_1 = message.message_id

                elif update.message.caption is not None:
                    message = context.bot.send_document(
                        self.first_group, document=update.message.document.file_id,
                        caption=f"*From {name}:* {self.translation_(1, update.message.caption)}",
                        reply_to_message_id=DB().find_id(2, update.message.reply_to_message.message_id),
                        parse_mode="Markdown")

                    message_id_1 = message.message_id

        else:
            if update.message.chat.id == self.first_group:
                message_id_1 = update.message.message_id

                if update.message.caption is None:
                    message = context.bot.send_document(
                        self.second_group, document=update.message.document.file_id,
                        caption=f"*From {name}*", parse_mode="Markdown")

                    message_id_2 = message.message_id

                elif update.message.caption is not None:
                    message = context.bot.send_document(
                        self.second_group, document=update.message.document.file_id,
                        caption=f"*From {name}:* {self.translation_(0, update.message.caption)}", parse_mode="Markdown")

                    message_id_2 = message.message_id

            elif update.message.chat.id == self.second_group:
                message_id_2 = update.message.message_id

                if update.message.caption is None:
                    message = context.bot.send_document(
                        self.first_group, document=update.message.document.file_id,
                        caption=f"*From {name}*", parse_mode="Markdown")

                    message_id_1 = message.message_id

                elif update.message.caption is not None:
                    message = context.bot.send_document(
                        self.first_group, document=update.message.document.file_id,
                        caption=f"*From {name}:* {self.translation_(1, update.message.caption)}", parse_mode="Markdown")

                    message_id_1 = message.message_id

        DB().add_new_data(message_id_1, message_id_2)  # saving post id

    def vid(self, update, context):
        name = self.from_user(update, context)
        message_id_1 = 0
        message_id_2 = 0

        if update.message.reply_to_message is not None:  # Update is reply of previous message.
            if update.message.chat.id == self.first_group:  # Post is coming from Ch1
                message_id_1 = update.message.message_id

                if update.message.caption is None:
                    message = context.bot.send_video(
                        self.second_group, video=update.message.video.file_id,
                        caption=f"*From {name}*",
                        reply_to_message_id=DB().find_id(1, update.message.reply_to_message.message_id),
                        parse_mode="Markdown")

                    message_id_2 = message.message_id

                elif update.message.caption is not None:
                    message = context.bot.send_video(
                        self.second_group, video=update.message.video.file_id,
                        caption=f"*From {name}:* {self.translation_(0, update.message.caption)}",
                        reply_to_message_id=DB().find_id(1, update.message.reply_to_message.message_id),
                        parse_mode="Markdown")

                    message_id_2 = message.message_id


            elif update.message.chat.id == self.second_group:  # Post is coming from Ch2
                message_id_2 = update.message.message_id

                if update.message.caption is None:
                    message = context.bot.send_video(
                        self.first_group, video=update.message.video.file_id, caption=f"*From {name}*",
                        reply_to_message_id=DB().find_id(2, update.message.reply_to_message.message_id),
                        parse_mode="Markdown")

                    message_id_1 = message.message_id

                elif update.message.caption is not None:
                    message = context.bot.send_video(
                        self.first_group, video=update.message.video.file_id,
                        caption=f"*From {name}:* {self.translation_(1, update.message.caption)}",
                        reply_to_message_id=DB().find_id(2, update.message.reply_to_message.message_id),
                        parse_mode="Markdown")

                    message_id_1 = message.message_id

        else:
            if update.message.chat.id == self.first_group:
                message_id_1 = update.message.message_id

                if update.message.caption is None:
                    message = context.bot.send_video(
                        self.second_group, video=update.message.video.file_id,
                        caption=f"*From {name}*", parse_mode="Markdown")

                    message_id_2 = message.message_id

                elif update.message.caption is not None:
                    message = context.bot.send_video(
                        self.second_group, video=update.message.video.file_id,
                        caption=f"*From {name}:* {self.translation_(0, update.message.caption)}", parse_mode="Markdown")

                    message_id_2 = message.message_id

            elif update.message.chat.id == self.second_group:
                message_id_2 = update.message.message_id

                if update.message.caption is None:
                    message = context.bot.send_video(
                        self.first_group, video=update.message.video.file_id,
                        caption=f"*From {name}*", parse_mode="Markdown")

                    message_id_1 = message.message_id

                elif update.message.caption is not None:
                    message = context.bot.send_video(
                        self.first_group, video=update.message.video.file_id,
                        caption=f"*From {name}:* {self.translation_(1, update.message.caption)}",
                        parse_mode="Markdown")

                    message_id_1 = message.message_id

        DB().add_new_data(message_id_1, message_id_2)  # saving post id

    def error(self, update, context):
        """Log Errors caused by Updates."""
        logger.warning('Update "%s" caused error "%s"', update, context.error)

        logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

    def main(self):
        updater = Updater(token=self._token, use_context=True)
        dispatcher = updater.dispatcher
        dispatcher.add_handler(CommandHandler("start", self.start))
        dispatcher.add_handler(MessageHandler(Filters.chat(
            [self.first_group, self.second_group]) & Filters.text, self.text))

        dispatcher.add_handler(MessageHandler(Filters.chat(
            [self.first_group, self.second_group]) & Filters.photo, self.photo))

        dispatcher.add_handler(MessageHandler(Filters.chat(
            [self.first_group, self.second_group]) & Filters.document, self.doc))

        dispatcher.add_handler(MessageHandler(Filters.chat(
            [self.first_group, self.second_group]) & Filters.video, self.vid))

        updater.start_polling()
        updater.idle()


if __name__ == '__main__':
    Bot().main()
