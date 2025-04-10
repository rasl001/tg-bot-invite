#!/usr/bin/env python3
"""
Telegram Invite Bot
==================
A Telegram bot for managing invites to a private channel. Built with aiogram 3.x and SQLite.
Features include invite creation, listing with pagination, and an admin panel for settings.

Бот для Telegram для управления приглашениями в приватный канал. Построен на aiogram 3.x и SQLite.
Функции включают создание инвайтов, список с пагинацией и админ-панель для настроек.

Author: rasl
Date: April 2025
License: MIT License (see below)

Requirements:
- Python 3.8+
- aiogram 3.x (`pip install aiogram`)

Usage:
1. Replace BOT_TOKEN, CHANNEL_ID, and ADMIN_ID with your values.
2. Ensure the bot is an admin in the private channel with invite link permissions.
3. Run the script: `python invite_bot.py`

Использование:
1. Замените BOT_TOKEN, CHANNEL_ID и ADMIN_ID на свои значения.
2. Убедитесь, что бот является админом в приватном канале с правами на создание ссылок.
3. Запустите скрипт: `python invite_bot.py`

MIT License:
Permission is hereby granted, free of charge, to any person obtaining a copy of this software...
"""

import asyncio
import sqlite3
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, ChatInviteLink
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

# Bot Configuration / Конфигурация бота
BOT_TOKEN = 'TOKEN'  # Replace with your bot token / Замените на токен вашего бота
CHANNEL_ID = -100XXXXXXXXXX  # Replace with your private channel ID / Замените на ID вашего приватного канала
ADMIN_ID = XXXXXXXXX  # Replace with your Telegram user ID / Замените на ваш Telegram ID
DEFAULT_INVITE_DAYS = 30  # Default invite expiration in days / Срок действия инвайта по умолчанию в днях

# Initialize Bot and Dispatcher / Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# Finite State Machine States for Admin Panel / Состояния конечного автомата для админ-панели
class AdminStates(StatesGroup):
    edit_welcome = State()
    edit_info = State()
    edit_invite_days = State()


# Database Initialization / Инициализация базы данных
def init_db():
    """Initialize SQLite database with invites and settings tables.
    Инициализация базы данных SQLite с таблицами инвайтов и настроек."""
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()

    # Create invites table / Создание таблицы инвайтов
    c.execute('''CREATE TABLE IF NOT EXISTS invites
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  code TEXT UNIQUE,
                  link TEXT,
                  created_at TIMESTAMP,
                  expires_at TIMESTAMP,
                  used INTEGER DEFAULT 0,
                  user_id INTEGER)''')

    # Create settings table / Создание таблицы настроек
    c.execute('''CREATE TABLE IF NOT EXISTS settings
                 (key TEXT PRIMARY KEY,
                  value TEXT)''')

    # Insert default settings / Вставка настроек по умолчанию
    default_settings = [
        ('welcome_msg', 'Welcome! This bot manages access to a private Telegram channel.'),
        ('info_msg', 'This bot creates and manages invite links for a private channel.'),
        ('invite_days', str(DEFAULT_INVITE_DAYS))
    ]
    for key, value in default_settings:
        c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (key, value))

    conn.commit()  # Save changes / Сохранение изменений
    conn.close()  # Close connection / Закрытие соединения


# Utility Functions / Утилитарные функции
def generate_code(length=8):
    """Generate a random invite code of specified length.
    Генерация случайного кода приглашения заданной длины."""
    import random
    import string
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def get_setting(key):
    """Retrieve a setting value from the database.
    Получение значения настройки из базы данных."""
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key = ?", (key,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None


def update_setting(key, value):
    """Update or insert a setting value in the database.
    Обновление или вставка значения настройки в базу данных."""
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()


async def check_bot_permissions():
    """Check if the bot has admin rights and can create invite links in the channel.
    Проверка, имеет ли бот права администратора и может ли создавать ссылки в канале."""
    try:
        chat = await bot.get_chat(CHANNEL_ID)
        admins = await bot.get_chat_administrators(CHANNEL_ID)
        bot_id = (await bot.get_me()).id
        for admin in admins:
            if admin.user.id == bot_id and admin.can_invite_users:
                print(f"Bot has invite permissions in channel: {chat.title}")
                print(f"Бот имеет права на создание инвайтов в канале: {chat.title}")
                return True
        print("Bot lacks invite permissions or is not an admin!")
        print("Бот не имеет прав на создание инвайтов или не является админом!")
        return False
    except Exception as e:
        print(f"Error checking bot permissions: {str(e)}")
        print(f"Ошибка при проверке прав бота: {str(e)}")
        return False


