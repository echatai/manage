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
    conn = psycopg2.connect("postgresql://postgres:qRoPLmVAenZFFyNFjSicmBKMDSIFIqAa@postgres.railway.internal:5432/railway")
    cursor = conn.cursor()
    logger.info("اتصال به دیتابیس برقرار شد.")
except Exception as e:
    logger.error(f"خطا در اتصال به دیتابیس: {e}")
    raise

# بررسی و ایجاد جداول و ستون‌ها در دیتابیس در صورت عدم وجود
def create_tables_if_not_exists():
    try:
        # حذف جداول اگر موجود باشند
        cursor.execute("DROP TABLE IF EXISTS students, teachers, categories CASCADE;")
        conn.commit()
        logger.info("جداول موجود حذف شدند.")

        # ایجاد جدول دانش‌آموزان
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

        # ایجاد جدول معلمان
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

        # ایجاد جدول دسته‌ها
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) UNIQUE NOT NULL
            );
        """)

        # اعمال تغییرات به دیتابیس
        conn.commit()
        logger.info("جداول و ستون‌های مورد نیاز ایجاد شدند.")
    except Exception as e:
        logger.error(f"خطا در ایجاد جداول: {e}")
        conn.rollback()

# مراحل مکالمه
ADMIN_LOGIN, MAIN_MENU, MANAGE_STUDENTS, MANAGE_TEACHERS, MANAGE_CATEGORIES, ADD_CATEGORY, ADD_STUDENT, ADD_TEACHER, EDIT_STUDENT, EDIT_TEACHER, DELETE_STUDENT, DELETE_TEACHER, EDIT_STUDENT_CONFIRM, EDIT_TEACHER_CONFIRM = range(14)

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
    elif text == "حذف دانش‌آموز":
        return await delete_student(update, context)
    elif text == "بازگشت به منوی اصلی":
        return await main_menu(update, context)
    else:
        await update.message.reply_text(
            "گزینه نامعتبر. لطفاً یکی از عملیات زیر را انتخاب کنید:",
            reply_markup=ReplyKeyboardMarkup(STUDENT_MENU_KEYBOARD, one_time_keyboard=True)
        )
        return MANAGE_STUDENTS

# حذف دانش‌آموز
async def delete_student(update: Update, context: CallbackContext):
    cursor.execute("SELECT id, first_name, last_name FROM students")
    students = cursor.fetchall()
    if not students:
        await update.message.reply_text("هیچ دانش‌آموزی برای حذف وجود ندارد.")
        return MANAGE_STUDENTS
    
    student_list = "\n".join([f"{student[0]}: {student[1]} {student[2]}" for student in students])
    await update.message.reply_text(f"لیست دانش‌آموزان:\n{student_list}\n\nلطفاً شناسه دانش‌آموز مورد نظر را وارد کنید:")
    return DELETE_STUDENT

async def confirm_delete_student(update: Update, context: CallbackContext):
    student_id = update.message.text.strip()
    try:
        cursor.execute("SELECT id FROM students WHERE id = %s", (student_id,))
        student = cursor.fetchone()
        if student:
            cursor.execute("DELETE FROM students WHERE id = %s", (student_id,))
            conn.commit()
            await update.message.reply_text(f"دانش‌آموز با شناسه {student_id} با موفقیت حذف شد!")
        else:
            await update.message.reply_text("شناسه وارد شده معتبر نیست.")
    except Exception as e:
        logger.error(f"خطا در حذف دانش‌آموز: {e}")
        await update.message.reply_text("خطا در حذف دانش‌آموز. لطفاً دوباره تلاش کنید.")
    return MANAGE_STUDENTS

# مدیریت معلمان
async def manage_teachers(update: Update, context: CallbackContext):
    text = update.message.text
    if text == "افزودن معلم":
        await update.message.reply_text("لطفاً اطلاعات معلم (کد ملی:رمز عبور:نام:نام خانوادگی:دسته‌بندی) را وارد کنید:")
        return ADD_TEACHER
    elif text == "حذف معلم":
        return await delete_teacher(update, context)
    elif text == "بازگشت به منوی اصلی":
        return await main_menu(update, context)
    else:
        await update.message.reply_text(
            "گزینه نامعتبر. لطفاً یکی از عملیات زیر را انتخاب کنید:",
            reply_markup=ReplyKeyboardMarkup(TEACHER_MENU_KEYBOARD, one_time_keyboard=True)
        )
        return MANAGE_TEACHERS

# حذف معلم
async def delete_teacher(update: Update, context: CallbackContext):
    cursor.execute("SELECT id, first_name, last_name FROM teachers")
    teachers = cursor.fetchall()
    if not teachers:
        await update.message.reply_text("هیچ معلمی برای حذف وجود ندارد.")
        return MANAGE_TEACHERS
    
    teacher_list = "\n".join([f"{teacher[0]}: {teacher[1]} {teacher[2]}" for teacher in teachers])
    await update.message.reply_text(f"لیست معلمان:\n{teacher_list}\n\nلطفاً شناسه معلم مورد نظر را وارد کنید:")
    return DELETE_TEACHER

async def confirm_delete_teacher(update: Update, context: CallbackContext):
    teacher_id = update.message.text.strip()
    try:
        cursor.execute("SELECT id FROM teachers WHERE id = %s", (teacher_id,))
        teacher = cursor.fetchone()
        if teacher:
            cursor.execute("DELETE FROM teachers WHERE id = %s", (teacher_id,))
            conn.commit()
            await update.message.reply_text(f"معلم با شناسه {teacher_id} با موفقیت حذف شد!")
        else:
            await update.message.reply_text("شناسه وارد شده معتبر نیست.")
    except Exception as e:
        logger.error(f"خطا در حذف معلم: {e}")
        await update.message.reply_text("خطا در حذف معلم. لطفاً دوباره تلاش کنید.")
    return MANAGE_TEACHERS

# افزودن دانش‌آموز
async def add_student(update: Update, context: CallbackContext):
    student_info = update.message.text.strip().split(":")
    if len(student_info) != 4:
        await update.message.reply_text("فرمت ورودی اشتباه است. لطفاً به شکل کد ملی:رمز عبور:نام:نام خانوادگی وارد کنید.")
        return ADD_STUDENT

    national_code, password, first_name, last_name = student_info
    try:
        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        cursor.execute(
            "INSERT INTO students (national_code, password_hash, first_name, last_name) VALUES (%s, %s, %s, %s)",
            (national_code, password_hash, first_name, last_name)
        )
        conn.commit()
        await update.message.reply_text(f"دانش‌آموز '{first_name} {last_name}' با موفقیت اضافه شد!")
    except Exception as e:
        logger.error(f"خطا در افزودن دانش‌آموز: {e}")
        await update.message.reply_text("خطا در افزودن دانش‌آموز. لطفاً دوباره تلاش کنید.")
    return MANAGE_STUDENTS

# افزودن معلم
async def add_teacher(update: Update, context: CallbackContext):
    teacher_info = update.message.text.strip().split(":")
    if len(teacher_info) != 5:
        await update.message.reply_text("فرمت ورودی اشتباه است. لطفاً به شکل کد ملی:رمز عبور:نام:نام خانوادگی:دسته‌بندی وارد کنید.")
        return ADD_TEACHER

    national_code, password, first_name, last_name, category = teacher_info
    try:
        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        cursor.execute(
            "INSERT INTO teachers (national_code, password_hash, first_name, last_name, category) VALUES (%s, %s, %s, %s, %s)",
            (national_code, password_hash, first_name, last_name, category)
        )
        conn.commit()
        await update.message.reply_text(f"معلم '{first_name} {last_name}' با موفقیت اضافه شد!")
    except Exception as e:
        logger.error(f"خطا در افزودن معلم: {e}")
        await update.message.reply_text("خطا در افزودن معلم. لطفاً دوباره تلاش کنید.")
    return MANAGE_TEACHERS

# انجام عملیات ویرایش دانش‌آموز و معلم
async def edit_student(update: Update, context: CallbackContext):
    cursor.execute("SELECT id, first_name, last_name FROM students")
    students = cursor.fetchall()
    if not students:
        await update.message.reply_text("هیچ دانش‌آموزی برای ویرایش وجود ندارد.")
        return MANAGE_STUDENTS
    
    student_list = "\n".join([f"{student[0]}: {student[1]} {student[2]}" for student in students])
    await update.message.reply_text(f"لیست دانش‌آموزان:\n{student_list}\n\nلطفاً شناسه دانش‌آموز مورد نظر را وارد کنید:")
    return EDIT_STUDENT

async def confirm_edit_student(update: Update, context: CallbackContext):
    student_id = update.message.text.strip()
    try:
        cursor.execute("SELECT * FROM students WHERE id = %s", (student_id,))
        student = cursor.fetchone()
        if student:
            context.user_data['student_id'] = student_id
            await update.message.reply_text(f"لطفاً اطلاعات جدید دانش‌آموز (کد ملی:رمز عبور:نام:نام خانوادگی) را وارد کنید:")
            return EDIT_STUDENT_CONFIRM
        else:
            await update.message.reply_text("شناسه وارد شده معتبر نیست.")
    except Exception as e:
        logger.error(f"خطا در ویرایش دانش‌آموز: {e}")
        await update.message.reply_text("خطا در ویرایش دانش‌آموز. لطفاً دوباره تلاش کنید.")
    return MANAGE_STUDENTS

# ویرایش معلم
async def edit_teacher(update: Update, context: CallbackContext):
    cursor.execute("SELECT id, first_name, last_name FROM teachers")
    teachers = cursor.fetchall()
    if not teachers:
        await update.message.reply_text("هیچ معلمی برای ویرایش وجود ندارد.")
        return MANAGE_TEACHERS
    
    teacher_list = "\n".join([f"{teacher[0]}: {teacher[1]} {teacher[2]}" for teacher in teachers])
    await update.message.reply_text(f"لیست معلمان:\n{teacher_list}\n\nلطفاً شناسه معلم مورد نظر را وارد کنید:")
    return EDIT_TEACHER

async def confirm_edit_teacher(update: Update, context: CallbackContext):
    teacher_id = update.message.text.strip()
    try:
        cursor.execute("SELECT * FROM teachers WHERE id = %s", (teacher_id,))
        teacher = cursor.fetchone()
        if teacher:
            context.user_data['teacher_id'] = teacher_id
            await update.message.reply_text(f"لطفاً اطلاعات جدید معلم (کد ملی:رمز عبور:نام:نام خانوادگی:دسته‌بندی) را وارد کنید:")
            return EDIT_TEACHER_CONFIRM
        else:
            await update.message.reply_text("شناسه وارد شده معتبر نیست.")
    except Exception as e:
        logger.error(f"خطا در ویرایش معلم: {e}")
        await update.message.reply_text("خطا در ویرایش معلم. لطفاً دوباره تلاش کنید.")
    return MANAGE_TEACHERS

# آغاز ربات
if __name__ == "__main__":
    create_tables_if_not_exists()

    application = ApplicationBuilder().token("8097014995:AAFdMtovZfyW0YkbycFXS_SVssBG5pRtsk4").build()

    # تنظیمات handler‌ها
    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ADMIN_LOGIN: [MessageHandler(filters.TEXT, admin_login)],
            MAIN_MENU: [MessageHandler(filters.TEXT, main_menu)],
            MANAGE_STUDENTS: [MessageHandler(filters.TEXT, manage_students)],
            MANAGE_TEACHERS: [MessageHandler(filters.TEXT, manage_teachers)],
            MANAGE_CATEGORIES: [MessageHandler(filters.TEXT, manage_categories)],
            ADD_CATEGORY: [MessageHandler(filters.TEXT, add_category)],
            ADD_STUDENT: [MessageHandler(filters.TEXT, add_student)],
            ADD_TEACHER: [MessageHandler(filters.TEXT, add_teacher)],
            DELETE_STUDENT: [MessageHandler(filters.TEXT, confirm_delete_student)],
            DELETE_TEACHER: [MessageHandler(filters.TEXT, confirm_delete_teacher)],
            EDIT_STUDENT: [MessageHandler(filters.TEXT, edit_student)],
            EDIT_TEACHER: [MessageHandler(filters.TEXT, edit_teacher)],
            EDIT_STUDENT_CONFIRM: [MessageHandler(filters.TEXT, confirm_edit_student)],
            EDIT_TEACHER_CONFIRM: [MessageHandler(filters.TEXT, confirm_edit_teacher)],
        },
        fallbacks=[],
    )

    application.add_handler(conversation_handler)
    application.run_polling()
