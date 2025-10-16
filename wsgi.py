import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import app, db
from models import User, Company, Location, Site, Place, Criterion, Evaluation, EvaluationDetail, EvaluationAuthority, \
    Permission, UserPermission, ActionPlan, AuditLog, Notification


def check_database_status():
    """فحص حالة قاعدة البيانات"""
    with app.app_context():
        try:
            print("🔍 فحص قاعدة البيانات...")

            # تحقق من الجداول
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"📋 الجداول الموجودة: {tables}")

            # تحقق من البيانات
            user_count = User.query.count()
            company_count = Company.query.count()

            print(f"👥 عدد المستخدمين: {user_count}")
            print(f"🏢 عدد الشركات: {company_count}")

            if user_count > 0:
                users = User.query.all()
                for user in users:
                    print(f"   👤 {user.username} - {user.fullname} - {user.role} - company_id: {user.company_id}")

            return True

        except Exception as e:
            print(f"❌ خطأ في فحص قاعدة البيانات: {e}")
            return False


def create_emergency_user():
    """إنشاء مستخدم طوارئ إذا لم يكن هناك مستخدمين"""
    with app.app_context():
        try:
            user_count = User.query.count()
            company_count = Company.query.count()

            print(f"🚨 فحص الطوارئ: {user_count} مستخدم, {company_count} شركة")

            if user_count == 0:
                print("🚨 لا يوجد مستخدمين - إنشاء مستخدم طوارئ...")

                # التحقق من وجود شركة
                emergency_company = Company.query.filter_by(name='شركة الطوارئ').first()
                if not emergency_company:
                    emergency_company = Company(
                        name='شركة الطوارئ',
                        code='EMERGENCY',
                        active=True
                    )
                    db.session.add(emergency_company)
                    db.session.flush()
                    print("✅ تم إنشاء شركة الطوارئ")

                # إنشاء مستخدم طوارئ
                emergency_user = User(
                    fullname='مدير الطوارئ',
                    username='emergency',
                    email='emergency@system.com',
                    role='admin',
                    company_id=emergency_company.id,
                    active=True,
                    is_admin=True
                )
                emergency_user.set_password('123456')
                db.session.add(emergency_user)

                db.session.commit()
                print("✅ تم إنشاء مستخدم الطوارئ:")
                print("   👤 username: emergency")
                print("   🔑 password: 123456")
                print("   🏢 company: شركة الطوارئ")
            else:
                print(f"✅ يوجد {user_count} مستخدم في النظام - لا حاجة للطوارئ")

        except Exception as e:
            db.session.rollback()
            print(f"❌ خطأ في إنشاء مستخدم الطوارئ: {e}")
            import traceback
            traceback.print_exc()


def initialize_database():
    """تهيئة قاعدة البيانات وإنشاء البيانات الافتراضية"""
    with app.app_context():
        try:
            print("🔄 بدء تهيئة قاعدة البيانات الشاملة...")

            # إنشاء جميع الجداول
            db.create_all()
            print("✅ تم إنشاء الجداول الأساسية")

            # 🔍 فحص الشركات الحالية
            existing_companies = Company.query.all()
            print(f"🔍 عدد الشركات الحالية: {len(existing_companies)}")
            for company in existing_companies:
                print(f"   🏢 {company.id}: {company.name} - active: {company.active}")

            # إنشاء الشركة اليمنية لتكرير السكر إذا لم تكن موجودة
            yemen_sugar_company = Company.query.filter_by(name='الشركة اليمنية لتكرير السكر').first()
            if not yemen_sugar_company:
                print("🆕 إنشاء الشركة اليمنية لتكرير السكر...")
                yemen_sugar_company = Company(
                    name='الشركة اليمنية لتكرير السكر',
                    code='YSRC',
                    description='الشركة اليمنية الرائدة في مجال تكرير وإنتاج السكر',
                    address='الجمهورية اليمنية',
                    phone='+967123456789',
                    email='info@yemen-sugar.com',
                    active=True
                )
                db.session.add(yemen_sugar_company)
                db.session.flush()
                print(f"✅ تم إنشاء الشركة اليمنية لتكرير السكر - ID: {yemen_sugar_company.id}")
            else:
                print(f"✅ الشركة موجودة مسبقاً - ID: {yemen_sugar_company.id}")

            # 🔍 فحص المستخدمين الحاليين
            existing_users = User.query.all()
            print(f"🔍 عدد المستخدمين الحاليين: {len(existing_users)}")
            for user in existing_users:
                print(f"   👤 {user.id}: {user.username} - {user.role} - company: {user.company_id}")

            # إنشاء/تحديث المستخدم admin
            admin_user = User.query.filter_by(username='admin').first()
            if not admin_user:
                print("🆕 إنشاء المستخدم admin...")
                admin_user = User(
                    fullname='المدير العام',
                    username='admin',
                    email='admin@system.com',
                    role='admin',
                    company_id=yemen_sugar_company.id,
                    active=True,
                    is_admin=True
                )
                admin_user.set_password('123456')
                db.session.add(admin_user)
                print("✅ تم إنشاء المستخدم admin")
            else:
                print(f"✅ المستخدم admin موجود مسبقاً - company_id: {admin_user.company_id}")
                # إذا كان admin موجوداً بدون شركة، اربطه بالشركة
                if admin_user.company_id is None:
                    admin_user.company_id = yemen_sugar_company.id
                    print("✅ تم ربط المستخدم admin بالشركة")

            db.session.commit()
            print("🎉 تم إنشاء البيانات الافتراضية بنجاح")

        except Exception as e:
            db.session.rollback()
            print(f"❌ خطأ في تهيئة قاعدة البيانات: {e}")
            import traceback
            traceback.print_exc()


# تهيئة قاعدة البيانات عند التشغيل
print("=" * 60)
print("🚀 بدء تشغيل التطبيق عبر WSGI...")
print("=" * 60)

with app.app_context():
    try:
        # 1. فحص قاعدة البيانات
        print("🔍 فحص حالة قاعدة البيانات...")
        check_database_status()

        # 2. إنشاء مستخدم طوارئ إذا لزم الأمر
        print("🚨 فحص وإنشاء مستخدم طوارئ...")
        create_emergency_user()

        # 3. التهيئة الرئيسية
        print("🔄 تهيئة البيانات الافتراضية...")
        initialize_database()

        print("=" * 60)
        print("🎉 اكتملت التهيئة التلقائية بنجاح!")
        print("=" * 60)

    except Exception as e:
        print("❌ فشل في التهيئة التلقائية!")
        print(f"📄 الخطأ: {e}")
        import traceback

        traceback.print_exc()

application = app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)