# Menu Functions / Функции меню
def get_main_menu():
    """Generate the main menu inline keyboard.
    Создание инлайн-клавиатуры главного меню."""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Create Invite", callback_data="create_invite")],
        [InlineKeyboardButton(text="List Invites", callback_data="list_invites_0")],
        [InlineKeyboardButton(text="Info", callback_data="info")],
        [InlineKeyboardButton(text="Admin Panel", callback_data="admin_menu")],
    ])
    return keyboard


# Command Handlers / Обработчики команд
@dp.message(Command("start"))
async def start_command(message: Message):
    """Handle the /start command and display the welcome message with main menu.
    Обработка команды /start и вывод приветственного сообщения с главным меню."""
    welcome_msg = get_setting("welcome_msg")
    await message.answer(welcome_msg, reply_markup=get_main_menu())


# Callback Query Handlers / Обработчики callback-запросов
@dp.callback_query(lambda c: c.data == "create_invite")
async def process_create_invite(callback: types.CallbackQuery):
    """Create a new invite link for the channel.
    Создание новой ссылки-приглашения для канала."""
    try:
        if not await check_bot_permissions():
            await callback.message.answer("Error: Bot lacks access or permissions! Add @Invitebot001_bot as admin.")
            await callback.message.answer(
                "Ошибка: Бот не имеет доступа или прав! Добавьте @Invitebot001_bot как админа.")
            return

        invite_days = int(get_setting("invite_days"))
        expire_date = datetime.now() + timedelta(days=invite_days)
        code = generate_code()

        invite_link: ChatInviteLink = await bot.create_chat_invite_link(
            chat_id=CHANNEL_ID,
            name=f"Invite_{code}",
            expire_date=int(expire_date.timestamp()),
            member_limit=1
        )

        # Save invite to database / Сохранение инвайта в базу данных
        conn = sqlite3.connect('bot_data.db')
        c = conn.cursor()
        c.execute("""INSERT INTO invites (code, link, created_at, expires_at, user_id)
                     VALUES (?, ?, ?, ?, ?)""",
                  (code, invite_link.invite_link, datetime.now(), expire_date, callback.from_user.id))
        conn.commit()
        conn.close()

        await callback.message.answer(
            f"Your invite:\n{invite_link.invite_link}\nValid until: {expire_date.strftime('%Y-%m-%d %H:%M')}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Back", callback_data="back_to_menu")]
            ])
        )
    except Exception as e:
        await callback.message.answer(f"Error: {str(e)}")
        await callback.message.answer(f"Ошибка: {str(e)}")
    await callback.answer()


@dp.callback_query(lambda c: c.data.startswith("list_invites_"))
async def process_list_invites(callback: types.CallbackQuery):
    """Display a paginated list of invites with status and expiration.
    Отображение списка инвайтов с пагинацией, статусом и сроком действия."""
    try:
        offset = int(callback.data.split("_")[2])
        conn = sqlite3.connect('bot_data.db')
        c = conn.cursor()
        c.execute("SELECT code, link, expires_at, used FROM invites ORDER BY created_at DESC LIMIT 10 OFFSET ?",
                  (offset,))
        invites = c.fetchall()
        conn.close()

        if not invites:
            await callback.message.answer(
                "No invites found.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="Back", callback_data="back_to_menu")]
                ])
            )
            await callback.answer()
            return

        response = "Invite List:\n\n"
        now = datetime.now()
        for code, link, expires_at, used in invites:
            expires_at = datetime.fromisoformat(str(expires_at))
            status = "Used" if used else ("Active" if expires_at > now else "Expired")
            response += (f"Code: {code} | Status: {status}\n"
                         f"Valid until: {expires_at.strftime('%Y-%m-%d %H:%M')}\n"
                         f"{link}\n\n")

        keyboard = InlineKeyboardMarkup(inline_keyboard=[])
        if len(invites) == 10:
            keyboard.inline_keyboard.append(
                [InlineKeyboardButton(text="Show More", callback_data=f"list_invites_{offset + 10}")])
        keyboard.inline_keyboard.append([InlineKeyboardButton(text="Back", callback_data="back_to_menu")])

        await callback.message.answer(response, reply_markup=keyboard, disable_web_page_preview=True)
    except Exception as e:
        await callback.message.answer(f"Error: {str(e)}")
        await callback.message.answer(f"Ошибка: {str(e)}")
    await callback.answer()


@dp.callback_query(lambda c: c.data == "info")
async def process_info(callback: types.CallbackQuery):
    """Display the info section.
    Отображение раздела информации."""
    info_msg = get_setting("info_msg")
    await callback.message.answer(
        info_msg,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Back", callback_data="back_to_menu")]
        ])
    )
    await callback.answer()


