from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# Хранилище данных пользователей и договоров
users = {}  # {user_id: {"name": str, "email": str, "password": str, "contract": dict, "is_admin": bool}}
contracts = {}  # {contract_id: {"type": str, "start_date": str, "end_date": str, "status": str}}

# Состояния для управления диалогом
CHOICE, REGISTER_NAME, REGISTER_EMAIL, REGISTER_PASSWORD, REGISTER_PASSWORD_CONFIRM, REGISTER_CONTRACT_ID, \
REGISTER_CONTRACT_TYPE, REGISTER_CONTRACT_START, REGISTER_CONTRACT_END, REGISTER_CONTRACT_STATUS, \
REGISTER_ADMIN, LOGIN, MENU, ADMIN_MENU = range(14)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    reply_keyboard = [["Зарегистрироваться", "Войти"]]
    await update.message.reply_text(
        "Здравствуйте! Я чат-бот для управления договоров от Ростелеком. Что хотите сделать?",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )
    return CHOICE

async def choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text

    if text == "Зарегистрироваться":
        await update.message.reply_text("Введите ваше имя.", reply_markup=ReplyKeyboardRemove())
        return REGISTER_NAME
    elif text == "Войти":
        await update.message.reply_text("Введите ваше имя для входа.", reply_markup=ReplyKeyboardRemove())
        return LOGIN
    else:
        await update.message.reply_text("Пожалуйста, выберите 'Зарегистрироваться' или 'Войти'.")
        return CHOICE

async def register_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["name"] = update.message.text
    await update.message.reply_text(f"Привет, {context.user_data['name']}! Теперь введи email.")
    return REGISTER_EMAIL

async def register_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    email = update.message.text
    # Проверка формата email
    if "@" not in email or "." not in email.split("@")[-1]:
        await update.message.reply_text("Неверный формат email. Email должен содержать '@' и домен (например, .com). Попробуйте снова.")
        return REGISTER_EMAIL
    context.user_data["email"] = email
    await update.message.reply_text("Придумайте пароль (минимум 8 символов).")
    return REGISTER_PASSWORD

async def register_password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["password"] = update.message.text
    await update.message.reply_text("Повторите пароль.")
    return REGISTER_PASSWORD_CONFIRM

async def register_password_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text == context.user_data["password"]:
        await update.message.reply_text("Введите ID договора.")
        return REGISTER_CONTRACT_ID
    else:
        await update.message.reply_text("Пароли не совпадают. Придумайте пароль заново.")
        return REGISTER_PASSWORD

async def register_contract_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    contract_id = update.message.text
    # Проверка на уникальность ID
    if contract_id in contracts:
        await update.message.reply_text("Этот ID договора уже существует. Введите другой ID.")
        return REGISTER_CONTRACT_ID
    context.user_data["contract_id"] = contract_id
    reply_keyboard = [["Интернет", "Телевидение", "Телефония", "Комплексные услуги"]]
    await update.message.reply_text(
        "Выберите тип договора.",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )
    return REGISTER_CONTRACT_TYPE

async def register_contract_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["contract_type"] = update.message.text
    await update.message.reply_text("Введите дату начала.", reply_markup=ReplyKeyboardRemove())  # Удалено (например, 01.03.2025)
    return REGISTER_CONTRACT_START

async def register_contract_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["contract_start"] = update.message.text
    await update.message.reply_text("Введите дату окончания.")
    return REGISTER_CONTRACT_END

async def register_contract_end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["contract_end"] = update.message.text
    reply_keyboard = [["Активен", "Завершен", "Приостановлен"]]
    await update.message.reply_text(
        "Выберите статус договора.",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )
    return REGISTER_CONTRACT_STATUS

async def register_contract_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["contract_status"] = update.message.text
    reply_keyboard = [["Да", "Нет"]]
    await update.message.reply_text(
        "Вы администратор?",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )
    return REGISTER_ADMIN

async def register_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    text = update.message.text

    if text == "Да":
        await update.message.reply_text("Введите код доступа.", reply_markup=ReplyKeyboardRemove())
        context.user_data["is_admin"] = True
        return REGISTER_ADMIN
    else:
        context.user_data["is_admin"] = False
        users[user_id] = {
            "name": context.user_data["name"],
            "email": context.user_data["email"],
            "password": context.user_data["password"],
            "contract": {
                "id": context.user_data["contract_id"],
                "type": context.user_data["contract_type"],
                "start_date": context.user_data["contract_start"],
                "end_date": context.user_data["contract_end"],
                "status": context.user_data["contract_status"]
            },
            "is_admin": False
        }
        contracts[context.user_data["contract_id"]] = users[user_id]["contract"]
        reply_keyboard = [["Войти", "Завершить"]]
        await update.message.reply_text(
            "Регистрация завершена! Что дальше?",
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
        )
        return CHOICE

