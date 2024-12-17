import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackContext, ConversationHandler, filters
import psycopg2
import bcrypt

# تنظیمات لاگ‌گیری
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# اتصال به دیتابیس
try:
    conn = psycopg2.connect("postgresql://postgres:WwsdWwGXSFWbTbcyRvSchqpltUXOCTVZ@postgres.railway.internal:5432/railway")
    cursor = conn.cursor()
    logger.info("اتصال به دیتابیس برقرار شد.")
except Exception as e:
    logger.error(f"خطا در اتصال به دیتابیس: {e}")
    raise

# مراحل مکالمه
ADMIN_LOGIN, MAIN_MENU, MANAGE_STUDENTS, MANAGE_TEACHERS, MANAGE_CATEGORIES, ADD_CATEGORY, ADD_STUDENT, ADD_TEACHER = range(8)

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

CATEGORY_MENU_KEYBOARD = [
    ["افزودن دسته", "ویرایش دسته"],
    ["حذف دسته", "بازگشت به منوی اصلی"]
]

STUDENT_MENU_KEYBOARD = [
    ["افزودن دانش‌آموز", "ویرایش دانش‌آموز"],
    ["حذف دانش‌آموز", "بازگشت به منوی اصلی"]
]

TEACHER_MENU_KEYBOARD = [
    ["افزودن معلم", "ویرایش معلم"],
    ["حذف معلم", "بازگشت به منوی اصلی"]
]

# شروع ربات
async def start(update: Update, context: CallbackContext):
    logger.info(f"کاربر {update.effective_user.id} /start را اجرا کرد.")
    await update.message.reply_text(
        "لطفاً نام کاربری و رمز عبور ادمین را به صورت زیر وارد کنید:\n\nنام کاربری:رمز عبور"
    )
    return ADMIN_LOGIN

# ورود ادمین
async def admin_login(update: Update, context: CallbackContext):
    try:
        username, password = update.message.text.split(":")
        if username == ADMIN_CREDENTIALS["username"] and bcrypt.checkpw(password.encode(), ADMIN_CREDENTIALS["password"].encode()):
            logger.info(f"ورود موفق برای کاربر {update.effective_user.id}.")
            await update.message.reply_text(
                "ورود موفقیت‌آمیز بود! لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
                reply_markup=ReplyKeyboardMarkup(MAIN_MENU_KEYBOARD, one_time_keyboard=True)
            )
            return MAIN_MENU
        else:
            await update.message.reply_text("نام کاربری یا رمز عبور اشتباه است. لطفاً دوباره تلاش کنید.")
    except ValueError as e:
        logger.error(f"خطای فرمت ورودی: {e}")
        await update.message.reply_text("فرمت ورودی اشتباه است. لطفاً به شکل نام کاربری:رمز عبور وارد کنید.")
    return ADMIN_LOGIN

# منوی اصلی
async def main_menu(update: Update, context: CallbackContext):
    text = update.message.text
    if text == "مدیریت دانش‌آموزان":
        await update.message.reply_text(
            "لطفاً یکی از عملیات زیر را انتخاب کنید:",
            reply_markup=ReplyKeyboardMarkup(STUDENT_MENU_KEYBOARD, one_time_keyboard=True)
        )
        return MANAGE_STUDENTS
    elif text == "مدیریت معلمان":
        await update.message.reply_text(
            "لطفاً یکی از عملیات زیر را انتخاب کنید:",
            reply_markup=ReplyKeyboardMarkup(TEACHER_MENU_KEYBOARD, one_time_keyboard=True)
        )
        return MANAGE_TEACHERS
    elif text == "مدیریت دسته‌ها":
        await update.message.reply_text(
            "لطفاً یکی از عملیات زیر را انتخاب کنید:",
            reply_markup=ReplyKeyboardMarkup(CATEGORY_MENU_KEYBOARD, one_time_keyboard=True)
        )
        return MANAGE_CATEGORIES
    elif text == "خروج":
        await update.message.reply_text("خداحافظ!")
        return ConversationHandler.END
    else:
        await update.message.reply_text(
            "گزینه نامعتبر. لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
            reply_markup=ReplyKeyboardMarkup(MAIN_MENU_KEYBOARD, one_time_keyboard=True)
        )
        return MAIN_MENU

