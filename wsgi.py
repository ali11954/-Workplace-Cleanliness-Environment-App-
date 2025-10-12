from main import app
import os


application = app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    print(f"🚀 التشغيل على المنفذ: {port}")
    app.run(host='0.0.0.0', port=port, debug=app.config['DEBUG'])
