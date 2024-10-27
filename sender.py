# -*- coding: utf-8 -*

import urllib3 
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from concurrent.futures import ThreadPoolExecutor, as_completed

ENTER_EMAIL, ENTER_SUBJECT, ENTER_BODY = range(3)
CONNECTION_TIMEOUT = 1  # Тайм-аут на подключение к SMTP-серверу в секундах

# Функция для загрузки SMTP аккаунтов из текстового файла
def load_smtp_accounts(filename="smtp_accounts.txt"):
    smtp_accounts = []
    with open(filename, "r") as file:
        for line in file:
            try:
                server, port, user, password = line.strip().split('|')
                smtp_accounts.append({
                    "server": server.strip(),
                    "port": int(port.strip()),
                    "user": user.strip(),
                    "password": password.strip()
                })
            except ValueError:
                print(f"Строка с неверным форматом пропущена: {line.strip()}")
    return smtp_accounts

# Функция для сохранения рабочих SMTP аккаунтов обратно в файл
def save_working_smtp_accounts(working_accounts, filename="smtp_accounts.txt"):
    with open(filename, "w") as file:
        for account in working_accounts:
            line = f"{account['server']}|{account['port']}|{account['user']}|{account['password']}\n"
            file.write(line)

# Загрузка SMTP аккаунтов из файла
SMTP_ACCOUNTS = load_smtp_accounts()

ALLOWED_USER_IDS = [581553076, 8039420474]

def check_user_access(update: Update) -> bool:
    user_id = update.effective_user.id
    if user_id not in ALLOWED_USER_IDS:
        update.message.reply_text("У вас нет доступа к этому боту.")
        return False
    return True

def start(update: Update, context: CallbackContext) -> int:
    if not check_user_access(update):
        return ConversationHandler.END

    update.message.reply_text("Введите адреса электронной почты получателей (разделите их запятой):")
    return ENTER_EMAIL

def enter_email(update: Update, context: CallbackContext) -> int:
    if not check_user_access(update):
        return ConversationHandler.END

    emails = [email.strip() for email in update.message.text.split(",")]
    context.user_data['emails'] = emails
    update.message.reply_text("Введите тему письма:")
    return ENTER_SUBJECT

def enter_subject(update: Update, context: CallbackContext) -> int:
    if not check_user_access(update):
        return ConversationHandler.END

    context.user_data['subject'] = update.message.text
    update.message.reply_text("Введите текст письма:")
    return ENTER_BODY

# Функция отправки письма с одного SMTP аккаунта
def send_email(account, emails, subject, body):
    try:
        with smtplib.SMTP(account["server"], account["port"], timeout=CONNECTION_TIMEOUT) as server:
            server.starttls()
            server.login(account["user"], account["password"])

            # Создаем сообщение
            message = MIMEMultipart()
            message['From'] = account["user"]
            message['To'] = ', '.join(emails)
            message['Subject'] = subject
            message.attach(MIMEText(body, 'plain', 'utf-8'))

            server.sendmail(account["user"], emails, message.as_string())
            return account, "success"
    except Exception as e:
        return account, f"fail: {e}"

def enter_body(update: Update, context: CallbackContext) -> int:
    if not check_user_access(update):
        return ConversationHandler.END

    body = update.message.text
    emails = context.user_data['emails']
    subject = context.user_data['subject']
    working_accounts = []
    fail_count = 0
    failure_details = []

    # Parallel email sending
    with ThreadPoolExecutor(max_workers=len(SMTP_ACCOUNTS)) as executor:
        futures = [executor.submit(send_email, account, emails, subject, body) for account in SMTP_ACCOUNTS]
        for future in as_completed(futures):
            account, status = future.result()
            if status == "success":
                working_accounts.append(account)
            else:
                failure_details.append(f"Account {account['user']} failed: {status}")
                fail_count += 1

    # Save working accounts
    save_working_smtp_accounts(working_accounts)

    # Summarize response to user
    summary_message = f"Emails successfully sent from {len(working_accounts)} accounts. Errors on {fail_count} accounts."
    if fail_count > 0:
        summary_message += "\n\nDetails:\n" + "\n".join(failure_details)
    
    update.message.reply_text(summary_message)
    return ConversationHandler.END


# Завершение диалога
def cancel(update: Update, context: CallbackContext) -> int:
    if not check_user_access(update):
        return ConversationHandler.END

    update.message.reply_text("Операция отменена.")
    return ConversationHandler.END

def main():
    updater = Updater("7680269520:AAEzQXxh8sjPFJfdqM6-syRpY2A7mal7jf4", request_kwargs={'read_timeout': 20, 'connect_timeout': 20})
    dispatcher = updater.dispatcher

    # Определение диалогового обработчика
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ENTER_EMAIL: [MessageHandler(Filters.text & ~Filters.command, enter_email)],
            ENTER_SUBJECT: [MessageHandler(Filters.text & ~Filters.command, enter_subject)],
            ENTER_BODY: [MessageHandler(Filters.text & ~Filters.command, enter_body)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    dispatcher.add_handler(conv_handler)
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()



File "/usr/local/lib/python3.7/site-packages/telegram/utils/request.py", line 279, in _request_wrapper
    raise BadRequest(message)
telegram.error.BadRequest: Message is too long  исправь это 


