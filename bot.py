import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")
CHANNEL_ID = os.getenv("CHANNEL_ID")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📢 Подати оголошення", callback_data="new_ad")],
        [
            InlineKeyboardButton("💼 Робота", callback_data="job"),
            InlineKeyboardButton("🔧 Послуги", callback_data="services"),
        ],
        [
            InlineKeyboardButton("🛒 Куплю / Продам", callback_data="market"),
            InlineKeyboardButton("🚗 Авто", callback_data="auto"),
        ],
        [
            InlineKeyboardButton("🏠 Нерухомість", callback_data="realty"),
            InlineKeyboardButton("📣 Реклама бізнесу", callback_data="business"),
        ],
    ]

    await update.message.reply_text(
        "👋 Вітаємо у «ЗЛАТОПІЛЬ | СВОЇ»!\n\n"
        "Тут можна знайти роботу, майстра, товар або клієнта.\n\n"
        "Оберіть потрібний розділ:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "new_ad":
        context.user_data["step"] = "category"

        keyboard = [
            [InlineKeyboardButton("💼 Робота", callback_data="cat_job")],
            [InlineKeyboardButton("🔧 Послуги", callback_data="cat_services")],
            [InlineKeyboardButton("🛒 Куплю / Продам", callback_data="cat_market")],
            [InlineKeyboardButton("🚗 Авто", callback_data="cat_auto")],
            [InlineKeyboardButton("🏠 Нерухомість", callback_data="cat_realty")],
            [InlineKeyboardButton("📣 Реклама бізнесу", callback_data="cat_business")],
        ]

        await query.edit_message_text(
            "Оберіть категорію оголошення:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    elif query.data.startswith("cat_"):
        category = query.data.replace("cat_", "")
        context.user_data["category"] = category
        context.user_data["step"] = "text"

        await query.edit_message_text(
            "✍️ Напишіть текст оголошення.\n\n"
            "Наприклад:\n"
            "«Продам диван у хорошому стані. Златопіль. "
            "Ціна 3000 грн.»"
        )


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    step = context.user_data.get("step")

    if step == "text":
        context.user_data["text"] = update.message.text
        context.user_data["step"] = "photo"

        await update.message.reply_text(
            "📸 Тепер надішліть фото оголошення.\n\n"
            "Якщо фото немає — напишіть «без фото»."
        )

    elif step == "photo":
        if update.message.photo:
            photo = update.message.photo[-1].file_id
            context.user_data["photo"] = photo

        elif update.message.text and update.message.text.lower() == "без фото":
            context.user_data["photo"] = None

        else:
            await update.message.reply_text(
                "Будь ласка, надішліть фото або напишіть «без фото»."
            )
            return

        context.user_data["step"] = "contact"

        await update.message.reply_text(
            "📞 Вкажіть контакт для зв'язку:\n\n"
            "Наприклад: +380XXXXXXXXX або @username"
        )

    elif step == "contact":
        context.user_data["contact"] = update.message.text
        context.user_data["step"] = None

        category = context.user_data.get("category", "інше")
        text = context.user_data.get("text", "")
        contact = context.user_data.get("contact", "")
        photo = context.user_data.get("photo")

        admin_text = (
            "🔔 НОВЕ ОГОЛОШЕННЯ\n\n"
            f"📂 Категорія: {category}\n"
            f"📞 Контакт: {contact}\n\n"
            f"📝 {text}"
        )

        if ADMIN_ID:
            try:
                if photo:
                    await context.bot.send_photo(
                        chat_id=ADMIN_ID,
                        photo=photo,
                        caption=admin_text,
                    )
                else:
                    await context.bot.send_message(
                        chat_id=ADMIN_ID,
                        text=admin_text,
                    )
            except Exception as e:
                print(f"Admin notification error: {e}")

        await update.message.reply_text(
            "✅ Дякуємо!\n\n"
            "Оголошення передано адміністратору на модерацію."
        )


def main():
    if not TOKEN:
        raise ValueError("BOT_TOKEN is not set")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(
        MessageHandler(
            filters.TEXT | filters.PHOTO,
            message_handler,
        )
    )

    print("Bot started...")
    app.run_polling()


if __name__ == "__main__":
    main()