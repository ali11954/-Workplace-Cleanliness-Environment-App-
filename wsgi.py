from main import app, db, initialize_database
import os

# تهيئة قاعدة البيانات عند التشغيل
with app.app_context():
    print("🚀 بدء تهيئة قاعدة البيانات على Render...")
    try:
        initialize_database()
        print("✅ تم تهيئة قاعدة البيانات بنجاح")

        # تحقق من البيانات
        from main import User, Company

        user_count = User.query.count()
        company_count = Company.query.count()
        print(f"📊 عدد المستخدمين: {user_count}")
        print(f"🏢 عدد الشركات: {company_count}")

    except Exception as e:
        print(f"❌ خطأ في التهيئة: {e}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)