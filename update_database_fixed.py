# update_database_fixed.py
import os
import sys
import sqlite3

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import app, db
from models import User, Company, Location, Site, Place, Criterion, EvaluationAuthority
from models import Permission, UserPermission, Evaluation, EvaluationDetail


def update_cloud_database():
    """تحديث قاعدة البيانات السحابية بالبيانات المحلية - الإصدار المصحح"""
    with app.app_context():
        try:
            print("🔄 بدء تحديث قاعدة البيانات السحابية...")
            print("🌐 الهدف: قاعدة البيانات السحابية (PostgreSQL)")

            # إنشاء الجداول
            db.create_all()
            print("✅ تم إنشاء/تأكيد الجداول")

            # مسار قاعدة البيانات المحلية
            local_db_path = r'D:\ghith\NEW\hoesing\DullUselessIntegrationtesting\DullUselessIntegrationtesting\instance\database.db'

            if not os.path.exists(local_db_path):
                print("❌ قاعدة البيانات المحلية غير موجودة")
                return

            print(f"📁 مصدر البيانات: {local_db_path}")

            # الاتصال بالمحلية
            local_conn = sqlite3.connect(local_db_path)
            local_cursor = local_conn.cursor()

            # فحص المحتويات
            print("\n🔍 فحص قاعدة البيانات المحلية...")
            tables_to_check = ['companies', 'user', 'location', 'site', 'place', 'evaluation_authorities', 'criterion']

            for table in tables_to_check:
                try:
                    local_cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = local_cursor.fetchone()[0]
                    print(f"   📊 {table}: {count} سجل")
                except Exception as e:
                    print(f"   ⚠️ {table}: غير موجود - {e}")

            # نسخ البيانات بترتيب صحيح
            print("\n📥 بدء نسخ البيانات...")

            # 1. أولاً: الشركات (لأنها أساسية للعلاقات)
            copy_companies(local_cursor)

            # 2. ثانياً: المناطق (لأنها مرتبطة بالشركات)
            copy_locations(local_cursor)

            # 3. ثالثاً: المستخدمين (مرتبط بالشركات)
            copy_users(local_cursor)

            # 4. باقي الجداول
            copy_sites(local_cursor)
            copy_places(local_cursor)
            copy_evaluation_authorities(local_cursor)
            copy_criteria(local_cursor)

            local_conn.close()

            print(f"\n🎉 اكتمل التحديث!")

            # عرض النتائج النهائية
            print("\n📊 الإحصائيات النهائية:")
            print("=" * 40)
            print(f"🏢 الشركات: {Company.query.count()}")
            print(f"👥 المستخدمين: {User.query.count()}")
            print(f"📍 المناطق: {Location.query.count()}")
            print(f"🏗️ المواقع: {Site.query.count()}")
            print(f"🏠 الأماكن: {Place.query.count()}")
            print(f"🏛️ جهات التقييم: {EvaluationAuthority.query.count()}")
            print(f"📊 المعايير: {Criterion.query.count()}")
            print("=" * 40)

        except Exception as e:
            print(f"❌ خطأ في التحديث: {e}")
            import traceback
            traceback.print_exc()


def copy_companies(local_cursor):
    """نسخ الشركات"""
    print("\n🏢 نسخ الشركات...")
    try:
        local_cursor.execute("SELECT * FROM companies")
        records = local_cursor.fetchall()

        added_count = 0
        for record in records:
            # استخدام الفهرس بدلاً من .get()
            company_id = record[0]
            name = record[1]
            code = record[2] if len(record) > 2 else ''
            active = bool(record[3]) if len(record) > 3 else True

            # التحقق من عدم التكرار
            exists = Company.query.get(company_id)
            if not exists:
                new_company = Company(
                    id=company_id,
                    name=name,
                    code=code,
                    active=active
                )
                db.session.add(new_company)
                added_count += 1
                print(f"   ➕ أضيف: {name}")

        db.session.commit()
        print(f"✅ الشركات: أضيف {added_count} سجل")

    except Exception as e:
        print(f"❌ خطأ في نسخ الشركات: {e}")
        db.session.rollback()


