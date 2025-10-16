import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import app, db
from models import Company, User

# تهيئة قاعدة البيانات عند التشغيل
with app.app_context():
    print("🚀 بدء تهيئة قاعدة البيانات...")

    try:
        # إنشاء الجداول
        print("🔧 جاري إنشاء الجداول...")
        db.create_all()
        print("✅ تم إنشاء الجداول بنجاح")

        # التحقق من وجود المستخدم الافتراضي
        user_count = db.session.query(User).count()
        company_count = db.session.query(Company).count()

        print(f"📊 البيانات الحالية: {user_count} مستخدم، {company_count} شركة")

        if user_count == 0:
            print("🆕 إنشاء البيانات الافتراضية...")

            # إنشاء شركة افتراضية
            default_company = Company(
                name="الشركة اليمنية لتكرير السكر",
                code="YSRC001"
            )
            db.session.add(default_company)
            db.session.commit()

            # إنشاء مستخدم افتراضي
            from werkzeug.security import generate_password_hash

            default_user = User(
                fullname="المسؤول العام",
                username="owner",
                email="owner@company.com",
                password_hash=generate_password_hash("123456"),
                is_admin=True,
                role="admin",
                company_id=default_company.id
            )
            db.session.add(default_user)
            db.session.commit()

            print("✅ تم إنشاء البيانات الافتراضية:")
            print("   👤 مستخدم: owner / 123456")
            print("   🏢 شركة: الشركة اليمنية لتكرير السكر")
        else:
            print("✅ توجد بيانات بالفعل")

    except Exception as e:
        print(f"⚠️ خطأ أثناء التهيئة: {e}")

    print("✅ تم تهيئة التطبيق بنجاح")

# هذا هو المتغير الذي يبحث عنه Gunicorn
application = app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)