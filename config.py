import os
from datetime import timedelta


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'cleaning-company-secret-key-2025'

    # ===============================
    # قاعدة البيانات - مع تحديد المسار بالضبط
    # ===============================
    DATABASE_URL = os.environ.get('DATABASE_URL')

    if DATABASE_URL:
        SQLALCHEMY_DATABASE_URI = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
        if 'render.com' in SQLALCHEMY_DATABASE_URI and 'sslmode=' not in SQLALCHEMY_DATABASE_URI:
            SQLALCHEMY_DATABASE_URI += '?sslmode=require'
    else:
        BASE_DIR = os.path.abspath(os.path.dirname(__file__))
        instance_path = os.path.join(BASE_DIR, 'instance')

        # ✅ إنشاء المجلد إذا لم يكن موجوداً
        if not os.path.exists(instance_path):
            os.makedirs(instance_path)
            print(f"✅ تم إنشاء مجلد: {instance_path}")

        # ✅ تحديد المسار بالضبط
        db_full_path = os.path.join(instance_path, 'database.db')
        SQLALCHEMY_DATABASE_URI = f'sqlite:///{db_full_path}'

        # ✅ طباعة المسار للتأكد
        print("=" * 60)
        print("📍 مسار قاعدة البيانات المحلية:")
        print(f"   {db_full_path}")
        print(f"   📁 المجلد موجود: {os.path.exists(instance_path)}")
        print(f"   💾 الملف موجود: {os.path.exists(db_full_path)}")
        if os.path.exists(db_full_path):
            file_size = os.path.getsize(db_full_path)
            print(f"   📊 حجم الملف: {file_size:,} bytes")
        print("=" * 60)

    # ===============================
    # خيارات SQLAlchemy
    # ===============================
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 300,
        'pool_pre_ping': True,
        'connect_args': {'check_same_thread': False} if 'sqlite' in SQLALCHEMY_DATABASE_URI else {}
    }

    # ===============================
    # إعدادات Flask
    # ===============================
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
    SESSION_COOKIE_SECURE = not DEBUG
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    PREFERRED_URL_SCHEME = 'https' if not DEBUG else 'http'
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600