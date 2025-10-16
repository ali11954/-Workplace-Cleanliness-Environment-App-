# copy_missing.py
import os
import sys
import sqlite3

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import app, db
from models import User, Company


def copy_missing_data():
    """نسخ البيانات المفقودة فقط"""
    with app.app_context():
        try:
            print("🔍 البحث عن البيانات المفقودة...")

            local_db_path = r'D:\ghith\NEW\hoesing\DullUselessIntegrationtesting\DullUselessIntegrationtesting\instance\database.db'

            if not os.path.exists(local_db_path):
                print("❌ قاعدة البيانات المحلية غير موجودة")
                return

            local_conn = sqlite3.connect(local_db_path)
            local_conn.row_factory = sqlite3.Row
            local_cursor = local_conn.cursor()

            # نسخ المستخدمين المفقودين فقط
            local_cursor.execute("SELECT * FROM user")
            local_users = local_cursor.fetchall()

            added_users = 0
            for user in local_users:
                existing_user = User.query.filter_by(username=user['username']).first()
                if not existing_user:
                    new_user = User(
                        username=user['username'],
                        fullname=user.get('fullname', ''),
                        email=user.get('email', ''),
                        role=user.get('role', 'user'),
                        active=True
                    )
                    new_user.set_password('123456')
                    db.session.add(new_user)
                    added_users += 1
                    print(f"➕ أضيف مستخدم: {user['username']}")

            db.session.commit()
            local_conn.close()

            print(f"\n🎉 تم إضافة {added_users} مستخدم جديد")
            print(f"👥 إجمالي المستخدمين: {User.query.count()}")

        except Exception as e:
            print(f"❌ خطأ: {e}")


if __name__ == "__main__":
    copy_missing_data()