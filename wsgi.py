import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import app, db
from models import User, Company, Location, Site, Place, Criterion, Evaluation, EvaluationDetail, EvaluationAuthority

# تهيئة قاعدة البيانات عند التشغيل
with app.app_context():
    print("🚀 بدء تهيئة قاعدة البيانات الشاملة...")

    try:
        # أولاً: إنشاء جميع الجداول
        print("🔧 جاري إنشاء جميع الجداول...")
        db.create_all()
        print("✅ تم إنشاء الجداول الأساسية")

        # ثانياً: إضافة جميع الأعمدة المفقودة
        print("📝 جاري إضافة الأعمدة المفقودة...")
        with db.engine.connect() as conn:
            # قائمة بجميع أوامر SQL لإضافة الأعمدة المفقودة
            sql_commands = [
                # جدول companies
                "ALTER TABLE companies ADD COLUMN IF NOT EXISTS code VARCHAR(50)",
                "ALTER TABLE companies ADD COLUMN IF NOT EXISTS active BOOLEAN DEFAULT true",
                "ALTER TABLE companies ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",

                # جدول user
                "ALTER TABLE user ADD COLUMN IF NOT EXISTS fullname VARCHAR(150)",
                "ALTER TABLE user ADD COLUMN IF NOT EXISTS email VARCHAR(120)",
                "ALTER TABLE user ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT false",
                "ALTER TABLE user ADD COLUMN IF NOT EXISTS role VARCHAR(50)",
                "ALTER TABLE user ADD COLUMN IF NOT EXISTS active BOOLEAN DEFAULT true",
                "ALTER TABLE user ADD COLUMN IF NOT EXISTS company_id INTEGER",
                "ALTER TABLE user ADD COLUMN IF NOT EXISTS region_id INTEGER",

                # جدول location
                "ALTER TABLE location ADD COLUMN IF NOT EXISTS parent_id INTEGER",
                "ALTER TABLE user ADD COLUMN IF NOT EXISTS company_id INTEGER REFERENCES companies(id)",
                "ALTER TABLE location ADD COLUMN IF NOT EXISTS code VARCHAR(50)",
                "ALTER TABLE location ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT true",
                "ALTER TABLE location ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",

                # جدول site
                "ALTER TABLE site ADD COLUMN IF NOT EXISTS region_id INTEGER REFERENCES location(id)",

                # جدول place
                "ALTER TABLE place ADD COLUMN IF NOT EXISTS site_id INTEGER REFERENCES site(id)",

                # جدول criterion
                "ALTER TABLE criterion ADD COLUMN IF NOT EXISTS place_id INTEGER REFERENCES place(id)",
                "ALTER TABLE criterion ADD COLUMN IF NOT EXISTS authority_id INTEGER REFERENCES evaluation_authorities(id)",
                "ALTER TABLE criterion ADD COLUMN IF NOT EXISTS min_score FLOAT",
                "ALTER TABLE criterion ADD COLUMN IF NOT EXISTS max_score FLOAT",

                # جدول evaluation
                "ALTER TABLE evaluation ADD COLUMN IF NOT EXISTS region_id INTEGER REFERENCES location(id)",
                "ALTER TABLE evaluation ADD COLUMN IF NOT EXISTS site_id INTEGER REFERENCES site(id)",
                "ALTER TABLE evaluation ADD COLUMN IF NOT EXISTS place_id INTEGER REFERENCES place(id)",
                "ALTER TABLE evaluation ADD COLUMN IF NOT EXISTS criterion_id INTEGER REFERENCES criterion(id)",
                "ALTER TABLE evaluation ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES user(id)",
                "ALTER TABLE evaluation ADD COLUMN IF NOT EXISTS total_score INTEGER",
                "ALTER TABLE evaluation ADD COLUMN IF NOT EXISTS percent FLOAT",
                "ALTER TABLE evaluation ADD COLUMN IF NOT EXISTS notes TEXT",
                "ALTER TABLE evaluation ADD COLUMN IF NOT EXISTS date TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                "ALTER TABLE evaluation ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'draft'",
                "ALTER TABLE evaluation ADD COLUMN IF NOT EXISTS submitted_at TIMESTAMP",
                "ALTER TABLE evaluation ADD COLUMN IF NOT EXISTS approved_by INTEGER REFERENCES user(id)",
                "ALTER TABLE evaluation ADD COLUMN IF NOT EXISTS approved_at TIMESTAMP",
                "ALTER TABLE evaluation ADD COLUMN IF NOT EXISTS created_by_id INTEGER REFERENCES user(id)",
                "ALTER TABLE evaluation ADD COLUMN IF NOT EXISTS updated_by_id INTEGER REFERENCES user(id)",

                # جدول evaluation_detail
                "ALTER TABLE evaluation_detail ADD COLUMN IF NOT EXISTS evaluation_id INTEGER REFERENCES evaluation(id)",
                "ALTER TABLE evaluation_detail ADD COLUMN IF NOT EXISTS criterion_id INTEGER REFERENCES criterion(id)",
                "ALTER TABLE evaluation_detail ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES user(id)",
                "ALTER TABLE evaluation_detail ADD COLUMN IF NOT EXISTS score FLOAT",
                "ALTER TABLE evaluation_detail ADD COLUMN IF NOT EXISTS timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                "ALTER TABLE evaluation_detail ADD COLUMN IF NOT EXISTS authority_id INTEGER REFERENCES evaluation_authorities(id)",
                "ALTER TABLE evaluation_detail ADD COLUMN IF NOT EXISTS place_id INTEGER REFERENCES place(id)",
                "ALTER TABLE evaluation_detail ADD COLUMN IF NOT EXISTS company_id INTEGER REFERENCES companies(id)",
                "ALTER TABLE evaluation_detail ADD COLUMN IF NOT EXISTS note TEXT",

                # جدول evaluation_authorities
                "ALTER TABLE evaluation_authorities ADD COLUMN IF NOT EXISTS name VARCHAR(100)",
                "ALTER TABLE evaluation_authorities ADD COLUMN IF NOT EXISTS company_id INTEGER REFERENCES companies(id)",

                # جدول permissions
                "ALTER TABLE permissions ADD COLUMN IF NOT EXISTS name VARCHAR(100)",
                "ALTER TABLE permissions ADD COLUMN IF NOT EXISTS code VARCHAR(50)",
                "ALTER TABLE permissions ADD COLUMN IF NOT EXISTS description TEXT",
                "ALTER TABLE permissions ADD COLUMN IF NOT EXISTS category VARCHAR(50)",
                "ALTER TABLE permissions ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",

                # جدول user_permissions
                "ALTER TABLE user_permissions ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES user(id)",
                "ALTER TABLE user_permissions ADD COLUMN IF NOT EXISTS permission_code VARCHAR(50)",
                "ALTER TABLE user_permissions ADD COLUMN IF NOT EXISTS granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",

                # جدول action_plan
                "ALTER TABLE action_plan ADD COLUMN IF NOT EXISTS note TEXT",
                "ALTER TABLE action_plan ADD COLUMN IF NOT EXISTS plan_text TEXT",
                "ALTER TABLE action_plan ADD COLUMN IF NOT EXISTS action_plan TEXT",
                "ALTER TABLE action_plan ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                "ALTER TABLE action_plan ADD COLUMN IF NOT EXISTS closed BOOLEAN DEFAULT false",
                "ALTER TABLE action_plan ADD COLUMN IF NOT EXISTS closed_date TIMESTAMP",
                "ALTER TABLE action_plan ADD COLUMN IF NOT EXISTS improvement_score FLOAT",
                "ALTER TABLE action_plan ADD COLUMN IF NOT EXISTS evaluation_detail_id INTEGER REFERENCES evaluation_detail(id)",
                "ALTER TABLE action_plan ADD COLUMN IF NOT EXISTS location_id INTEGER REFERENCES location(id)",
                "ALTER TABLE action_plan ADD COLUMN IF NOT EXISTS site_id INTEGER REFERENCES site(id)",
                "ALTER TABLE action_plan ADD COLUMN IF NOT EXISTS place_id INTEGER REFERENCES place(id)",
                "ALTER TABLE action_plan ADD COLUMN IF NOT EXISTS criterion_id INTEGER REFERENCES criterion(id)",

                # جدول audit_logs
                "ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES user(id)",
                "ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS action VARCHAR(100)",
                "ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS table_name VARCHAR(100)",
                "ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS record_id INTEGER",
                "ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS old_values TEXT",
                "ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS new_values TEXT",
                "ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS ip_address VARCHAR(45)",
                "ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS user_agent TEXT",
                "ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",

                # جدول notifications
                "ALTER TABLE notifications ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES user(id)",
                "ALTER TABLE notifications ADD COLUMN IF NOT EXISTS title VARCHAR(200)",
                "ALTER TABLE notifications ADD COLUMN IF NOT EXISTS message TEXT",
                "ALTER TABLE notifications ADD COLUMN IF NOT EXISTS is_read BOOLEAN DEFAULT false",
                "ALTER TABLE notifications ADD COLUMN IF NOT EXISTS notification_type VARCHAR(50)",
                "ALTER TABLE notifications ADD COLUMN IF NOT EXISTS related_url VARCHAR(500)",
                "ALTER TABLE notifications ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
            ]

            for sql in sql_commands:
                try:
                    conn.execute(db.text(sql))
                    print(
                        f"✅ {sql.split('ADD COLUMN IF NOT EXISTS')[1].split(' ')[0] if 'ADD COLUMN' in sql else 'تم تنفيذ الأمر'}")
                except Exception as e:
                    print(f"⚠️ خطأ في: {sql[:50]}... - {e}")

            conn.commit()

        print("✅ تم إضافة جميع الأعمدة المفقودة")

        # ثالثاً: إنشاء البيانات الافتراضية
        print("📦 جاري إنشاء البيانات الافتراضية...")
        user_count = db.session.query(User).count()
        company_count = db.session.query(Company).count()

        if user_count == 0:
            print("🆕 إنشاء البيانات الافتراضية...")

            # إنشاء شركة افتراضية
            company = Company(
                name="الشركة اليمنية لتكرير السكر",
                code="YSRC001",
                active=True
            )
            db.session.add(company)
            db.session.commit()

            # إنشاء مستخدم افتراضي
            from werkzeug.security import generate_password_hash

            user = User(
                fullname="المسؤول العام",
                username="owner",
                email="owner@company.com",
                password_hash=generate_password_hash("123456"),
                is_admin=True,
                role="admin",
                active=True,
                company_id=company.id
            )
            db.session.add(user)
            db.session.commit()

            print("✅ تم إنشاء البيانات الافتراضية:")
            print("   👤 مستخدم: owner / 123456")
            print("   🏢 شركة: الشركة اليمنية لتكرير السكر")
        else:
            print(f"✅ توجد بيانات بالفعل: {user_count} مستخدم، {company_count} شركة")

    except Exception as e:
        print(f"❌ خطأ أثناء التهيئة: {e}")

    print("🎉 تم تهيئة قاعدة البيانات بنجاح!")

application = app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)