#!/usr/bin/python3
# -*- coding: utf-8 -*-

import logging
import xlwt
from telebot.types import KeyboardButton, ReplyKeyboardMarkup
from xlrd import *
from xlutils.copy import copy
import os
import datetime
import telebot
from config import token, ip
from lxml import html
import requests
from keyboa import Keyboa

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
        self.size = None
        self.url_item = None
        self.step = "step1"
        self.name_xls_file = None

    def pars_shop(self, name_item):
        """Парсинг товара на сайте"""

        url = 'https://whitepark.ru'
        catalogs = ["/catalog/ryukzaki/",
                    "/catalog/obuv/",
                    "/catalog/odezhda/",
                    "/catalog/snou/",
                    "/catalog/skeyt/",
                    "/catalog/aksessuary/"]

        for url_catalog in catalogs:
            r = requests.get(url + url_catalog + '?PAGEN_1=1&pp=1000')
            tree = html.fromstring(r.text)
            items_list_lxml = tree.xpath('.//div[@class="grid catalog_grid"]')[0]
            for item in items_list_lxml:
                if name_item == str(item.xpath('.//footer[@class="goods_desc"]/a/text()')[0]):
                    url_item = str(item.xpath('.//footer[@class="goods_desc"]/a/@href')[0])
                    resp = requests.get(url + url_item)
                    self.url_item = resp.url
                    log.info(f'Ссылка на товар {self.url_item}')
                    tree_item = html.fromstring(resp.text)
                    return list(set(tree_item.xpath('.//div[@class="wrapper__radiobutton_size"]/label/div/text()')))

    def query_analytics(self):
        """Аналитика запрошенных товаров"""
        self.name_xls_file = datetime.date.today()
        time_now = datetime.datetime.strftime(datetime.datetime.now(), '%H:%M')
        font0 = xlwt.Font()
        font0.bold = True
        style0 = xlwt.XFStyle()
        style0.font = font0
        if os.path.exists(f'{str(self.name_xls_file)}.xls'):
            workbook = open_workbook(f'{str(self.name_xls_file)}.xls', formatting_info=True)
            book = copy(workbook)
            sheet = book.get_sheet(0)
            self.count = workbook.sheet_by_index(0).nrows
        else:
            book = xlwt.Workbook('utf8')
            sheet = book.add_sheet(f'{self.name_xls_file}')
            self.count = 1
        sheet.write(0, 0, 'Время запроса', style0)
        sheet.write(0, 1, 'Наименование позиции', style0)
        sheet.write(0, 2, 'Размер', style0)
        sheet.write(0, 3, 'Ссылка', style0)
        sheet.write(self.count, 0, str(time_now))
        sheet.write(self.count, 1, self.item)
        sheet.write(self.count, 2, self.size)  # TODO - размер
        sheet.write(self.count, 3, self.url_item)
        sheet.col(0).width = 5000
        sheet.col(1).width = 15000
        sheet.col(2).width = 7000
        sheet.col(3).width = 15000
        name_book = f'{self.name_xls_file}.xls'
        book.save(name_book)

    def get_list_size(self, message):
        """Получение"""
        image_bytes = self.photo(message)
        self.item = self.firebird_connect(image_bytes)
        return self.item

    def output_xls_server(self):
        """Отправка xls файла на сервер"""
        with open(self.name_xls_file, 'rb') as file_bytes:
            headers = {
                'Content-Type': 'text/plain',
            }
            requests.post(f'http://{ip}/file_xls', headers=headers, data=file_bytes.read())

    def firebird_connect(self, image_bytes):
        """Подключение к базе"""
        headers = {
            'Content-Type': 'text/plain',
        }
        try:
            response = requests.post(f'http://{ip}/item', headers=headers, data=image_bytes)
        except requests.exceptions.ConnectionError:
            log.info(response.status_code)
        else:
            return response.text

    def photo(self, message):
        """Сохранение фото"""
        fileID = message.photo[-1].file_id
        file_info = bot.get_file(fileID)
        downloaded_file = bot.download_file(file_info.file_path)
        return downloaded_file

    def keyboard_anew(self):
        """Кнопка Начать заного"""
        button_anew = KeyboardButton('Начать заного')
        anew = ReplyKeyboardMarkup()
        anew.add(button_anew)

        return anew

    def keyboard_v2(self):
        """Формирование общей клавиатуры"""

        yes_or_no = ["Да", "Нет", "Товар не тот"]
        markup_inline = Keyboa(items=yes_or_no, copy_text_to_callback=True, items_in_row=1).keyboard
        return markup_inline

    def keyboard_clothing_sizes(self):
        """Формирование кнопок с размерами одежды"""

        clothing_sizes = ["XS", "S", "M", "L", "XL", "XXL", "Y"]
        sizes = Keyboa(items=clothing_sizes, copy_text_to_callback=True, items_in_row=4).keyboard
        return sizes

    def keyboard_shoe_sizes(self):
        """Формирование кнопок с размерами обуви"""

        shoe_sizes = ["28", "29", "30.5", "31.5", "33", "34", "35", "36", "36.5", "37", "38", "39", "40", "40.5", "41",
                      "41.5", "42", "42.5", "43", "43.5", "44", "45", "46", "46.5", "48", "49"]
        sizes = Keyboa(items=shoe_sizes, copy_text_to_callback=True, items_in_row=4).keyboard
        return sizes


