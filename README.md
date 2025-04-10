# Telegram Invite Bot

🌟 **English**

A Python-based Telegram bot for managing invites to a private channel using aiogram 3.x and SQLite. This bot allows users to create single-use invite links, view a paginated list of invites with their status and expiration dates, and provides an admin panel for managing settings.

### 🚀 Features
- **Invite Creation**: Generate single-use invite links with configurable expiration (default: 30 days).
- **Invite Listing**: View invites with pagination (10 per page), including code, status (Active/Used/Expired), and expiration date.
- **Admin Panel**: Restricted access for editing welcome message, info text, and invite duration.
- **Database**: Uses SQLite to store invites and settings.

### 🛠️ Installation
1. Install the required package: `pip install aiogram`
2. Update `BOT_TOKEN`, `CHANNEL_ID`, and `ADMIN_ID` in `invite_bot.py` with your values.
3. Ensure the bot is an admin in the private channel with invite link permissions.
4. Run the bot: `python invite_bot.py`

### 📜 License
MIT License

---

🌟 **Русский**

Бот для Telegram на Python для управления приглашениями в приватный канал, построенный на aiogram 3.x и SQLite. Этот бот позволяет пользователям создавать одноразовые ссылки-приглашения, просматривать список инвайтов с пагинацией, статусом и сроком действия, а также предоставляет админ-панель для управления настройками.

### 🚀 Возможности
- **Создание инвайтов**: Генерация одноразовых ссылок с настраиваемым сроком действия (по умолчанию: 30 дней).
- **Список инвайтов**: Просмотр инвайтов с пагинацией (по 10 на страницу), включая код, статус (Активен/Использован/Просрочен) и дату окончания.
- **Админ-панель**: Ограниченный доступ для редактирования приветственного сообщения, текста информации и срока действия инвайтов.
- **База данных**: Использует SQLite для хранения инвайтов и настроек.

### 🛠️ Установка
1. Установите необходимую библиотеку: `pip install aiogram`
2. Обновите `BOT_TOKEN`, `CHANNEL_ID` и `ADMIN_ID` в файле `invite_bot.py` своими значениями.
3. Убедитесь, что бот добавлен в приватный канал как администратор с правами на создание ссылок.
4. Запустите бота: `python invite_bot.py`

### 📜 Лицензия
Лицензия MIT
