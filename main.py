import time
import os, sys

activate_this = "/home/a0995005/order_bot/python/bin/activate_this.py"
with open(activate_this) as f:
    exec(f.read(), {"__file__": activate_this})

import logging
from datetime import datetime
from typing import Optional

import telebot
from calculations import CaloriesCalculation
from config import Security
from constants import Gender, ActivityLevel, Goal
from utils import get_telegram_username

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

bot = telebot.TeleBot(Security.TOKEN)

ACTIVITY_MAP = {
    "1": ActivityLevel.MINIMUM,
    "2": ActivityLevel.THREE_TIMES_PER_WEEK,
    "3": ActivityLevel.FIVE_TIMES_PER_WEEK,
    "4": ActivityLevel.FIVE_TIMES_PER_WEEK_INTENSIVE,
    "5": ActivityLevel.TWO_TIMES_PER_DAY_OR_EVERYDAY_INTENSIVE,
    "6": ActivityLevel.EVERYDAY_AND_PHYSICAL_WORK,
}

GOAL_MAP = {
    "1": Goal.WEIGHT_LOSS,
    "2": Goal.MUSCLE_GAIN,
    "3": Goal.MAINTAIN_WEIGHT,
}


class TelegramBot:
    """Main BOT functionality class"""

    def __init__(self):
        self.bot = bot
        self.user_data = {}

        self.bot.message_handler(func=lambda message: True)(self.welcome_handler)
        self.bot.callback_query_handler(
            func=lambda call: call.data in [Gender.MEN, Gender.WOMAN]
        )(self.handle_gender_selection)
        self.bot.callback_query_handler(
            func=lambda call: call.data in ACTIVITY_MAP.keys()
        )(self.handle_activity_selection)
        self.bot.callback_query_handler(
            func=lambda call: call.data.startswith("goal_")
        )(self.handle_goal_selection)

    @staticmethod
    def start_polling():
        while True:
            try:
                bot.infinity_polling(timeout=10, long_polling_timeout=5)
            except Exception as e:
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                log.error(
                    f"Error occurred during polling at {current_time} Exception: {e}"
                )
                time.sleep(60)
    def ask_question(self, chat_id, text, next_step, keyboard=None):
        log.info(f"Asking question: '{text}' to user {chat_id}")
        self.bot.send_message(chat_id, text, reply_markup=keyboard)
        self.bot.register_next_step_handler_by_chat_id(chat_id, next_step)

    def welcome_handler(self, message, user_data: Optional = None):
        chat_id = user_data.get("chat_id") if user_data else message.chat.id
        log.info(f"Received message from {chat_id}: {message.text}")
        if chat_id not in self.user_data:
            self.user_data[chat_id] = {}

        self.bot.send_message(
            chat_id, f"Привет {get_telegram_username(message)}! Я калькулятор БЖУ."
        )
        self.ask_question(chat_id, "Сколько тебе лет?", self.get_age)

    def get_age(self, message):
        chat_id = message.chat.id
        log.info(f"User {chat_id} provided age: {message.text}")
        user_input = message.text

        if not user_input.isdigit():
            log.warning(f"User {chat_id} entered invalid age: {user_input}")
            return self.ask_question(
                chat_id, "Введите свой реальный возраст", self.get_age
            )
        if int(user_input) < 1 or int(user_input) > 100:
            log.warning(f"User input is bullshit {user_input}")
            return self.ask_question(
                chat_id, "Введите корректный возраст", self.get_age
            )
        age = int(user_input)
        self.user_data[chat_id]["age"] = age

        gender_keyboard = telebot.types.InlineKeyboardMarkup(row_width=2)
        gender_keyboard.add(
            telebot.types.InlineKeyboardButton("Мужчина👨", callback_data=Gender.MEN),
            telebot.types.InlineKeyboardButton("Женщина👩", callback_data=Gender.WOMAN),
        )
        self.bot.send_message(chat_id, "Выберите ваш пол", reply_markup=gender_keyboard)

    def handle_gender_selection(self, call):
        chat_id = call.message.chat.id
        log.info(f"User {chat_id} selected gender: {call.data}")
        self.bot.answer_callback_query(call.id)

        gender = call.data
        self.user_data[chat_id]["gender"] = gender
        self.ask_question(chat_id, "Какой у вас вес в кг?⚖️", self.get_weight)

    def get_weight(self, message):
        chat_id = message.chat.id
        log.info(f"User {chat_id} provided weight: {message.text}")

        try:
            user_input = message.text
            if float(user_input) < 15 or float(user_input) > 300:
                log.warning(f"User {chat_id} entered bullshit weight: {user_input}")
                self.ask_question(chat_id, "Введите корректный вес", self.get_weight)

            self.user_data[chat_id]["weight"] = float(user_input)
            self.ask_question(chat_id, "Какой у вас рост в см?📏", self.get_height)
        except ValueError:
            log.warning(f"User {chat_id} entered invalid weight: {message.text}")
            self.ask_question(chat_id, "Введите корректный вес", self.get_weight)

    def get_height(self, message):
        chat_id = message.chat.id
        log.info(f"User {chat_id} provided height: {message.text}")

        try:
            height = int(message.text)
            if self.user_data:
                self.user_data[chat_id]["height"] = height
            else:
                self.welcome_handler(message, {"chat_id": chat_id})

            activity_keyboard = telebot.types.InlineKeyboardMarkup(row_width=3)
            for k, v in ACTIVITY_MAP.items():
                activity_keyboard.add(
                    telebot.types.InlineKeyboardButton(v, callback_data=k)
                )
            self.bot.send_message(
                chat_id,
                "Выберите уровень активности:🏃‍♂️",
                reply_markup=activity_keyboard,
            )
        except ValueError:
            log.warning(f"User {chat_id} entered invalid height: {message.text}")
            self.ask_question(chat_id, "Введите корректный рост.", self.get_height)

    def handle_activity_selection(self, call):
        chat_id = call.message.chat.id
        log.info(f"User {chat_id} selected activity level: {call.data}")
        self.bot.answer_callback_query(call.id)

        activity_level = ACTIVITY_MAP.get(call.data)
        if self.user_data and self.user_data[chat_id]:
            self.user_data[chat_id]["activity_level"] = activity_level
        else:
            self.welcome_handler(call.message, {"chat_id": chat_id})

        goal_keyboard = telebot.types.InlineKeyboardMarkup(row_width=3)
        goal_keyboard.add(
            telebot.types.InlineKeyboardButton("Похудение", callback_data="goal_1"),
            telebot.types.InlineKeyboardButton(
                "Набор мышечной массы", callback_data="goal_2"
            ),
            telebot.types.InlineKeyboardButton(
                "Поддержание веса", callback_data="goal_3"
            ),
        )
        self.bot.send_message(
            chat_id, "Выберите вашу цель🎯", reply_markup=goal_keyboard
        )

    def handle_goal_selection(self, call):
        chat_id = call.message.chat.id
        log.info(f"User {chat_id} selected goal: {call.data}")
        self.bot.answer_callback_query(call.id)

        goal_key = call.data.split("_")[1]
        goal = GOAL_MAP.get(goal_key)

        if goal:
            if self.user_data:
                self.user_data[chat_id]["goal"] = goal
                self.calculate_results(chat_id, call.message)
            else:
                self.welcome_handler(call.message, {"chat_id": chat_id})
        else:
            log.error(f"Invalid goal selection by user {chat_id}: {call.data}")
            self.bot.send_message(
                chat_id, "Произошла ошибка. Попробуйте выбрать цель еще раз."
            )

    def calculate_results(self, chat_id, message):
        user_info = self.user_data.get(chat_id, {})
        log.info(f"Calculating results for user {chat_id}: {user_info}")

        try:
            age = user_info["age"]
            gender = user_info["gender"]
            weight = user_info["weight"]
            height = user_info["height"]
            activity_level = user_info["activity_level"]
            goal = user_info["goal"]

            results = CaloriesCalculation.get_calorie_info(
                weight, height, age, gender, activity_level, goal
            )

            self.bot.send_message(
                chat_id,
                f"🌟 *Результаты:* 🌟\n\n"
                f"🔥 *Базальный метаболизм:* {int(results['BMR'])} ккал\n"
                f"🍽️ *Общие калории:* {int(results['Total Calories'])} ккал\n"
                f"💪 *Белки:* {int(results['Protein (grams)'])} г\n"
                f"🧈 *Жиры:* {int(results['Fat (grams)'])} г\n"
                f"🍞 *Углеводы:* {int(results['Carbs (grams)'])} г\n",
                parse_mode="Markdown",
            )
            del self.user_data[chat_id]
        except KeyError as e:
            log.error(f"Missing data for user {chat_id}: {e}")
            self.bot.send_message(
                chat_id, "Произошла ошибка. Пожалуйста, начните с самого начала."
            )
            del self.user_data[chat_id]
            self.welcome_handler(message, {"chat_id": chat_id})


if __name__ == "__main__":
    telegram_bot = TelegramBot()
    telegram_bot.start_polling()