@dp.callback_query(lambda c: c.data == "admin_menu")
async def process_admin_menu(callback: types.CallbackQuery):
    """Display the admin panel menu (admin only).
    Отображение меню админ-панели (только для админа)."""
    if callback.from_user.id != ADMIN_ID:
        await callback.message.answer("Access denied!")
        await callback.message.answer("Доступ запрещен!")
        await callback.answer()
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Edit Welcome", callback_data="edit_welcome")],
        [InlineKeyboardButton(text="Edit Info", callback_data="edit_info")],
        [InlineKeyboardButton(text="Edit Invite Days", callback_data="edit_invite_days")],
        [InlineKeyboardButton(text="Back", callback_data="back_to_menu")]
    ])
    await callback.message.answer("Admin Panel:", reply_markup=keyboard)
    await callback.answer()


# Admin Panel FSM Handlers / Обработчики FSM для админ-панели
@dp.callback_query(lambda c: c.data == "edit_welcome")
async def process_edit_welcome(callback: types.CallbackQuery, state: FSMContext):
    """Prompt admin to edit the welcome message.
    Запрос админу на редактирование приветственного сообщения."""
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Access denied!")
        await callback.answer("Доступ запрещен!")
        return
    await callback.message.answer("Enter new welcome message:")
    await state.set_state(AdminStates.edit_welcome)
    await callback.answer()


@dp.message(AdminStates.edit_welcome)
async def save_welcome(message: Message, state: FSMContext):
    """Save the new welcome message.
    Сохранение нового приветственного сообщения."""
    update_setting("welcome_msg", message.text)
    await message.answer(
        "Welcome message updated!",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Back to Admin", callback_data="admin_menu")]
        ])
    )
    await state.clear()


@dp.callback_query(lambda c: c.data == "edit_info")
async def process_edit_info(callback: types.CallbackQuery, state: FSMContext):
    """Prompt admin to edit the info message.
    Запрос админу на редактирование информационного сообщения."""
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Access denied!")
        await callback.answer("Доступ запрещен!")
        return
    await callback.message.answer("Enter new info text:")
    await state.set_state(AdminStates.edit_info)
    await callback.answer()


@dp.message(AdminStates.edit_info)
async def save_info(message: Message, state: FSMContext):
    """Save the new info message.
    Сохранение нового информационного сообщения."""
    update_setting("info_msg", message.text)
    await message.answer(
        "Info updated!",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Back to Admin", callback_data="admin_menu")]
        ])
    )
    await state.clear()


@dp.callback_query(lambda c: c.data == "edit_invite_days")
async def process_edit_invite_days(callback: types.CallbackQuery, state: FSMContext):
    """Prompt admin to edit the invite expiration days.
    Запрос админу на редактирование срока действия инвайта."""
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Access denied!")
        await callback.answer("Доступ запрещен!")
        return
    await callback.message.answer("Enter new invite expiration days (number):")
    await state.set_state(AdminStates.edit_invite_days)
    await callback.answer()


@dp.message(AdminStates.edit_invite_days)
async def save_invite_days(message: Message, state: FSMContext):
    """Save the new invite expiration days.
    Сохранение нового срока действия инвайтов."""
    try:
        days = int(message.text)
        if days <= 0:
            raise ValueError("Days must be positive!")
        update_setting("invite_days", str(days))
        await message.answer(
            f"Invite expiration updated to {days} days!",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Back to Admin", callback_data="admin_menu")]
            ])
        )
    except ValueError:
        await message.answer("Error: Please enter a valid number!")
        await message.answer("Ошибка: Введите корректное число!")
    await state.clear()


@dp.callback_query(lambda c: c.data == "back_to_menu")
async def back_to_menu(callback: types.CallbackQuery):
    """Return to the main menu.
    Возврат в главное tiled меню."""
    welcome_msg = get_setting("welcome_msg")
    await callback.message.edit_text(welcome_msg, reply_markup=get_main_menu())
    await callback.answer()


# Main Execution / Основной запуск
async def main():
    """Initialize the database and start the bot.
    Инициализация базы данных и запуск бота."""
    init_db()
    print("Bot started")
    print("Бот запущен")
    if await check_bot_permissions():
        print("Bot successfully connected to the channel")
        print("Бот успешно подключен к каналу")
    else:
        print("Error: Bot is not added to the channel or lacks admin permissions!")
        print("Ошибка: Бот не добавлен в канал или не имеет прав администратора!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())