def copy_locations(local_cursor):
    """نسخ المناطق"""
    print("\n📍 نسخ المناطق...")
    try:
        local_cursor.execute("SELECT * FROM location")
        records = local_cursor.fetchall()

        added_count = 0
        for record in records:
            location_id = record[0]
            name = record[1]
            code = record[2] if len(record) > 2 else ''
            is_active = bool(record[3]) if len(record) > 3 else True
            company_id = record[4] if len(record) > 4 else None

            # التحقق من وجود الشركة أولاً
            if company_id and not Company.query.get(company_id):
                print(f"   ⚠️ تخطي المنطقة {name} - الشركة {company_id} غير موجودة")
                continue

            exists = Location.query.get(location_id)
            if not exists:
                new_location = Location(
                    id=location_id,
                    name=name,
                    code=code,
                    is_active=is_active,
                    company_id=company_id
                )
                db.session.add(new_location)
                added_count += 1
                print(f"   ➕ أضيف: {name}")

        db.session.commit()
        print(f"✅ المناطق: أضيف {added_count} سجل")

    except Exception as e:
        print(f"❌ خطأ في نسخ المناطق: {e}")
        db.session.rollback()


def copy_users(local_cursor):
    """نسخ المستخدمين"""
    print("\n👥 نسخ المستخدمين...")
    try:
        local_cursor.execute("SELECT * FROM user")
        records = local_cursor.fetchall()

        added_count = 0
        for record in records:
            user_id = record[0]
            username = record[1]
            fullname = record[2] if len(record) > 2 else ''
            email = record[3] if len(record) > 3 else ''
            password_hash = record[4] if len(record) > 4 else ''
            role = record[5] if len(record) > 5 else 'user'
            active = bool(record[6]) if len(record) > 6 else True
            company_id = record[7] if len(record) > 7 else None

            # التحقق من وجود الشركة
            if company_id and not Company.query.get(company_id):
                print(f"   ⚠️ تخطي المستخدم {username} - الشركة {company_id} غير موجودة")
                continue

            exists = User.query.get(user_id)
            if not exists:
                new_user = User(
                    id=user_id,
                    username=username,
                    fullname=fullname,
                    email=email,
                    role=role,
                    active=active,
                    company_id=company_id
                )

                # نسخ كلمة المرور الأصلية إن وجدت
                if password_hash:
                    new_user.password_hash = password_hash
                else:
                    new_user.set_password('123456')  # كلمة افتراضية

                db.session.add(new_user)
                added_count += 1
                print(f"   ➕ أضيف: {username}")

        db.session.commit()
        print(f"✅ المستخدمين: أضيف {added_count} سجل")

    except Exception as e:
        print(f"❌ خطأ في نسخ المستخدمين: {e}")
        db.session.rollback()


def copy_sites(local_cursor):
    """نسخ المواقع"""
    print("\n🏗️ نسخ المواقع...")
    try:
        local_cursor.execute("SELECT * FROM site")
        records = local_cursor.fetchall()

        added_count = 0
        for record in records:
            site_id = record[0]
            name = record[1]
            region_id = record[2] if len(record) > 2 else None

            # إذا كان region_id مطلوباً، تأكد من وجود المنطقة
            if region_id and not Location.query.get(region_id):
                print(f"   ⚠️ تخطي الموقع {name} - المنطقة {region_id} غير موجودة")
                continue

            exists = Site.query.get(site_id)
            if not exists:
                new_site = Site(
                    id=site_id,
                    name=name,
                    region_id=region_id
                )
                db.session.add(new_site)
                added_count += 1
                print(f"   ➕ أضيف: {name}")

        db.session.commit()
        print(f"✅ المواقع: أضيف {added_count} سجل")

    except Exception as e:
        print(f"❌ خطأ في نسخ المواقع: {e}")
        db.session.rollback()


