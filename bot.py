import os
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# Определяем состояния для ConversationHandler
CHOICE, REGISTER_NAME, REGISTER_EMAIL, REGISTER_PASSWORD, REGISTER_PASSWORD_CONFIRM, REGISTER_CONTRACT_ID, \
REGISTER_CONTRACT_TYPE, REGISTER_CONTRACT_START, REGISTER_CONTRACT_END, REGISTER_CONTRACT_STATUS, \
REGISTER_ADMIN, REGISTER_ADMIN_CODE, LOGIN, MENU, ADMIN_MENU = range(15)

# Хранилище данных (временное, вместо базы данных)
users = {}
contracts = {}

# Код администратора
ADMIN_CODE = "12345"

# Функция для проверки формата email
def validate_email(email):
    return "@" in email and "." in email.split("@")[-1]

# Начало работы с ботом
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    reply_keyboard = [["Зарегистрироваться", "Войти"]]
    await update.message.reply_text(
        "Здравствуйте! Я чат-бот для управления договоров от Ростелеком. Что хотите сделать?",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )
    return CHOICE

# Выбор действия
async def choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_choice = update.message.text
    if user_choice == "Зарегистрироваться":
        await update.message.reply_text("Введите ваше имя:", reply_markup=ReplyKeyboardRemove())
        return REGISTER_NAME
    elif user_choice == "Войти":
        await update.message.reply_text("Введите ваше имя для входа:", reply_markup=ReplyKeyboardRemove())
        return LOGIN
    else:
        await update.message.reply_text("Пожалуйста, выберите один из предложенных вариантов.")
        return CHOICE

# Регистрация: имя
async def register_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["name"] = update.message.text
    await update.message.reply_text("Введите ваш email:")
    return REGISTER_EMAIL

# Регистрация: email с валидацией
async def register_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    email = update.message.text
    if not validate_email(email):
        await update.message.reply_text(
            "Неверный формат email. Email должен содержать '@' и домен (например, .com). Попробуйте снова."
        )
        return REGISTER_EMAIL
    context.user_data["email"] = email
    await update.message.reply_text("Придумайте пароль:")
    return REGISTER_PASSWORD

# Регистрация: пароль
async def register_password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["password"] = update.message.text
    await update.message.reply_text("Подтвердите пароль:")
    return REGISTER_PASSWORD_CONFIRM

# Регистрация: подтверждение пароля
async def register_password_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    password_confirm = update.message.text
    if password_confirm != context.user_data["password"]:
        await update.message.reply_text("Пароли не совпадают. Придумайте пароль заново.")
        return REGISTER_PASSWORD
    await update.message.reply_text("Введите ID договора:")
    return REGISTER_CONTRACT_ID

# Регистрация: ID договора с проверкой уникальности
async def register_contract_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    contract_id = update.message.text
    if contract_id in contracts:
        await update.message.reply_text("Этот ID договора уже существует. Введите другой ID.")
        return REGISTER_CONTRACT_ID
    context.user_data["contract_id"] = contract_id
    reply_keyboard = [["Интернет", "Телевидение", "Телефония"]]
    await update.message.reply_text(
        "Выберите тип договора:", reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )
    return REGISTER_CONTRACT_TYPE

# Регистрация: тип договора
async def register_contract_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["contract_type"] = update.message.text
    await update.message.reply_text("Введите дату начала договора (например, 01.03.2025):", reply_markup=ReplyKeyboardRemove())
    return REGISTER_CONTRACT_START

# Регистрация: дата начала
async def register_contract_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["contract_start"] = update.message.text
    await update.message.reply_text("Введите дату окончания договора (например, 01.03.2026):")
    return REGISTER_CONTRACT_END

# Регистрация: дата окончания
async def register_contract_end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["contract_end"] = update.message.text
    reply_keyboard = [["Активен", "Приостановлен", "Расторгнут"]]
    await update.message.reply_text(
        "Выберите статус договора:", reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )
    return REGISTER_CONTRACT_STATUS

# Регистрация: статус договора
async def register_contract_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["contract_status"] = update.message.text
    reply_keyboard = [["Да", "Нет"]]
    await update.message.reply_text(
        "Вы администратор?", reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )
    return REGISTER_ADMIN

# Регистрация: администратор
async def register_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["is_admin"] = update.message.text == "Да"
    if context.user_data["is_admin"]:
        await update.message.reply_text("Введите код доступа для администратора:", reply_markup=ReplyKeyboardRemove())
        return REGISTER_ADMIN_CODE
    else:
        return await finish_registration(update, context)

