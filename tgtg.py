import telebot
from telebot import types
import threading
import time
import json
import os

# Токен вашего бота
bot = telebot.TeleBot('6469687404:AAEX_go4bLMGEmAzS7GrYi_0qdtHjQmx6HU')

# Файл для сохранения данных пользователей
USER_DATA_FILE = 'user_data.json'

# Начальные параметры
STARTING_BALANCE = 1000
STARTING_HOURLY_INCOME = 100
INCOME_INTERVAL = 60  # секунды
CHANNEL_USERNAME = "@scamcoinofficia"
LEVELS = {
    1: {'balance_required': 1000, 'bonus': 0},
    2: {'balance_required': 10000, 'bonus': 5000},
    3: {'balance_required': 100000, 'bonus': 10000}
}

# Загружаем данные пользователей
try:
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, 'r') as file:
            users = json.load(file)
        print(f"Общее количество пользователей: {len(users)}")
    else:
        users = {}
        print("Общее количество пользователей: 0")
except Exception as e:
    print(f"Ошибка при загрузке данных пользователей: {e}")
    users = {}

# Функция для сохранения данных пользователей
def save_user_data():
    try:
        with open(USER_DATA_FILE, 'w') as file:
            json.dump(users, file)
    except Exception as e:
        print(f"Ошибка при сохранении данных пользователей: {e}")

# Инициализация нового пользователя
def init_user(user_id):
    if user_id not in users:
        users[user_id] = {
            'balance': STARTING_BALANCE,
            'hourly_income': STARTING_HOURLY_INCOME,
            'staked': 0,
            'referrals': [],
            'level': 1,
            'referred_by': None,
            'tasks_completed': False  # Новое поле для отслеживания выполнения задания
        }

# Функция для начисления дохода за стекинг
def distribute_staking_income():
    while True:
        for user_id, user_data in users.items():
            user_data['balance'] += user_data['staked'] * (0.10 / 3600)
        save_user_data()
        time.sleep(INCOME_INTERVAL)

# Запуск фонового процесса для начисления дохода
income_thread = threading.Thread(target=distribute_staking_income, daemon=True)
income_thread.start()

# Основное меню
def main_menu():
    keyboard = types.ReplyKeyboardMarkup(row_width=2)
    button_income = types.KeyboardButton('Доход')
    button_referrals = types.KeyboardButton('Реф система')
    button_tasks = types.KeyboardButton('Задания')
    button_balance = types.KeyboardButton('Баланс')
    keyboard.add(button_income, button_referrals, button_tasks, button_balance)
    return keyboard

# Меню для раздела "Доход"
def income_menu():
    keyboard = types.ReplyKeyboardMarkup(row_width=1)
    button_staking = types.KeyboardButton('Стекинг')
    button_tasks = types.KeyboardButton('Задания')
    button_referrals = types.KeyboardButton('Рефералы')
    button_back = types.KeyboardButton('Назад')
    keyboard.add(button_staking, button_tasks, button_referrals, button_back)
    return keyboard

# Меню для раздела "Реф система"
def referral_menu():
    keyboard = types.ReplyKeyboardMarkup(row_width=1)
    button_referral_link = types.KeyboardButton('Реф ссылка')
    button_my_referrals = types.KeyboardButton('Мои рефералы')
    button_back = types.KeyboardButton('Назад')
    keyboard.add(button_referral_link, button_my_referrals, button_back)
    return keyboard

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = message.from_user.id
    referrer_id = None
    if len(message.text.split()) > 1:
        try:
            referrer_id = int(message.text.split()[1])
        except ValueError:
            bot.send_message(message.chat.id, "Некорректный реферальный код.", reply_markup=main_menu())
            return

    if user_id not in users:
        users[user_id] = {
            'balance': STARTING_BALANCE,
            'hourly_income': STARTING_HOURLY_INCOME,
            'staked': 0,
            'referrals': [],
            'level': 1,
            'referred_by': referrer_id,
            'tasks_completed': False  # Новое поле для отслеживания выполнения задания
        }
        if referrer_id and referrer_id in users and referrer_id != user_id:
            users[referrer_id]['balance'] += 1000
            users[referrer_id]['referrals'].append(user_id)
            bot.send_message(referrer_id, f"Вы получили 1000 монет за приглашение нового пользователя! Ваш текущий баланс: {users[referrer_id]['balance']} монет.")
            save_user_data()

    user_data = users[user_id]
    balance_message = (f"Привет! Я бот. Ваш текущий баланс: {user_data['balance']} монет. "
                       f"Ваш доход в час: {user_data['hourly_income']} монет.\n"
                       "Для начала вы можете ознакомиться с нашими функциями, используя меню ниже.")
    bot.send_message(message.chat.id, balance_message, reply_markup=main_menu())
    update_level(user_id)
    save_user_data()

