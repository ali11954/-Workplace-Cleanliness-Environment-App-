import os
from datetime import timedelta


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'cleaning-company-secret-key-2025'

    # ===============================
    # قاعدة البيانات - الإصدار المعدل
    # ===============================
    # الرابط السحابي المباشر - تم إضافته
    CLOUD_DB_URL = 'postgresql://evaluation_db_3th0_user:RylVGtHAlaIWTv63DcOjIMPPn1lJ54kT@dpg-d3ft80u3jp1c73f87ib0-a.frankfurt-postgres.render.com/evaluation_db_3th0'

    DATABASE_URL = os.environ.get('DATABASE_URL') or CLOUD_DB_URL  # استخدم السحابي كافتراضي

    if DATABASE_URL:
        # تنظيف الرابط من المسافات
        DATABASE_URL = DATABASE_URL.strip()

        # إصلاح postgres -> postgresql إذا needed
        if DATABASE_URL.startswith('postgres://'):
            DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

        # إضافة sslmode=require لـ Render
        if 'render.com' in DATABASE_URL and 'sslmode=' not in DATABASE_URL:
            if '?' in DATABASE_URL:
                DATABASE_URL += '&sslmode=require'
            else:
                DATABASE_URL += '?sslmode=require'

        SQLALCHEMY_DATABASE_URI = DATABASE_URL

        # تحديد نوع قاعدة البيانات
        if 'postgresql' in DATABASE_URL:
            print("✅ تم تهيئة رابط قاعدة البيانات السحابية (Production)")
            print(f"🌐 السحابية: {DATABASE_URL.split('@')[1].split('/')[0]}")  # عرض اسم المضيف فقط
        else:
            print("✅ تم تهيئة رابط قاعدة البيانات Production")

    else:
        # قاعدة البيانات المحلية (لل development)
        BASE_DIR = os.path.abspath(os.path.dirname(__file__))
        instance_path = os.path.join(BASE_DIR, 'instance')

        if not os.path.exists(instance_path):
            os.makedirs(instance_path)

        db_full_path = os.path.join(instance_path, 'database.db')
        SQLALCHEMY_DATABASE_URI = f'sqlite:///{db_full_path}'
        print("✅ تم تهيئة قاعدة البيانات المحلية")

    # ===============================
    # خيارات SQLAlchemy
    # ===============================
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # خيارات المحرك
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 300,
        'pool_pre_ping': True,
    }

    # إذا كان PostgreSQL، أضف خيارات SSL
    if 'postgresql' in SQLALCHEMY_DATABASE_URI:
        SQLALCHEMY_ENGINE_OPTIONS['connect_args'] = {
            'connect_timeout': 10,
            'sslmode': 'require',
            'sslrootcert': None
        }
        print("🔒 تم تفعيل خيارات SSL لPostgreSQL")
    else:
        # إذا كان SQLite
        SQLALCHEMY_ENGINE_OPTIONS['connect_args'] = {'check_same_thread': False}
        print("💾 تم تفعيل خيارات SQLite")

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

    # إعدادات إضافية للسحابية
    if 'postgresql' in SQLALCHEMY_DATABASE_URI:
        # تحسينات لأداء PostgreSQL
        SQLALCHEMY_ENGINE_OPTIONS.update({
            'pool_size': 10,
            'max_overflow': 20,
            'pool_timeout': 30,
        })