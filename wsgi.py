import os
import sys

# إضافة المسار الحالي إلى sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import app, db  # هذا السطر مهم!
from models import Company, User

# تهيئة قاعدة البيانات عند التشغيل
with app.app_context():
    print("🚀 بدء تهيئة التطبيق...")

    try:
        # إضافة العمود - الطريقة الصحيحة لـ SQLAlchemy 2.0
        from sqlalchemy import inspect, text

        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('companies')]

        if 'code' not in columns:
            print("📝 إضافة عمود code إلى جدول companies...")
            with db.engine.connect() as conn:
                conn.execute(text("ALTER TABLE companies ADD COLUMN code VARCHAR(50)"))
                conn.commit()
            print("✅ تم إضافة عمود code بنجاح")
        else:
            print("✅ عمود code موجود بالفعل")

    except Exception as e:
        print(f"⚠️ ملاحظة: {e}")

    # 1. إنشاء الجداول
    print("🔧 جاري إنشاء الجداول...")
    db.create_all()
    print("✅ تم إنشاء الجداول بنجاح")

    # 2. التحقق من البيانات الافتراضية
    print("📦 جاري التحقق من البيانات الافتراضية...")

    try:
        user_count = db.session.query(User).count()
        company_count = db.session.query(Company).count()

        print(f"📊 البيانات الحالية: {user_count} مستخدم، {company_count} شركة")

        if user_count == 0:
            print("🆕 لا توجد بيانات مستخدمين، جاري الإنشاء...")

            # إنشاء شركة افتراضية إذا لم تكن موجودة
            if company_count == 0:
                default_company = Company(
                    name="الشركة اليمنية لتكرير السكر",
                    code="YSRC001"
                )
                db.session.add(default_company)
                db.session.commit()
                company_id = default_company.id
                print("    🏢 شركة: الشركة اليمنية لتكرير السكر")
            else:
                company_id = db.session.query(Company).first().id

            # إنشاء مستخدم افتراضي
            from werkzeug.security import generate_password_hash

            default_user = User(
                fullname="المسؤول العام",
                username="owner",
                email="owner@company.com",
                password_hash=generate_password_hash("123456"),
                is_admin=True,
                role="admin",
                company_id=company_id
            )
            db.session.add(default_user)
            db.session.commit()
            print("    👤 مستخدم: owner / 123456")
        else:
            print("✅ توجد بيانات بالفعل")

    except Exception as e:
        print(f"❌ خطأ في التحقق من البيانات: {e}")
        # المتابعة رغم الخطأ

    print("✅ تم تهيئة التطبيق بنجاح")

# هذا هو المتغير الذي يبحث عنه Gunicorn
application = app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)