# Обновление уровня пользователя
def update_level(user_id):
    user_data = users[user_id]
    for level, criteria in sorted(LEVELS.items()):
        if user_data['balance'] >= criteria['balance_required']:
            if user_data['level'] < level:
                user_data['level'] = level
                user_data['balance'] += criteria['bonus']
                bot.send_message(user_id, f"Поздравляем! Вы достигли {level} уровня и получили бонус {criteria['bonus']} монет!")
        else:
            break

# Обработчик нажатия кнопки "Доход"
@bot.message_handler(func=lambda message: message.text == 'Доход')
def handle_income(message):
    bot.send_message(message.chat.id, "Выберите раздел для управления доходом:", reply_markup=income_menu())

# Обработчик нажатия кнопки "Стекинг"
@bot.message_handler(func=lambda message: message.text == 'Стекинг')
def handle_staking(message):
    bot.send_message(message.chat.id, "Стекинг позволяет вам заморозить монеты и получать 10% от замороженной суммы каждый час. Введите количество монет, которые вы хотите заморозить для стекинга:")
    bot.register_next_step_handler(message, process_staking_amount)

# Обработка введенного пользователем количества монет для стекинга
def process_staking_amount(message):
    try:
        amount = float(message.text)
        user_id = message.from_user.id
        init_user(user_id)
        user_data = users[user_id]
        
        if amount <= 0:
            bot.send_message(message.chat.id, "Пожалуйста, введите положительное число.", reply_markup=income_menu())
            return
        
        if user_data['balance'] < amount:
            bot.send_message(message.chat.id, f"У вас недостаточно средств. Ваш текущий баланс: {user_data['balance']} монет.", reply_markup=main_menu())
            return
        
        user_data['balance'] -= amount
        user_data['staked'] += amount
        hourly_profit = amount * 0.10
        user_data['hourly_income'] += hourly_profit

        bot.send_message(message.chat.id, f"Вы успешно заморозили {amount} монет. Вы будете получать 10% от этой суммы каждый час.", reply_markup=main_menu())
        bot.send_message(message.chat.id, f"Ваш доход увеличился на {hourly_profit} монет каждый час. Текущий баланс: {user_data['balance']} монет.", reply_markup=main_menu())
        update_level(user_id)
        save_user_data()
    except ValueError:
        bot.send_message(message.chat.id, "Пожалуйста, введите корректное число.", reply_markup=income_menu())

# Обработчик нажатия кнопки "Задания"
@bot.message_handler(func=lambda message: message.text == 'Задания')
def handle_tasks(message):
    user_id = message.from_user.id
    init_user(user_id)
    user_data = users[user_id]

    if user_data['tasks_completed']:
        bot.send_message(message.chat.id, "Вы уже выполнили задание. Невозможно выполнить его снова.", reply_markup=main_menu())
    else:
        keyboard = types.InlineKeyboardMarkup()
        subscribe_button = types.InlineKeyboardButton(text="Подписаться на канал", url=f"https://t.me/{CHANNEL_USERNAME.lstrip('@')}")
        check_subscription_button = types.InlineKeyboardButton(text="Проверить подписку", callback_data="check_subscription")
        keyboard.add(subscribe_button)
        keyboard.add(check_subscription_button)
        bot.send_message(message.chat.id, "Подпишитесь на канал для получения 10,000 монет. После подписки нажмите 'Проверить подписку' для получения бонуса:", reply_markup=keyboard)

