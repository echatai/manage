from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackContext, ConversationHandler, filters
import psycopg2
import bcrypt

# اتصال به دیتابیس
conn = psycopg2.connect("postgresql://postgres:WwsdWwGXSFWbTbcyRvSchqpltUXOCTVZ@postgres.railway.internal:5432/railway")
cursor = conn.cursor()

# مراحل مکالمه
ADMIN_LOGIN, MAIN_MENU, MANAGE_STUDENTS, MANAGE_TEACHERS, MANAGE_CATEGORIES = range(5)

# اطلاعات ادمین
ADMIN_CREDENTIALS = {
    "username": "admin",
    "password": bcrypt.hashpw("Mr123456".encode(), bcrypt.gensalt()).decode()
}

# منوی اصلی
MAIN_MENU_KEYBOARD = [
    ["مدیریت دانش‌آموزان", "مدیریت معلمان"],
    ["مدیریت دسته‌ها", "خروج"]
]

# شروع ربات
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "لطفاً نام کاربری و رمز عبور ادمین را به صورت زیر وارد کنید:\n\nنام کاربری:رمز عبور"
    )
    return ADMIN_LOGIN

# ورود ادمین
async def admin_login(update: Update, context: CallbackContext):
    try:
        username, password = update.message.text.split(":")
        if username == ADMIN_CREDENTIALS["username"] and bcrypt.checkpw(password.encode(), ADMIN_CREDENTIALS["password"].encode()):
            await update.message.reply_text(
                "ورود موفقیت‌آمیز بود! لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
                reply_markup=ReplyKeyboardMarkup(MAIN_MENU_KEYBOARD, one_time_keyboard=True)
            )
            return MAIN_MENU
        else:
            await update.message.reply_text("نام کاربری یا رمز عبور اشتباه است. لطفاً دوباره تلاش کنید.")
    except ValueError:
        await update.message.reply_text("فرمت ورودی اشتباه است. لطفاً به شکل نام کاربری:رمز عبور وارد کنید.")
    return ADMIN_LOGIN

# منوی اصلی
async def main_menu(update: Update, context: CallbackContext):
    text = update.message.text
    if text == "مدیریت دانش‌آموزان":
        return await manage_students_menu(update, context)
    elif text == "مدیریت معلمان":
        return await manage_teachers_menu(update, context)
    elif text == "مدیریت دسته‌ها":
        return await manage_categories_menu(update, context)
    elif text == "خروج":
        await update.message.reply_text("خداحافظ!")
        return ConversationHandler.END
    else:
        await update.message.reply_text(
            "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
            reply_markup=ReplyKeyboardMarkup(MAIN_MENU_KEYBOARD, one_time_keyboard=True)
        )
        return MAIN_MENU

# مدیریت دانش‌آموزان
async def manage_students_menu(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "لطفاً یکی از عملیات زیر را انتخاب کنید:",
        reply_markup=ReplyKeyboardMarkup([
            ["افزودن دانش‌آموز", "ویرایش دانش‌آموز"],
            ["حذف دانش‌آموز", "بازگشت به منوی اصلی"]
        ], one_time_keyboard=True)
    )
    return MANAGE_STUDENTS

async def manage_students(update: Update, context: CallbackContext):
    text = update.message.text
    if text == "افزودن دانش‌آموز":
        await update.message.reply_text("لطفاً اطلاعات دانش‌آموز را به شکل زیر وارد کنید:\n\nکد ملی:رمز عبور")
    elif text == "ویرایش دانش‌آموز":
        await update.message.reply_text("لطفاً کد ملی دانش‌آموزی که می‌خواهید ویرایش کنید را وارد کنید:")
    elif text == "حذف دانش‌آموز":
        await update.message.reply_text("لطفاً کد ملی دانش‌آموزی که می‌خواهید حذف کنید را وارد کنید:")
    elif text == "بازگشت به منوی اصلی":
        return await main_menu(update, context)
    return MANAGE_STUDENTS

# مدیریت معلمان
async def manage_teachers_menu(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "لطفاً یکی از عملیات زیر را انتخاب کنید:",
        reply_markup=ReplyKeyboardMarkup([
            ["افزودن معلم", "ویرایش معلم"],
            ["حذف معلم", "بازگشت به منوی اصلی"]
        ], one_time_keyboard=True)
    )
    return MANAGE_TEACHERS

async def manage_teachers(update: Update, context: CallbackContext):
    text = update.message.text
    if text == "افزودن معلم":
        await update.message.reply_text("لطفاً اطلاعات معلم را به شکل زیر وارد کنید:\n\nکد ملی:رمز عبور:دسته‌بندی")
    elif text == "ویرایش معلم":
        await update.message.reply_text("لطفاً کد ملی معلمی که می‌خواهید ویرایش کنید را وارد کنید:")
    elif text == "حذف معلم":
        await update.message.reply_text("لطفاً کد ملی معلمی که می‌خواهید حذف کنید را وارد کنید:")
    elif text == "بازگشت به منوی اصلی":
        return await main_menu(update, context)
    return MANAGE_TEACHERS

# مدیریت دسته‌ها
async def manage_categories_menu(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "لطفاً یکی از عملیات زیر را انتخاب کنید:",
        reply_markup=ReplyKeyboardMarkup([
            ["افزودن دسته", "ویرایش دسته"],
            ["حذف دسته", "بازگشت به منوی اصلی"]
        ], one_time_keyboard=True)
    )
    return MANAGE_CATEGORIES

async def manage_categories(update: Update, context: CallbackContext):
    text = update.message.text
    if text == "افزودن دسته":
        await update.message.reply_text("لطفاً نام دسته‌ای که می‌خواهید اضافه کنید را وارد کنید:")
    elif text == "ویرایش دسته":
        await update.message.reply_text("لطفاً نام دسته‌ای که می‌خواهید ویرایش کنید را وارد کنید:")
    elif text == "حذف دسته":
        await update.message.reply_text("لطفاً نام دسته‌ای که می‌خواهید حذف کنید را وارد کنید:")
    elif text == "بازگشت به منوی اصلی":
        return await main_menu(update, context)
    return MANAGE_CATEGORIES

# مسیر مکالمه
conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        ADMIN_LOGIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_login)],
        MAIN_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, main_menu)],
        MANAGE_STUDENTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, manage_students)],
        MANAGE_TEACHERS: [MessageHandler(filters.TEXT & ~filters.COMMAND, manage_teachers)],
        MANAGE_CATEGORIES: [MessageHandler(filters.TEXT & ~filters.COMMAND, manage_categories)],
    },
    fallbacks=[CommandHandler("start", start)]
)

# اجرای ربات
app = ApplicationBuilder().token("8097014995:AAFdMtovZfyW0YkbycFXS_SVssBG5pRtsk4").build()
app.add_handler(conv_handler)
app.run_polling()
