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

# بررسی و ایجاد جداول و ستون‌ها در دیتابیس در صورت عدم وجود
def create_tables_if_not_exists():
    # ایجاد جدول دانش‌آموزان در صورت عدم وجود
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id SERIAL PRIMARY KEY,
            national_code VARCHAR(20) UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            first_name VARCHAR(100) NOT NULL,
            last_name VARCHAR(100) NOT NULL,
            telegram_id BIGINT UNIQUE
        );
    """)

    # ایجاد جدول معلمان در صورت عدم وجود
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS teachers (
            id SERIAL PRIMARY KEY,
            national_code VARCHAR(20) UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            first_name VARCHAR(100) NOT NULL,
            last_name VARCHAR(100) NOT NULL,
            category VARCHAR(50) NOT NULL,
            telegram_username VARCHAR(100) UNIQUE NOT NULL
        );
    """)

    # ایجاد جدول دسته‌ها در صورت عدم وجود
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) UNIQUE NOT NULL
        );
    """)

    # اعمال تغییرات به دیتابیس
    conn.commit()
    logger.info("جداول و ستون‌های مورد نیاز ایجاد شدند.")

# فراخوانی تابع برای ایجاد جداول در صورت عدم وجود
create_tables_if_not_exists()

# مراحل مکالمه
ADMIN_LOGIN, MAIN_MENU, MANAGE_STUDENTS, MANAGE_TEACHERS, MANAGE_CATEGORIES, ADD_CATEGORY, ADD_STUDENT, ADD_TEACHER, EDIT_STUDENT, EDIT_TEACHER = range(10)

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
        await update.message.reply_text("لطفاً اطلاعات دانش‌آموز (کد ملی:رمز عبور:نام:نام خانوادگی) را وارد کنید:")
        return ADD_STUDENT
    elif text == "بازگشت به منوی اصلی":
        return await main_menu(update, context)
    else:
        await update.message.reply_text(
            "گزینه نامعتبر. لطفاً یکی از عملیات زیر را انتخاب کنید:",
            reply_markup=ReplyKeyboardMarkup(STUDENT_MENU_KEYBOARD, one_time_keyboard=True)
        )
        return MANAGE_STUDENTS

async def add_student(update: Update, context: CallbackContext):
    try:
        national_code, password, first_name, last_name = update.message.text.split(":")
        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

        cursor.execute("""
            INSERT INTO students (national_code, password_hash, first_name, last_name) 
            VALUES (%s, %s, %s, %s)
        """, (national_code, password_hash, first_name, last_name))
        conn.commit()

        await update.message.reply_text(f"دانش‌آموز {first_name} {last_name} با کد ملی {national_code} اضافه شد!")
        return MANAGE_STUDENTS
    except Exception as e:
        logger.error(f"خطا در افزودن دانش‌آموز: {e}")
        await update.message.reply_text("خطا در افزودن دانش‌آموز. لطفاً دوباره تلاش کنید.")
        return ADD_STUDENT

# مدیریت معلمان
async def manage_teachers(update: Update, context: CallbackContext):
    text = update.message.text
    if text == "افزودن معلم":
        await update.message.reply_text("لطفاً اطلاعات معلم (کد ملی:رمز عبور:نام:نام خانوادگی:دسته‌بندی) را وارد کنید:")
        return ADD_TEACHER
    elif text == "بازگشت به منوی اصلی":
        return await main_menu(update, context)
    else:
        await update.message.reply_text(
            "گزینه نامعتبر. لطفاً یکی از عملیات زیر را انتخاب کنید:",
            reply_markup=ReplyKeyboardMarkup(TEACHER_MENU_KEYBOARD, one_time_keyboard=True)
        )
        return MANAGE_TEACHERS

async def add_teacher(update: Update, context: CallbackContext):
    try:
        national_code, password, first_name, last_name, category = update.message.text.split(":")
        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

        cursor.execute("""
            INSERT INTO teachers (national_code, password_hash, first_name, last_name, category) 
            VALUES (%s, %s, %s, %s, %s)
        """, (national_code, password_hash, first_name, last_name, category))
        conn.commit()

        await update.message.reply_text(f"معلم {first_name} {last_name} با کد ملی {national_code} و دسته '{category}' اضافه شد!")
        return MANAGE_TEACHERS
    except Exception as e:
        logger.error(f"خطا در افزودن معلم: {e}")
        await update.message.reply_text("خطا در افزودن معلم. لطفاً دوباره تلاش کنید.")
        return ADD_TEACHER

# مسیر مکالمه
conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        ADMIN_LOGIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_login)],
        MAIN_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, main_menu)],
        MANAGE_CATEGORIES: [MessageHandler(filters.TEXT & ~filters.COMMAND, manage_categories)],
        ADD_CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_category)],
        MANAGE_STUDENTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, manage_students)],
        ADD_STUDENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_student)],
        MANAGE_TEACHERS: [MessageHandler(filters.TEXT & ~filters.COMMAND, manage_teachers)],
        ADD_TEACHER: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_teacher)],
    },
    fallbacks=[CommandHandler("start", start)]
)

# ساخت اپلیکیشن و افزودن هندلر
application = ApplicationBuilder().token("8097014995:AAFdMtovZfyW0YkbycFXS_SVssBG5pRtsk4").build()
application.add_handler(conv_handler)

# اجرای ربات
if __name__ == "__main__":
    application.run_polling()
