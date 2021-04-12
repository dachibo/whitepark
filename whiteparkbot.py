#!/usr/bin/python3
# -*- coding: utf-8 -*-

import logging
import xlwt
from xlrd import *
from xlutils.copy import copy
import os
import datetime
from pyzbar.pyzbar import decode
from PIL import Image
import telebot
from config import token, DATABASE
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
import fdb
from parce_shop import pars_shop


log = logging.getLogger('wp_bot')


def configure_logging():
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(logging.Formatter("%(levelname)s - %(message)s"))
    stream_handler.setLevel(logging.INFO)
    log.addHandler(stream_handler)

    file_handler = logging.FileHandler('wp_bot.log')
    file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", datefmt='%d-%m-%Y %H:%M'))
    file_handler.setLevel(logging.DEBUG)
    log.addHandler(file_handler)
    log.setLevel(logging.DEBUG)

class Whitepark():
    def __init__(self):
        self.item = None
        self.count = 1
        self.ean = None
        self.step = "step1"

    def query_analytics(self):
        """Аналитика запрошенных товаров"""
        current_date = datetime.date.today()
        time_now = datetime.datetime.strftime(datetime.datetime.now(), '%H:%M')
        font0 = xlwt.Font()
        font0.bold = True
        style0 = xlwt.XFStyle()
        style0.font = font0
        if os.path.exists(f'{str(current_date)}.xls'):
            workbook = open_workbook(f'{str(current_date)}.xls',formatting_info=True)
            book = copy(workbook)
            sheet = book.get_sheet(0)
            self.count = workbook.sheet_by_index(0).nrows
        else:
            book = xlwt.Workbook('utf8')
            sheet = book.add_sheet(f'{current_date}')
            self.count = 1
        sheet.write(0, 0, 'Время запроса', style0)
        sheet.write(0, 1, 'Наименование позиции', style0)
        sheet.write(0, 2, 'Штрихкод', style0)
        sheet.write(self.count, 0, str(time_now))
        sheet.write(self.count, 1, self.item[0][0])
        sheet.write(self.count, 2, self.ean)
        sheet.col(0).width = 5000
        sheet.col(1).width = 15000
        sheet.col(2).width = 7000
        name_book = f'{current_date}.xls'
        book.save(name_book)

    def get_list_size(self, message):
        """Получение"""
        self.barcode_image(message)
        self.item = self.firebird_connect()
        return self.item

    def firebird_connect(self):
        """Подключение к базе"""
        con = fdb.connect(**DATABASE)
        cur = con.cursor()
        cur.execute(f"select sprt.name from sprt join barcode on sprt.id = barcode.wareid where barcode = {self.ean}")
        item_name = cur.fetchall()
        con.close()
        return item_name

    def barcode_image(self, message):
        """Считывание штрихкода"""

        self.photo(message)
        image_barcode = Image.open('image.jpg')
        decoded = decode(image_barcode)
        self.ean = decoded[0].data.decode("utf-8")

    def photo(self, message):
        """Сохранение фото"""
        fileID = message.photo[-1].file_id
        file_info = bot.get_file(fileID)
        downloaded_file = bot.download_file(file_info.file_path)

        with open("image.jpg", 'wb') as new_file:
            new_file.write(downloaded_file)

    def keyboard_v2(self):
        """Формирование общей клавиатуры"""

        keyboard = ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=True)
        button_yes = KeyboardButton(text="Да")
        button_no = KeyboardButton(text="Нет")
        button_error = KeyboardButton(text="Товар не тот")
        keyboard.add(button_yes, button_no, button_error)
        return keyboard

if __name__ == '__main__':

    configure_logging()
    bot = telebot.TeleBot(token)
    whitepark_bot = Whitepark()

    @bot.message_handler(content_types=['text', 'photo'])
    def telegram_send_me(message):
        try:
            if message.text == 'Нет' and whitepark_bot.step == "step2":
                whitepark_bot.query_analytics()
                whitepark_bot.step = "step1"
                log.info(f'Пользователь: {message.chat.username}, получено сообщение: {message.text}')
                bot.send_message(message.chat.id, 'Благодарю за работу. К следующему товару')
            elif message.text == 'Да' and whitepark_bot.step == "step2":
                whitepark_bot.step = "step1"
                log.info(f'Пользователь: {message.chat.username}, получено сообщение: {message.text}')
                bot.send_message(message.chat.id, 'Благодарю за работу. К следующему товару')
            elif message.text == 'Товар не тот' and whitepark_bot.step == "step2":
                whitepark_bot.step = "step1"
                log.info(f'Пользователь: {message.chat.username}, получено сообщение: {message.text}')
                bot.send_message(message.chat.id, 'Давай попробуем заного')
            elif message.content_type == 'photo' and whitepark_bot.step == "step1":
                log.info(f'Пользователь: {message.chat.username}, прислал фото')
                item = whitepark_bot.get_list_size(message)
                if len(item) != 0:
                    list_size = pars_shop(item[0][0])
                    text_size = ', '.join(list_size)
                    log.info(f'Пользователь: {message.chat.username}, Товар: {item[0][0]} найден')
                    bot.send_message(message.chat.id, f'Товар: {item[0][0]}\nРазмеры в наличии: {text_size}\nВ предложенных есть необходимый размер?',
                                    reply_markup=whitepark_bot.keyboard_v2())
                    whitepark_bot.step = "step2"
                else:
                    log.info(f'Пользователь: {message.chat.username}, Товар не найден')
                    bot.send_message(message.chat.id, 'Товар не найден')
            else:
                log.info(f'Пользователь: {message.chat.username}, получено сообщение: {message.text}')
                if whitepark_bot.step == "step2":
                    bot.send_message(message.chat.id, 'Да или Нет')
                else:
                    bot.send_message(message.chat.id, 'Жду фото штрихкода')

        except AttributeError as exc:
            log.exception(f'Неверный формат штрихкода')
            log.exception(f'{exc}')
            bot.send_message(message.chat.id, 'Неверный формат штрихкода')
        except IndexError as exc:
            log.exception(f'Неверный формат штрихкода')
            log.exception(f'{exc}')
            bot.send_message(message.chat.id, 'Неверный формат штрихкода')
        except Exception as exc:
            log.exception(f'{exc}')
            bot.send_message(message.chat.id, 'Что-то пошло не так, напиши @dachibo')


    bot.polling(none_stop=True)
