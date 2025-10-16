import os
import sys

# إضافة المسار الحالي إلى sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import app, db
from models import Company, User  # استيراد النماذج مباشرة

# تهيئة قاعدة البيانات عند التشغيل
with app.app_context():
    print("🚀 بدء تهيئة التطبيق...")

    try:
        # إضافة العمود مباشرة (سيتم تجاهله إذا كان موجوداً)
        db.engine.execute("ALTER TABLE companies ADD COLUMN IF NOT EXISTS code VARCHAR(50)")
        print("✅ تم التأكد من وجود عمود code")
    except Exception as e:
        print(f"⚠️ ملاحظة: {e}")

    # 1. إنشاء الجداول
    print("🔧 جاري إنشاء الجداول...")
    db.create_all()
    print("✅ تم إنشاء الجداول بنجاح")

    # 2. إنشاء البيانات الافتراضية يدوياً
    print("📦 جاري إنشاء البيانات الافتراضية...")

    # التحقق من وجود بيانات
    user_count = User.query.count()
    company_count = Company.query.count()

    print(f"📊 البيانات الحالية: {user_count} مستخدم، {company_count} شركة")

    if user_count == 0 and company_count == 0:
        print("🆕 لا توجد بيانات، جاري الإنشاء...")

        # إنشاء شركة افتراضية
        default_company = Company(
            name="الشركة اليمنية لتكرير السكر",
            code="YSRC001"  # إضافة كود للشركة
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

        print("    👤 مستخدم: owner / 123456")
        print("    🏢 شركة: الشركة اليمنية لتكرير السكر")
    else:
        print("✅ توجد بيانات بالفعل")

    print("✅ تم تهيئة التطبيق بنجاح")

# هذا هو المتغير الذي يبحث عنه Gunicorn
application = app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)