import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import app

# فقط اجعل app كـ application
application = app

print("✅ تم تحميل التطبيق بنجاح")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)