# مدیریت دسته‌ها
async def manage_categories(update: Update, context: CallbackContext):
    text = update.message.text
    if text == "افزودن دسته":
        await update.message.reply_text("لطفاً نام دسته‌ای که می‌خواهید اضافه کنید را وارد کنید:")
        return ADD_CATEGORY
    elif text == "بازگشت به منوی اصلی":
        return await main_menu(update, context)
    else:
        await update.message.reply_text(
            "گزینه نامعتبر. لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
            reply_markup=ReplyKeyboardMarkup(CATEGORY_MENU_KEYBOARD, one_time_keyboard=True)
        )
        return MANAGE_CATEGORIES

async def add_category(update: Update, context: CallbackContext):
    category_name = update.message.text.strip()
    if not category_name:
        await update.message.reply_text("نام دسته نمی‌تواند خالی باشد. لطفاً دوباره وارد کنید:")
        return ADD_CATEGORY
    try:
        cursor.execute("INSERT INTO categories (name) VALUES (%s)", (category_name,))
        conn.commit()
        await update.message.reply_text(
            f"دسته '{category_name}' با موفقیت اضافه شد!",
            reply_markup=ReplyKeyboardMarkup(CATEGORY_MENU_KEYBOARD, one_time_keyboard=True)
        )
        return MANAGE_CATEGORIES
    except Exception as e:
        logger.error(f"خطا در افزودن دسته: {e}")
        await update.message.reply_text("خطا در افزودن دسته. لطفاً دوباره تلاش کنید.")
        return ADD_CATEGORY

# مدیریت دانش‌آموزان
async def manage_students(update: Update, context: CallbackContext):
    text = update.message.text
    if text == "افزودن دانش‌آموز":
        await update.message.reply_text("لطفاً اطلاعات دانش‌آموز (کد ملی:رمز عبور) را وارد کنید:")
        return ADD_STUDENT
    elif text == "بازگشت به منوی اصلی":
        return await main_menu(update, context)
    else:
        await update.message.reply_text(
            "گزینه نامعتبر. لطفاً یکی از عملیات زیر را انتخاب کنید:",
            reply_markup=ReplyKeyboardMarkup(STUDENT_MENU_KEYBOARD, one_time_keyboard=True)
        )
        return MANAGE_STUDENTS

# مدیریت معلمان
async def manage_teachers(update: Update, context: CallbackContext):
    text = update.message.text
    if text == "افزودن معلم":
        await update.message.reply_text("لطفاً اطلاعات معلم (کد ملی:رمز عبور:دسته‌بندی) را وارد کنید:")
        return ADD_TEACHER
    elif text == "بازگشت به منوی اصلی":
        return await main_menu(update, context)
    else:
        await update.message.reply_text(
            "گزینه نامعتبر. لطفاً یکی از عملیات زیر را انتخاب کنید:",
            reply_markup=ReplyKeyboardMarkup(TEACHER_MENU_KEYBOARD, one_time_keyboard=True)
        )
        return MANAGE_TEACHERS

# مسیر مکالمه
conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        ADMIN_LOGIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_login)],
        MAIN_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, main_menu)],
        MANAGE_CATEGORIES: [MessageHandler(filters.TEXT & ~filters.COMMAND, manage_categories)],
        ADD_CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_category)],
        MANAGE_STUDENTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, manage_students)],
        MANAGE_TEACHERS: [MessageHandler(filters.TEXT & ~filters.COMMAND, manage_teachers)],
    },
    fallbacks=[CommandHandler("start", start)]
)

# اجرای ربات
app = ApplicationBuilder().token("8097014995:AAFdMtovZfyW0YkbycFXS_SVssBG5pRtsk4").build()
app.add_handler(conv_handler)
app.run_polling()