if __name__ == '__main__':

    configure_logging()
    bot = telebot.TeleBot(token)
    whitepark_bot = Whitepark()

    if datetime.datetime.now().hour >= 20 and whitepark_bot.name_xls_file is not None:
        whitepark_bot.output_xls_server()
        whitepark_bot.name_xls_file = None

    @bot.callback_query_handler(func=lambda call: True)
    def answer(call):
        if call.data == "Да" and whitepark_bot.step == "step2":
            whitepark_bot.step = "step1"
            log.info(f'Пользователь: {call.message.chat.username}, получено сообщение: {call.data}')
            bot.send_message(call.message.chat.id, 'Благодарю за работу. К следующему товару')

        elif call.data == "Нет" and whitepark_bot.step == "step2":
            if "/catalog/obuv/" in whitepark_bot.url_item:
                whitepark_bot.step = "step3"
                bot.send_message(call.message.chat.id,
                                 f'Выбери необходимый размер',
                                 reply_markup=whitepark_bot.keyboard_shoe_sizes())
            else:
                whitepark_bot.step = "step3"
                bot.send_message(call.message.chat.id,
                                 f'Выбери необходимый размер',
                                 reply_markup=whitepark_bot.keyboard_clothing_sizes())

        elif call.data == "Товар не тот" and whitepark_bot.step == "step2":
            whitepark_bot.step = "step1"
            log.info(f'Пользователь: {call.message.chat.username}, получено сообщение: {call.data}')
            bot.send_message(call.message.chat.id, 'Давай попробуем заного')

        elif whitepark_bot.step == "step3":
            whitepark_bot.step = "step1"
            log.info(f'Пользователь: {call.message.chat.username}, получено сообщение: {call.data}')
            bot.send_message(call.message.chat.id, 'Благодарю за работу. К следующему товару')
            whitepark_bot.size = call.data
            whitepark_bot.query_analytics()


    @bot.message_handler(content_types=['text', 'photo'])
    def telegram_send_me(message):
        try:
            if message.content_type == 'Начать заного':
                whitepark_bot.step = "step1"
                bot.send_message(message.chat.id, 'Давай попробуем заного')
                log.info(f'Пользователь: {message.chat.username}, Нажал кнопку "Начать заного"')

            elif message.content_type == 'photo' and whitepark_bot.step == "step1":
                log.info(f'Пользователь: {message.chat.username}, прислал фото')
                item = whitepark_bot.get_list_size(message)

                if item == 'Неверный формат штрихкода':
                    log.info(f'Пользователь: {message.chat.username}, Неверный формат штрихкода')
                    bot.send_message(message.chat.id, 'Неверный формат штрихкода',
                             reply_markup=whitepark_bot.keyboard_anew())
                elif item == 'Товар не найден':
                    log.info(f'Пользователь: {message.chat.username}, Товар не найден')
                    bot.send_message(message.chat.id, 'Товар не найден',
                             reply_markup=whitepark_bot.keyboard_anew())
                else:
                    list_size = whitepark_bot.pars_shop(item)
                    text_size = ', '.join(list_size)
                    log.info(f'Пользователь: {message.chat.username}, Товар: {item} найден')
                    bot.send_message(message.chat.id,
                                     f'Товар: {item}\nРазмеры в наличии: {text_size}\nВ предложенных есть необходимый размер?',
                                     reply_markup=whitepark_bot.keyboard_v2())
                    whitepark_bot.step = "step2"
            else:
                log.info(f'Пользователь: {message.chat.username}, получено сообщение: {message.text}')
                if whitepark_bot.step == "step2":
                    bot.delete_message(message.chat.id, message.id)
                else:
                    bot.send_message(message.chat.id, 'Жду фото штрихкода',
                             reply_markup=whitepark_bot.keyboard_anew())

        except Exception as exc:
            log.exception(f'{exc}')
            bot.send_message(message.chat.id, 'Что-то пошло не так, напиши @dachibo',
                             reply_markup=whitepark_bot.keyboard_anew())


    bot.polling(none_stop=True)