async def register_admin_code(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    users[user_id] = {
        "name": context.user_data["name"],
        "email": context.user_data["email"],
        "password": context.user_data["password"],
        "contract": {
            "id": context.user_data["contract_id"],
            "type": context.user_data["contract_type"],
            "start_date": context.user_data["contract_start"],
            "end_date": context.user_data["contract_end"],
            "status": context.user_data["contract_status"]
        },
        "is_admin": True,
        "admin_code": update.message.text
    }
    contracts[context.user_data["contract_id"]] = users[user_id]["contract"]
    reply_keyboard = [["Войти", "Завершить"]]
    await update.message.reply_text(
        "Роль администратора подтверждена. Регистрация завершена! Что дальше?",  # Удалено (код не проверяется)
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )
    return CHOICE

async def login(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    text = update.message.text

    if user_id in users and users[user_id]["name"] == text:
        context.user_data["logged_in"] = True
        reply_keyboard = [["Просмотреть договор", "Обновить договор", "Меню администратора", "Выйти"]]
        await update.message.reply_text(
            f"Вход выполнен, {text}!",
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
        )
        return MENU
    else:
        await update.message.reply_text("Имя не совпадает. Попробуйте снова.")
        await update.message.reply_text("Введите ваше имя для входа.")
        return LOGIN

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    text = update.message.text

    if text == "Просмотреть договор":
        contract = users[user_id]["contract"]
        await update.message.reply_text(
            f"Договор: ID={contract['id']}, Тип={contract['type']}, "
            f"Дата начала={contract['start_date']}, Дата окончания={contract['end_date']}, "
            f"Статус={contract['status']}"
        )
    elif text == "Обновить договор":
        await update.message.reply_text("Обновление договора недоступно (нужна база данных).")
    elif text == "Меню администратора":
        if users[user_id]["is_admin"]:
            reply_keyboard = [["Просмотреть все договоры", "Добавить пользователя", "Удалить пользователя", "Выйти"]]
            await update.message.reply_text(
                "Меню администратора:",
                reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
            )
            return ADMIN_MENU
        else:
            await update.message.reply_text("У вас нет прав администратора.")
    elif text == "Выйти":
        context.user_data["logged_in"] = False
        await update.message.reply_text("До свидания!", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

    reply_keyboard = [["Просмотреть договор", "Обновить договор", "Меню администратора", "Выйти"]]
    await update.message.reply_text(
        "Выберите действие:",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )
    return MENU

async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text

    if text == "Просмотреть все договоры":
        if contracts:
            response = "Все договоры:\n"
            for contract_id, contract in contracts.items():
                response += f"ID={contract_id}, Тип={contract['type']}, Статус={contract['status']}\n"
            await update.message.reply_text(response)
        else:
            await update.message.reply_text("Договоры отсутствуют.")
    elif text == "Добавить пользователя":
        await update.message.reply_text("Введите имя нового пользователя.")
        return REGISTER_NAME
    elif text == "Удалить пользователя":
        await update.message.reply_text("Удаление пользователя недоступно (нужна база данных).")
    elif text == "Выйти":
        context.user_data["logged_in"] = False
        await update.message.reply_text("До свидания!", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

    reply_keyboard = [["Просмотреть все договоры", "Добавить пользователя", "Удалить пользователя", "Выйти"]]
    await update.message.reply_text(
        "Меню администратора:",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )
    return ADMIN_MENU

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Действие отменено.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def main():
    import os
app = Application.builder().token(os.getenv("8102887528:AAEn8lhe2whpQoZl3G_-YFs-jQejUTnS3ew")).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, choice)],
            REGISTER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_name)],
            REGISTER_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_email)],
            REGISTER_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_password)],
            REGISTER_PASSWORD_CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_password_confirm)],
            REGISTER_CONTRACT_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_contract_id)],
            REGISTER_CONTRACT_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_contract_type)],
            REGISTER_CONTRACT_START: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_contract_start)],
            REGISTER_CONTRACT_END: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_contract_end)],
            REGISTER_CONTRACT_STATUS: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_contract_status)],
            REGISTER_ADMIN: [
                MessageHandler(filters.Regex("^(Да|Нет)$"), register_admin),
                MessageHandler(filters.TEXT & ~filters.COMMAND, register_admin_code)
            ],
            LOGIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, login)],
            MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, menu)],
            ADMIN_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_menu)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("login", login))
    app.run_polling()

if __name__ == "__main__":
    main()