def copy_places(local_cursor):
    """نسخ الأماكن"""
    print("\n🏠 نسخ الأماكن...")
    try:
        local_cursor.execute("SELECT * FROM place")
        records = local_cursor.fetchall()

        added_count = 0
        for record in records:
            place_id = record[0]
            name = record[1]
            site_id = record[2] if len(record) > 2 else None

            # إذا كان site_id مطلوباً، تأكد من وجود الموقع
            if site_id and not Site.query.get(site_id):
                print(f"   ⚠️ تخطي المكان {name} - الموقع {site_id} غير موجود")
                continue

            exists = Place.query.get(place_id)
            if not exists:
                new_place = Place(
                    id=place_id,
                    name=name,
                    site_id=site_id
                )
                db.session.add(new_place)
                added_count += 1
                print(f"   ➕ أضيف: {name}")

        db.session.commit()
        print(f"✅ الأماكن: أضيف {added_count} سجل")

    except Exception as e:
        print(f"❌ خطأ في نسخ الأماكن: {e}")
        db.session.rollback()


def copy_evaluation_authorities(local_cursor):
    """نسخ جهات التقييم"""
    print("\n🏛️ نسخ جهات التقييم...")
    try:
        local_cursor.execute("SELECT * FROM evaluation_authorities")
        records = local_cursor.fetchall()

        added_count = 0
        for record in records:
            authority_id = record[0]
            name = record[1]
            company_id = record[2] if len(record) > 2 else None

            # تأكد من وجود الشركة
            if company_id and not Company.query.get(company_id):
                print(f"   ⚠️ تخطي الجهة {name} - الشركة {company_id} غير موجودة")
                continue

            exists = EvaluationAuthority.query.get(authority_id)
            if not exists:
                new_authority = EvaluationAuthority(
                    id=authority_id,
                    name=name,
                    company_id=company_id
                )
                db.session.add(new_authority)
                added_count += 1
                print(f"   ➕ أضيف: {name}")

        db.session.commit()
        print(f"✅ جهات التقييم: أضيف {added_count} سجل")

    except Exception as e:
        print(f"❌ خطأ في نسخ جهات التقييم: {e}")
        db.session.rollback()


def copy_criteria(local_cursor):
    """نسخ المعايير"""
    print("\n📊 نسخ المعايير...")
    try:
        local_cursor.execute("SELECT * FROM criterion")
        records = local_cursor.fetchall()

        added_count = 0
        for record in records:
            criterion_id = record[0]
            name = record[1]
            min_score = record[2] if len(record) > 2 else 1.0  # قيمة افتراضية
            max_score = record[3] if len(record) > 3 else 10.0  # قيمة افتراضية
            place_id = record[4] if len(record) > 4 else None
            authority_id = record[5] if len(record) > 5 else None

            # تأكد من وجود المكان والجهة إذا كانت مطلوبة
            if place_id and not Place.query.get(place_id):
                print(f"   ⚠️ تخطي المعيار {name} - المكان {place_id} غير موجود")
                continue

            if authority_id and not EvaluationAuthority.query.get(authority_id):
                print(f"   ⚠️ تخطي المعيار {name} - الجهة {authority_id} غير موجودة")
                continue

            exists = Criterion.query.get(criterion_id)
            if not exists:
                new_criterion = Criterion(
                    id=criterion_id,
                    name=name,
                    min_score=float(min_score) if min_score is not None else 1.0,
                    max_score=float(max_score) if max_score is not None else 10.0,
                    place_id=place_id,
                    authority_id=authority_id
                )
                db.session.add(new_criterion)
                added_count += 1
                print(f"   ➕ أضيف: {name}")

        db.session.commit()
        print(f"✅ المعايير: أضيف {added_count} سجل")

    except Exception as e:
        print(f"❌ خطأ في نسخ المعايير: {e}")
        db.session.rollback()


if __name__ == "__main__":
    update_cloud_database()