# Регистрация: код администратора
async def register_admin_code(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    admin_code = update.message.text
    if admin_code != ADMIN_CODE:
        await update.message.reply_text("Неверный код доступа. Регистрация завершена без прав администратора.")
        context.user_data["is_admin"] = False
    return await finish_registration(update, context)

# Завершение регистрации
async def finish_registration(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    users[user_id] = {
        "name": context.user_data["name"],
        "email": context.user_data["email"],
        "password": context.user_data["password"],
        "is_admin": context.user_data["is_admin"]
    }
    contracts[context.user_data["contract_id"]] = {
        "user_id": user_id,
        "type": context.user_data["contract_type"],
        "start_date": context.user_data["contract_start"],
        "end_date": context.user_data["contract_end"],
        "status": context.user_data["contract_status"]
    }
    reply_keyboard = [["Войти", "Завершить"]]
    await update.message.reply_text(
        "Регистрация завершена! Что хотите сделать?", reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )
    return CHOICE

# Авторизация
async def login(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    name = update.message.text
    if user_id in users and users[user_id]["name"] == name:
        context.user_data["user_id"] = user_id
        await update.message.reply_text(f"Вход выполнен, {name}!")
        return await menu(update, context)
    else:
        await update.message.reply_text("Имя не совпадает. Попробуйте снова.")
        return LOGIN

# Меню пользователя
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    reply_keyboard = [["Просмотреть договор", "Обновить договор", "Меню администратора", "Выйти"]]
    await update.message.reply_text(
        "Выберите действие:", reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )
    return MENU

# Обработка выбора в меню
async def menu_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    choice = update.message.text
    user_id = context.user_data["user_id"]
    if choice == "Просмотреть договор":
        contract_id = next((cid for cid, contract in contracts.items() if contract["user_id"] == user_id), None)
        if contract_id:
            contract = contracts[contract_id]
            await update.message.reply_text(
                f"Ваш договор:\nID: {contract_id}\nТип: {contract['type']}\nДата начала: {contract['start_date']}\n"
                f"Дата окончания: {contract['end_date']}\nСтатус: {contract['status']}"
            )
        else:
            await update.message.reply_text("У вас нет договора.")
        return await menu(update, context)
    elif choice == "Обновить договор":
        await update.message.reply_text("Обновление договора пока недоступно.")
        return await menu(update, context)
    elif choice == "Меню администратора":
        if users[user_id]["is_admin"]:
            return await admin_menu(update, context)
        else:
            await update.message.reply_text("У вас нет прав администратора.")
            return await menu(update, context)
    elif choice == "Выйти":
        await update.message.reply_text("Вы вышли из системы.")
        return await start(update, context)

# Меню администратора
async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    reply_keyboard = [["Просмотреть все договоры", "Добавить пользователя", "Удалить пользователя", "Выйти"]]
    await update.message.reply_text(
        "Меню администратора. Выберите действие:", reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )
    return ADMIN_MENU

# Обработка выбора в меню администратора
async def admin_menu_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    choice = update.message.text
    if choice == "Просмотреть все договоры":
        if contracts:
            response = "Все договоры:\n"
            for contract_id, contract in contracts.items():
                response += f"ID: {contract_id}, Тип: {contract['type']}, Статус: {contract['status']}\n"
            await update.message.reply_text(response)
        else:
            await update.message.reply_text("Договоров нет.")
        return await admin_menu(update, context)
    elif choice == "Добавить пользователя":
        await update.message.reply_text("Введите имя нового пользователя:")
        return REGISTER_NAME
    elif choice == "Удалить пользователя":
        await update.message.reply_text("Удаление пользователя недоступно (нужна база данных).")
        return await admin_menu(update, context)
    elif choice == "Выйти":
        return await menu(update, context)

# Отмена
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Действие отменено.", reply_markup=ReplyKeyboardRemove())
    return await start(update, context)

def main() -> None:
    # Создаем приложение с токеном из переменной окружения
    app = Application.builder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()

    # Создаем ConversationHandler
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
            REGISTER_ADMIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_admin)],
            REGISTER_ADMIN_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_admin_code)],
            LOGIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, login)],
            MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, menu_choice)],
            ADMIN_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_menu_choice)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    # Добавляем обработчик
    app.add_handler(conv_handler)

    # Запускаем бота
    app.run_polling()

if __name__ == "__main__":
    main()