# Обработчик проверки подписки
@bot.callback_query_handler(func=lambda call: call.data == 'check_subscription')
def check_subscription(call):
    user_id = call.from_user.id
    init_user(user_id)
    user_data = users[user_id]
    
    try:
        chat_member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        if chat_member.status in ['member', 'administrator', 'creator']:
            if not user_data['tasks_completed']:
                user_data['balance'] += 10000
                user_data['tasks_completed'] = True
                bot.send_message(call.message.chat.id, "Вы успешно подписались на канал. Вам начислено 10,000 монет.", reply_markup=main_menu())
                update_level(user_id)
                save_user_data()
            else:
                bot.send_message(call.message.chat.id, "Вы уже выполнили это задание ранее.", reply_markup=main_menu())
        else:
            bot.send_message(call.message.chat.id, "Вы не подписаны на канал. Пожалуйста, подпишитесь и попробуйте снова.", reply_markup=main_menu())
    except telebot.apihelper.ApiTelegramException as e:
        bot.send_message(call.message.chat.id, f"Ошибка: {e.description}. Пожалуйста, убедитесь, что бот является администратором канала и попробуйте снова.", reply_markup=main_menu())

# Обработчик нажатия кнопки "Баланс"
@bot.message_handler(func=lambda message: message.text == 'Баланс')
def handle_balance(message):
    user_id = message.from_user.id
    init_user(user_id)
    user_data = users[user_id]
    bot.send_message(message.chat.id, f"Ваш текущий баланс: {user_data['balance']} монет. Ваш доход в час: {user_data['hourly_income']} монет. Ваш уровень: {user_data['level']}", reply_markup=main_menu())

# Обработчик нажатия кнопки "Назад"
@bot.message_handler(func=lambda message: message.text == 'Назад')
def handle_back(message):
    bot.send_message(message.chat.id, "Вы вернулись в главное меню.", reply_markup=main_menu())

# Обработчик нажатия кнопки "Реф система"
@bot.message_handler(func=lambda message: message.text == 'Реф система')
def handle_referral_system(message):
    bot.send_message(message.chat.id, "Реферальная система позволяет вам приглашать друзей и получать бонусы за их активность. Выберите опцию:", reply_markup=referral_menu())

# Обработчик нажатия кнопки "Реф ссылка"
@bot.message_handler(func=lambda message: message.text == 'Реф ссылка')
def handle_referral_link(message):
    user_id = message.from_user.id
    referral_link = f"https://t.me/{bot.get_me().username}?start={user_id}"
    bot.send_message(message.chat.id, f"Ваша реферальная ссылка: {referral_link}\nПриглашайте друзей и получайте бонусы за их активность.", reply_markup=referral_menu())

# Обработчик нажатия кнопки "Мои рефералы"
@bot.message_handler(func=lambda message: message.text == 'Мои рефералы')
def handle_my_referrals(message):
    user_id = message.from_user.id
    init_user(user_id)
    user_data = users[user_id]
    referrals = user_data.get('referrals', [])
    referral_message = f"У вас {len(referrals)} рефералов.\n"
    if referrals:
        referral_message += "Ваши рефералы:\n"
        for ref_id in referrals:
            ref_user_data = users.get(ref_id, {'balance': 0, 'hourly_income': 0, 'referrals': [], 'level': 1})
            referral_message += (f"Никнейм: @{bot.get_chat(ref_id).username}, Уровень: {ref_user_data['level']}, "
                                 f"Баланс: {ref_user_data['balance']} монет, "
                                 f"Рефералов: {len(ref_user_data['referrals'])}\n")
    bot.send_message(message.chat.id, referral_message, reply_markup=referral_menu())

bot.polling()
