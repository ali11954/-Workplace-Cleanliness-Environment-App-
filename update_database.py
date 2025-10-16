# update_database.py
import os
import sys
import sqlite3

# إضافة المسار الحالي
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import app, db
from models import User, Company, Location, Site, Place, Criterion, EvaluationAuthority


def update_cloud_database():
    """تحديث قاعدة البيانات السحابية بالبيانات المحلية"""
    with app.app_context():
        try:
            print("🔄 بدء تحديث قاعدة البيانات السحابية...")

            # 1. التحقق من نوع قاعدة البيانات
            db_url = app.config['SQLALCHEMY_DATABASE_URI']
            if 'postgresql' in db_url:
                print("🌐 الاتصال بقاعدة البيانات السحابية (PostgreSQL)")
            else:
                print("💻 الاتصال بقاعدة البيانات المحلية (SQLite)")

            # 2. إنشاء الجداول إذا لم تكن موجودة
            db.create_all()
            print("✅ تم إنشاء/تأكيد الجداول")

            # 3. مسار قاعدة البيانات المحلية
            local_db_path = r'D:\ghith\NEW\hoesing\DullUselessIntegrationtesting\DullUselessIntegrationtesting\instance\database.db'

            if not os.path.exists(local_db_path):
                print("❌ قاعدة البيانات المحلية غير موجودة")
                return

            print(f"📁 قاعدة البيانات المحلية: {local_db_path}")

            # 4. الاتصال بقاعدة البيانات المحلية
            local_conn = sqlite3.connect(local_db_path)
            local_conn.row_factory = sqlite3.Row
            local_cursor = local_conn.cursor()

            # 5. فحص محتويات قاعدة البيانات المحلية أولاً
            print("\n🔍 فحص قاعدة البيانات المحلية...")
            tables_to_check = ['companies', 'user', 'location', 'site', 'place', 'evaluation_authorities', 'criterion']

            for table in tables_to_check:
                try:
                    local_cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                    count = local_cursor.fetchone()['count']
                    print(f"   📊 {table}: {count} سجل")
                except Exception as e:
                    print(f"   ⚠️ {table}: غير موجود - {e}")

            # 6. نسخ البيانات
            print("\n📥 بدء نسخ البيانات...")

            tables_data = [
                ('companies', Company, 'name', '🏢 الشركات'),
                ('user', User, 'username', '👥 المستخدمين'),
                ('location', Location, 'name', '📍 المناطق'),
                ('site', Site, 'name', '🏗️ المواقع'),
                ('place', Place, 'name', '🏠 الأماكن'),
                ('evaluation_authorities', EvaluationAuthority, 'name', '🏛️ جهات التقييم'),
                ('criterion', Criterion, 'name', '📊 المعايير')
            ]

            total_added = 0

            for table_name, model, unique_field, emoji in tables_data:
                try:
                    local_cursor.execute(f"SELECT * FROM {table_name}")
                    records = local_cursor.fetchall()

                    added_count = 0
                    for record in records:
                        try:
                            # التحقق من عدم وجود السجل مسبقاً
                            filter_args = {unique_field: record[unique_field]}
                            exists = model.query.filter_by(**filter_args).first()

                            if not exists:
                                # إنشاء كائن جديد
                                if table_name == 'companies':
                                    new_obj = Company(
                                        name=record['name'],
                                        code=record.get('code', ''),
                                        description=record.get('description', ''),
                                        active=bool(record.get('active', True))
                                    )
                                elif table_name == 'user':
                                    new_obj = User(
                                        username=record['username'],
                                        fullname=record.get('fullname', ''),
                                        email=record.get('email', ''),
                                        role=record.get('role', 'user'),
                                        active=bool(record.get('active', True)),
                                        is_admin=bool(record.get('is_admin', False))
                                    )
                                    new_obj.set_password('123456')  # كلمة مرور افتراضية
                                elif table_name == 'location':
                                    new_obj = Location(
                                        name=record['name'],
                                        code=record.get('code', ''),
                                        is_active=bool(record.get('is_active', True))
                                    )
                                elif table_name == 'site':
                                    new_obj = Site(name=record['name'])
                                elif table_name == 'place':
                                    new_obj = Place(name=record['name'])
                                elif table_name == 'evaluation_authorities':
                                    new_obj = EvaluationAuthority(name=record['name'])
                                elif table_name == 'criterion':
                                    new_obj = Criterion(
                                        name=record['name'],
                                        min_score=float(record.get('min_score', 1)),
                                        max_score=float(record.get('max_score', 10))
                                    )

                                db.session.add(new_obj)
                                added_count += 1
                                print(f"      ➕ أضيف: {record[unique_field]}")

                        except Exception as e:
                            print(f"      ⚠️ خطأ في سجل: {e}")

                    db.session.commit()
                    total_added += added_count
                    print(f"{emoji} {table_name}: أضيف {added_count} سجل")

                except Exception as e:
                    print(f"⚠️ خطأ في جدول {table_name}: {e}")
                    db.session.rollback()

            local_conn.close()

            print(f"\n🎉 اكتمل التحديث! أضيف {total_added} سجل جديد")

            # 7. عرض النتائج النهائية
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


if __name__ == "__main__":
    update_cloud_database()