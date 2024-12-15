from flask import Flask, render_template, request, redirect, url_for, flash
import psycopg2
import bcrypt

app = Flask(__name__)
app.secret_key = "Aa123456"  # برای flash messages
app.config["SESSION_COOKIE_NAME"] = "eshagh"

# اتصال به دیتابیس
conn = psycopg2.connect("postgresql://postgres:WwsdWwGXSFWbTbcyRvSchqpltUXOCTVZ@postgres.railway.internal:5432/railway")
cursor = conn.cursor()

# ایجاد جداول
def create_tables():
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS teachers (
        id SERIAL PRIMARY KEY,
        national_code TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        telegram_username TEXT UNIQUE,
        category TEXT NOT NULL,
        first_name TEXT,
        last_name TEXT
    );
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS students (
        id SERIAL PRIMARY KEY,
        national_code TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        telegram_id TEXT UNIQUE
    );
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS categories (
        id SERIAL PRIMARY KEY,
        name TEXT UNIQUE NOT NULL
    );
    """)
    conn.commit()

create_tables()

# صفحه اصلی (فرم ورود)
@app.route('/')
def index():
    return render_template('index.html')

# فرم برای اضافه کردن معلم
@app.route('/add_teacher', methods=['GET', 'POST'])
def add_teacher():
    if request.method == 'POST':
        national_code = request.form['national_code']
        password = request.form['password']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        category = request.form['category']
        
        # رمزنگاری رمز عبور
        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

        # ذخیره داده‌ها در دیتابیس
        try:
            cursor.execute("INSERT INTO teachers (national_code, password_hash, first_name, last_name, category) VALUES (%s, %s, %s, %s, %s)",
                           (national_code, password_hash, first_name, last_name, category))
            conn.commit()
            flash("معلم با موفقیت اضافه شد!", "success")
        except Exception as e:
            conn.rollback()
            flash("خطا در اضافه کردن معلم!", "danger")

        return redirect(url_for('index'))

    return render_template('add_teacher.html')

# فرم برای اضافه کردن دانش‌آموز
@app.route('/add_student', methods=['GET', 'POST'])
def add_student():
    if request.method == 'POST':
        national_code = request.form['national_code']
        password = request.form['password']
        
        # رمزنگاری رمز عبور
        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

        # ذخیره داده‌ها در دیتابیس
        try:
            cursor.execute("INSERT INTO students (national_code, password_hash) VALUES (%s, %s)",
                           (national_code, password_hash))
            conn.commit()
            flash("دانش‌آموز با موفقیت اضافه شد!", "success")
        except Exception as e:
            conn.rollback()
            flash("خطا در اضافه کردن دانش‌آموز!", "danger")

        return redirect(url_for('index'))

    return render_template('add_student.html')

# فرم برای اضافه کردن دسته معلم‌ها
@app.route('/add_category', methods=['GET', 'POST'])
def add_category():
    if request.method == 'POST':
        category_name = request.form['category_name']
        
        # ذخیره داده‌ها در دیتابیس
        try:
            cursor.execute("INSERT INTO categories (name) VALUES (%s)", (category_name,))
            conn.commit()
            flash("دسته با موفقیت اضافه شد!", "success")
        except Exception as e:
            conn.rollback()
            flash("خطا در اضافه کردن دسته!", "danger")

        return redirect(url_for('index'))

    return render_template('add_category.html')

if __name__ == "__main__":
     app.run(host='0.0.0.0', port=5000)  # می‌توانید پورتی که می‌خواهید را انتخاب کنید
