# update_database_enhanced.py
import os
import sys
import sqlite3

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import app, db
from models import User, Company, Location, Site, Place, Criterion, EvaluationAuthority
from models import Permission, UserPermission, Evaluation, EvaluationDetail


def update_cloud_database():
    """تحديث قاعدة البيانات السحابية بالبيانات المحلية - نسخة محسنة"""
    with app.app_context():
        try:
            print("🔄 بدء تحديث قاعدة البيانات السحابية...")

            # التحقق من نوع قاعدة البيانات الهدف
            db_url = app.config['SQLALCHEMY_DATABASE_URI']
            if 'postgresql' in db_url:
                print("🌐 الهدف: قاعدة البيانات السحابية (PostgreSQL)")
            else:
                print("💻 الهدف: قاعدة البيانات المحلية (SQLite)")
                response = input("⚠️  أنت تستهدف قاعدة بيانات محلية. هل تريد المتابعة؟ (y/n): ")
                if response.lower() != 'y':
                    return

            # إنشاء الجداول
            db.create_all()
            print("✅ تم إنشاء/تأكيد الجداول")

            # مسار قاعدة البيانات المحلية المصدر
            local_db_path = r'D:\ghith\NEW\hoesing\DullUselessIntegrationtesting\DullUselessIntegrationtesting\instance\database.db'

            if not os.path.exists(local_db_path):
                print("❌ قاعدة البيانات المحلية غير موجودة")
                return

            print(f"📁 مصدر البيانات: {local_db_path}")

            # الاتصال بالمحلية
            local_conn = sqlite3.connect(local_db_path)
            local_conn.row_factory = sqlite3.Row
            local_cursor = local_conn.cursor()

            # فحص المحتويات
            print("\n🔍 فحص قاعدة البيانات المحلية...")
            all_tables = [
                'companies', 'user', 'location', 'site', 'place',
                'evaluation_authorities', 'criterion', 'permissions',
                'user_permissions', 'evaluation', 'evaluation_detail'
            ]

            for table in all_tables:
                try:
                    local_cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                    count = local_cursor.fetchone()['count']
                    print(f"   📊 {table}: {count} سجل")
                except Exception as e:
                    print(f"   ⚠️ {table}: غير موجود - {e}")

            # نسخ البيانات
            print("\n📥 بدء نسخ البيانات...")

            tables_data = [
                ('companies', Company, 'name', '🏢 الشركات'),
                ('user', User, 'username', '👥 المستخدمين'),
                ('location', Location, 'name', '📍 المناطق'),
                ('site', Site, 'name', '🏗️ المواقع'),
                ('place', Place, 'name', '🏠 الأماكن'),
                ('evaluation_authorities', EvaluationAuthority, 'name', '🏛️ جهات التقييم'),
                ('criterion', Criterion, 'name', '📊 المعايير'),
                ('permissions', Permission, 'name', '🔐 الصلاحيات')
            ]

            total_added = 0

            for table_name, model, unique_field, emoji in tables_data:
                try:
                    local_cursor.execute(f"SELECT * FROM {table_name}")
                    records = local_cursor.fetchall()

                    added_count = 0
                    for record in records:
                        try:
                            # التحقق من التكرار
                            filter_args = {unique_field: record[unique_field]}
                            exists = model.query.filter_by(**filter_args).first()

                            if not exists:
                                # إنشاء الكائن حسب نوع الجدول
                                if table_name == 'companies':
                                    new_obj = Company(
                                        id=record['id'],  # الحفاظ على الـ ID الأصلي
                                        name=record['name'],
                                        code=record.get('code', ''),
                                        active=bool(record.get('active', True))
                                    )
                                elif table_name == 'user':
                                    new_obj = User(
                                        id=record['id'],  # الحفاظ على الـ ID
                                        username=record['username'],
                                        fullname=record.get('fullname', ''),
                                        email=record.get('email', ''),
                                        role=record.get('role', 'user'),
                                        active=bool(record.get('active', True)),
                                        company_id=record.get('company_id'),
                                        is_admin=bool(record.get('is_admin', False))
                                    )
                                    # نسخ كلمة المرور الأصلية إن وجدت
                                    if 'password_hash' in record and record['password_hash']:
                                        new_obj.password_hash = record['password_hash']
                                    else:
                                        new_obj.set_password('123456')
                                elif table_name == 'location':
                                    new_obj = Location(
                                        id=record['id'],
                                        name=record['name'],
                                        code=record.get('code', ''),
                                        is_active=bool(record.get('is_active', True)),
                                        company_id=record.get('company_id')
                                    )
                                elif table_name == 'permissions':
                                    new_obj = Permission(
                                        id=record['id'],
                                        name=record['name'],
                                        code=record['code'],
                                        description=record.get('description', ''),
                                        category=record.get('category', '')
                                    )
                                else:
                                    # للجداول البسيطة
                                    new_obj = model(name=record['name'])
                                    if hasattr(new_obj, 'id') and 'id' in record:
                                        new_obj.id = record['id']

                                db.session.add(new_obj)
                                added_count += 1
                                print(f"      ➕ {emoji} أضيف: {record[unique_field]}")

                        except Exception as e:
                            print(f"      ⚠️ خطأ في سجل: {e}")

                    db.session.commit()
                    total_added += added_count
                    print(f"{emoji} {table_name}: أضيف {added_count} سجل")

                except Exception as e:
                    print(f"⚠️ خطأ في جدول {table_name}: {e}")
                    db.session.rollback()

            # نسخ الجداول ذات العلاقات
            copy_relationship_tables(local_cursor)

            local_conn.close()

            print(f"\n🎉 اكتمل التحديث! أضيف {total_added} سجل جديد")

            # عرض النتائج
            print("\n📊 الإحصائيات النهائية:")
            print("=" * 50)
            print(f"🏢 الشركات: {Company.query.count()}")
            print(f"👥 المستخدمين: {User.query.count()}")
            print(f"📍 المناطق: {Location.query.count()}")
            print(f"🔐 الصلاحيات: {Permission.query.count()}")
            print("=" * 50)

        except Exception as e:
            print(f"❌ خطأ في التحديث: {e}")
            import traceback
            traceback.print_exc()


def copy_relationship_tables(local_cursor):
    """نسخ الجداول ذات العلاقات"""
    print("\n🔗 نسخ الجداول ذات العلاقات...")

    # نسخ user_permissions
    try:
        local_cursor.execute("SELECT * FROM user_permissions")
        records = local_cursor.fetchall()

        added_count = 0
        for record in records:
            # التحقق من وجود المستخدم والصلاحية
            user_exists = User.query.get(record['user_id'])
            perm_exists = Permission.query.filter_by(code=record['permission_code']).first()

            if user_exists and perm_exists:
                # التحقق من عدم وجود التكرار
                exists = UserPermission.query.filter_by(
                    user_id=record['user_id'],
                    permission_code=record['permission_code']
                ).first()

                if not exists:
                    new_perm = UserPermission(
                        user_id=record['user_id'],
                        permission_code=record['permission_code']
                    )
                    db.session.add(new_perm)
                    added_count += 1

        db.session.commit()
        print(f"🔐 user_permissions: أضيف {added_count} سجل")
    except Exception as e:
        print(f"⚠️ خطأ في user_permissions: {e}")


if __name__ == "__main__":
    update_cloud_database()