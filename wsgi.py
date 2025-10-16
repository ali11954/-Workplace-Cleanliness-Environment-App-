import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import app, db
from models import Company, User

# تهيئة قاعدة البيانات عند التشغيل
with app.app_context():
    print("🚀 بدء تهيئة قاعدة البيانات...")

    try:
        # 1. إضافة العمود أولاً (سيتم تجاهله إذا كان موجوداً)
        with db.engine.connect() as conn:
            conn.execute(db.text("ALTER TABLE companies ADD COLUMN IF NOT EXISTS code VARCHAR(50)"))
            conn.commit()
        print("✅ تم التأكد من وجود عمود code")

        # 2. إنشاء الجداول
        print("🔧 جاري إنشاء الجداول...")
        db.create_all()
        print("✅ تم إنشاء الجداول بنجاح")

        # 3. التحقق من البيانات
        user_count = db.session.query(User).count()
        print(f"📊 عدد المستخدمين: {user_count}")

        if user_count == 0:
            print("🆕 إنشاء المستخدم الافتراضي...")

            # إنشاء شركة افتراضية
            company = Company(name="الشركة اليمنية لتكرير السكر", code="YSRC001")
            db.session.add(company)
            db.session.commit()

            # إنشاء مستخدم افتراضي
            from werkzeug.security import generate_password_hash

            user = User(
                username="owner",
                password_hash=generate_password_hash("123456"),
                is_admin=True,
                role="admin",
                company_id=company.id
            )
            db.session.add(user)
            db.session.commit()
            print("✅ تم إنشاء: owner / 123456")

    except Exception as e:
        print(f"⚠️ خطأ: {e}")

    print("✅ تم التهيئة")

application = app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)