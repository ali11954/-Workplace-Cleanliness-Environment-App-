from flask import Flask, render_template, redirect, url_for, request, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm
from models import Evaluation, Location, EvaluationAuthority, Criterion, Place, Site, Location, User, EvaluationDetail, ActionPlan
from flask import request
from sqlalchemy import func
from wtforms import StringField, PasswordField, SubmitField, IntegerField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Length, NumberRange, EqualTo, Optional
from datetime import datetime
from collections import defaultdict
import io
from wtforms import StringField, SelectField, FloatField, SubmitField
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField
from wtforms.validators import DataRequired
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
import arabic_reshaper
from bidi.algorithm import get_display
import os
from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from flask_migrate import Migrate
from flask import jsonify
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField
from wtforms.validators import DataRequired, NumberRange
from flask_wtf import FlaskForm
from wtforms import SelectField, TextAreaField, SubmitField
from wtforms.validators import DataRequired
from wtforms import IntegerField
from wtforms.validators import InputRequired, NumberRange
from sqlalchemy.orm import joinedload
from flask import Flask, render_template
from flask_login import login_required
from sqlalchemy import func
from sqlalchemy.orm import joinedload
from flask_sqlalchemy import SQLAlchemy
from models import db  # أو من مكانك الصحيح حسب مشروعك
from models import User
# في الأعلى مع بقية الاستدعاءات
from models import EvaluationAuthority



from flask import Flask
from models import db ,Location,Site,Place,Criterion,Evaluation,EvaluationDetail  # ← استيراد db من models فقط




# في بداية الملف بعد الاستيرادات
import os
from flask import Flask

app = Flask(__name__)

# إعدادات قاعدة البيانات للنشر
database_url = os.environ.get('DATABASE_URL')
if database_url:
    # تحويل من postgres إلى postgresql لـ SQLAlchemy
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    # للتطوير المحلي
    basedir = os.path.abspath(os.path.dirname(__file__))
    instance_path = os.path.join(basedir, 'instance')
    os.makedirs(instance_path, exist_ok=True)
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(instance_path, 'database.db')}"

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# تأكد أن db مستورد من models بشكل صحيح
from models import db
db.init_app(app)


@app.route("/debug-users")
def debug_users():
    users = User.query.all()
    return "<br>".join([f"{u.username} - {u.email} - {u.role}" for u in users])

# إنشاء تطبيق Flask

# تهيئة قاعدة البيانات وتسجيل الدخول


login_manager = LoginManager(app)
login_manager.login_view = 'login'
migrate = Migrate(app, db)
# التحقق من وجود قاعدة البيانات
if __name__ == "__main__":
    with app.app_context():
        with db.engine.connect() as conn:
            print("تم الاتصال بقاعدة البيانات بنجاح")


# تسجيل خط Amiri
font_path = 'fonts/Amiri-Regular.ttf'
if os.path.exists(font_path):
    pdfmetrics.registerFont(TTFont('Amiri', font_path))
else:
    print("تحذير: خط Amiri غير موجود - تقارير PDF قد لا تعرض العربية بشكل صحيح.")

# ====== MODELS ======
    # بقية الحقول والدوال هنا

    @property
    def is_active(self):
        return self.active

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)

# ====== FORMS ======

class LoginForm(FlaskForm):
    username = StringField('اسم المستخدم', validators=[DataRequired()])
    password = PasswordField('كلمة المرور', validators=[DataRequired()])
    submit = SubmitField('تسجيل الدخول')

from wtforms import SelectMultipleField

class UserForm(FlaskForm):
    fullname = StringField('الاسم الكامل', validators=[DataRequired(), Length(min=3, max=150)])
    username = StringField('اسم المستخدم', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('البريد الإلكتروني', validators=[DataRequired(), Length(max=120)])
    password = PasswordField('كلمة المرور', validators=[Optional(), Length(min=6)])
    password_confirm = PasswordField('تأكيد كلمة المرور', validators=[EqualTo('password', message='كلمتا المرور غير متطابقتين')])
    role = SelectField('الدور', choices=[('admin', 'مشرف'), ('user', 'مستخدم')], default='user')
    active = SelectField('نشط', choices=[('1', 'نعم'), ('0', 'لا')], default='1')

    # تعديل هذا الحقل ليكون متعدد
    region_ids = SelectMultipleField('اختر المناطق', coerce=int, validators=[DataRequired()])

    submit = SubmitField('حفظ')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from flask import current_app
        with current_app.app_context():
            self.region_ids.choices = [(r.id, r.name) for r in Location.query.order_by(Location.name).all()]
        # ضمان أن data ليست None
        if self.region_ids.data is None:
            self.region_ids.data = []

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

class EvaluationAuthorityForm(FlaskForm):
    name = StringField('اسم الجهة', validators=[DataRequired()])
    submit = SubmitField('إضافة الجهة')

class RegionForm(FlaskForm):
    name = StringField('اسم المنطقة', validators=[DataRequired()])
    submit = SubmitField('إضافة منطقة')

class SiteForm(FlaskForm):
    name = StringField('اسم الموقع', validators=[DataRequired()])
    region_id = SelectField('اختر المنطقة', coerce=int, validators=[DataRequired()])
    submit = SubmitField('إضافة موقع')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.region_id.choices = [(r.id, r.name) for r in Location.query.order_by(Location.name).all()]

class PlaceForm(FlaskForm):
    name = StringField('اسم المكان', validators=[DataRequired()])
    site_id = SelectField('اختر الموقع', coerce=int, validators=[DataRequired()])
    submit = SubmitField('إضافة مكان')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.site_id.choices = [(s.id, s.name) for s in Site.query.order_by(Site.name).all()]


# forms.py
from flask_wtf import FlaskForm
from wtforms import SelectField, IntegerField, FloatField, StringField, TextAreaField, SubmitField, FieldList, FormField
from wtforms.validators import DataRequired, InputRequired, NumberRange

class CriterionAddForm(FlaskForm):
    criterion_id = SelectField('المعيار', coerce=int, validators=[DataRequired()])
    min_score = IntegerField('الحد الأدنى', validators=[DataRequired()])
    max_score = IntegerField('الحد الأعلى', validators=[DataRequired()])
    authority_id = SelectField('الجهة المسؤولة', coerce=int, validators=[DataRequired()])
    score = IntegerField('درجة التقييم', validators=[InputRequired(), NumberRange(min=1, max=10)])

class EvaluationForm(FlaskForm):
    region_id = SelectField('المنطقة', coerce=int, validators=[DataRequired()])
    site_id = SelectField('الموقع', coerce=int, validators=[DataRequired()])
    place_id = SelectField('المكان', coerce=int, validators=[DataRequired()])
    details = FieldList(FormField(CriterionAddForm), min_entries=1)
    notes = TextAreaField('الملاحظات')
    submit = SubmitField('حفظ التقييم')



# forms.py

class LocationSelectionForm(FlaskForm):
    region_id = SelectField('اختر المنطقة', coerce=int, validators=[DataRequired()])
    site_id = SelectField('اختر الموقع', coerce=int, validators=[DataRequired()])
    place_id = SelectField('اختر المكان', coerce=int, validators=[DataRequired()])
    submit = SubmitField('تحميل المعايير')




# ====== ROUTES ======
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # صفحة تسجيل الدخول


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    if current_user.is_authenticated:
        # لو المستخدم سجل دخول قبل كذا
        if current_user.role == 'admin':
            return redirect(url_for('dashboard'))
        else:
            return redirect(url_for('user_dashboard'))
    else:
        # لو ما سجل دخول يروح لصفحة تسجيل الدخول
        return redirect(url_for('login'))

# الصفحة الرئيسية توجّه حسب نوع المستخدم
from flask import render_template
from flask_login import login_required
from sqlalchemy import func
from models import db, User, Evaluation, EvaluationDetail, Criterion, Place, Site, Location, EvaluationAuthority
from datetime import date

from datetime import datetime, date, timedelta
from sqlalchemy import func, extract


@app.route('/dashboard')
@login_required
def dashboard():
    today = date.today()
    now = datetime.now()

    # ===== إحصاءات عامة =====
    total_evaluations = Evaluation.query.count()
    total_regions = Location.query.count()
    regions_evaluated = db.session.query(Evaluation.region_id).distinct().count()
    total_authorities = EvaluationAuthority.query.count()
    authorities_evaluated = db.session.query(EvaluationDetail.authority_id).distinct().count()
    users = User.query.filter(User.role != 'admin', User.active == True).all()

    highest_score = db.session.query(func.max(EvaluationDetail.score)).scalar() or 0
    avg_score = round(db.session.query(func.avg(EvaluationDetail.score)).scalar() or 0, 1)

    # ===== الملاحظات =====
    total_action_plans = db.session.query(EvaluationDetail).filter(
        EvaluationDetail.note.isnot(None), EvaluationDetail.note != ''
    ).count()
    closed_action_plans = db.session.query(ActionPlan).filter(ActionPlan.closed == True).count()
    open_action_plans = total_action_plans - closed_action_plans
    close_percentage = round((closed_action_plans / total_action_plans) * 100, 1) if total_action_plans else 0

    top_regions_count = db.session.query(Evaluation.region_id) \
        .join(EvaluationDetail, Evaluation.id == EvaluationDetail.evaluation_id) \
        .group_by(Evaluation.region_id) \
        .having(func.avg(EvaluationDetail.score) >= 90).count()

    completed_authorities = db.session.query(EvaluationDetail.authority_id) \
        .group_by(EvaluationDetail.authority_id).count()

    # ===== بيانات المقارنات الزمنية =====
    time_comparison_data = get_time_comparison_data()

    # ===== بيانات الرسوم البيانية الزمنية =====
    weekly_trends = get_weekly_trends()
    monthly_comparison = get_monthly_comparison()
    daily_performance = get_daily_performance()

    # ===== بيانات المستخدمين (الكود الحالي) =====
    dashboard_users = []
    colors = ["#FFCDD2", "#C8E6C9", "#BBDEFB", "#FFF9C4", "#D1C4E9", "#B2DFDB", "#FFE0B2", "#F8BBD0"]
    color_index = 0

    for user in users:
        # ... كود المستخدمين الحالي بدون تغيير ...
        total_criteria = db.session.query(Criterion.id) \
            .join(Place).join(Site) \
            .filter(Site.region_id == user.region_id).count()

        today_evaluated = db.session.query(EvaluationDetail.id) \
            .join(Evaluation, Evaluation.id == EvaluationDetail.evaluation_id) \
            .filter(Evaluation.user_id == user.id, func.date(Evaluation.date) == today).count()

        today_percent = round((today_evaluated / total_criteria) * 100, 1) if total_criteria else 0
        today_percent = min(today_percent, 100)

        total_evaluated = db.session.query(EvaluationDetail.id) \
            .join(Evaluation, Evaluation.id == EvaluationDetail.evaluation_id) \
            .filter(Evaluation.user_id == user.id).count()

        first_eval_date = db.session.query(func.min(Evaluation.date)) \
            .filter(Evaluation.user_id == user.id).scalar()

        if first_eval_date:
            days_count = (today - first_eval_date.date()).days + 1
            total_criteria_all_period = total_criteria * days_count
        else:
            total_criteria_all_period = 0

        total_percent = round((total_evaluated / total_criteria_all_period) * 100,
                              1) if total_criteria_all_period else 0
        total_percent = min(total_percent, 100)

        user_color = colors[color_index % len(colors)]
        color_index += 1

        dashboard_users.append({
            "id": user.id,
            "fullname": user.fullname,
            "today_percent": today_percent,
            "total_percent": total_percent,
            "today_evaluated": today_evaluated,
            "total_evaluated": total_evaluated,
            "total_criteria": total_criteria,
            "color": user_color
        })

    # ===== بيانات جهات المسؤولية (الكود الحالي) =====
    authorities = EvaluationAuthority.query.all()
    chart_data = []

    for auth in authorities:
        # ... كود جهات المسؤولية الحالي بدون تغيير ...
        total_criteria = db.session.query(func.count(Criterion.id)) \
                             .filter(Criterion.authority_id == auth.id).scalar() or 0

        today_eval = db.session.query(
            func.sum(EvaluationDetail.score).label("score_sum"),
            func.sum(Criterion.max_score).label("max_sum"),
            func.count(EvaluationDetail.id)
        ).join(Criterion, EvaluationDetail.criterion_id == Criterion.id) \
            .join(Evaluation, EvaluationDetail.evaluation_id == Evaluation.id) \
            .filter(Criterion.authority_id == auth.id, func.date(Evaluation.date) == today).first()

        today_score = today_eval.score_sum or 0
        today_max = today_eval.max_sum or 0
        today_count = today_eval[2] or 0
        today_percent = round((today_score / today_max * 100), 1) if today_max else 0

        total_eval = db.session.query(
            func.sum(EvaluationDetail.score).label("score_sum"),
            func.sum(Criterion.max_score).label("max_sum"),
            func.count(EvaluationDetail.id)
        ).join(Criterion, EvaluationDetail.criterion_id == Criterion.id) \
            .join(Evaluation, EvaluationDetail.evaluation_id == Evaluation.id) \
            .filter(Criterion.authority_id == auth.id).first()

        total_score = total_eval.score_sum or 0
        total_max = total_eval.max_sum or 0
        total_count = total_eval[2] or 0
        total_percent = round((total_score / total_max * 100), 1) if total_max else 0

        chart_data.append({
            "authority": auth.name,
            "today_percent": today_percent,
            "total_percent": total_percent,
            "today_evaluated": today_count,
            "total_evaluated": total_count,
            "total_criteria": total_criteria
        })

    # ===== تحديد نوع المستوى (الكود الحالي) =====
    level_type = request.args.get('level', 'region')

    # ===== جمع البيانات حسب النوع (الكود الحالي) =====
    if level_type == 'region':
        levels = Location.query.all()
    elif level_type == 'site':
        levels = Site.query.all()
    elif level_type == 'place':
        levels = (
            db.session.query(Place.name, func.min(Place.id).label("id"))
            .group_by(Place.name)
            .all()
        )

    level_data = []

    for lvl in levels:
        # ... كود المستويات الحالي بدون تغيير ...
        if level_type == 'region':
            filter_condition = Site.region_id == lvl.id
            level_name = lvl.name
        elif level_type == 'site':
            filter_condition = Place.site_id == lvl.id
            level_name = lvl.name
        else:  # place
            filter_condition = Place.name == lvl.name
            level_name = lvl.name

        total_criteria = db.session.query(func.count(Criterion.id)) \
                             .filter(filter_condition).scalar() or 0

        today_eval = db.session.query(
            func.sum(EvaluationDetail.score).label("score_sum"),
            func.sum(Criterion.max_score).label("max_sum"),
            func.count(EvaluationDetail.id)
        ).join(Criterion, EvaluationDetail.criterion_id == Criterion.id) \
            .outerjoin(Evaluation, EvaluationDetail.evaluation_id == Evaluation.id) \
            .outerjoin(Place, Place.id == Criterion.place_id) \
            .outerjoin(Site, Site.id == Place.site_id) \
            .filter(filter_condition) \
            .filter(func.date(Evaluation.date) == today) \
            .first()

        today_score = today_eval.score_sum or 0
        today_max = today_eval.max_sum or 0
        today_count = today_eval[2] or 0
        today_percent = round((today_score / today_max * 100), 1) if today_max else 0

        total_eval = db.session.query(
            func.sum(EvaluationDetail.score).label("score_sum"),
            func.sum(Criterion.max_score).label("max_sum"),
            func.count(EvaluationDetail.id)
        ).join(Criterion, EvaluationDetail.criterion_id == Criterion.id) \
            .outerjoin(Evaluation, EvaluationDetail.evaluation_id == Evaluation.id) \
            .outerjoin(Place, Place.id == Criterion.place_id) \
            .outerjoin(Site, Site.id == Place.site_id) \
            .filter(filter_condition) \
            .first()

        total_score = total_eval.score_sum or 0
        total_max = total_eval.max_sum or 0
        total_count = total_eval[2] or 0
        total_percent = round((total_score / total_max * 100), 1) if total_max else 0

        level_data.append({
            "level": level_name,
            "today_percent": today_percent,
            "total_percent": total_percent,
            "today_evaluated": today_count,
            "total_evaluated": total_count,
            "total_criteria": total_criteria
        })

    # ===== تمرير البيانات للـ Jinja2 =====
    return render_template(
        'admin/dashboard.html',
        now=now,
        users=dashboard_users,
        total_evaluations=total_evaluations,
        total_regions=total_regions,
        regions_evaluated=regions_evaluated,
        total_authorities=total_authorities,
        authorities_evaluated=authorities_evaluated,
        highest_score=highest_score,
        avg_score=avg_score,
        top_regions_count=top_regions_count,
        completed_authorities=completed_authorities,
        total_action_plans=total_action_plans,
        closed_action_plans=closed_action_plans,
        open_action_plans=open_action_plans,
        close_percentage=close_percentage,
        authorities=chart_data,
        level_data=level_data,
        level_type=level_type,
        # البيانات الجديدة للمقارنات الزمنية
        time_comparison=time_comparison_data,
        weekly_trends=weekly_trends,
        monthly_comparison=monthly_comparison,
        daily_performance=daily_performance
    )


# ===== دوال جديدة للمقارنات الزمنية =====
def get_time_comparison_data():
    """الحصول على بيانات المقارنة بين الفترات الزمنية"""
    today = date.today()

    # الأسبوع الحالي
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)

    # الأسبوع الماضي
    start_of_last_week = start_of_week - timedelta(days=7)
    end_of_last_week = end_of_week - timedelta(days=7)

    # الشهر الحالي
    start_of_month = today.replace(day=1)
    end_of_month = (start_of_month + timedelta(days=32)).replace(day=1) - timedelta(days=1)

    # الشهر الماضي
    start_of_last_month = (start_of_month - timedelta(days=1)).replace(day=1)
    end_of_last_month = start_of_month - timedelta(days=1)

    # بيانات الأسبوع الحالي
    current_week_data = db.session.query(
        func.avg(EvaluationDetail.score).label('avg_score'),
        func.count(EvaluationDetail.id).label('evaluation_count')
    ).join(Evaluation).filter(
        Evaluation.date >= start_of_week,
        Evaluation.date <= end_of_week
    ).first()

    # بيانات الأسبوع الماضي
    last_week_data = db.session.query(
        func.avg(EvaluationDetail.score).label('avg_score'),
        func.count(EvaluationDetail.id).label('evaluation_count')
    ).join(Evaluation).filter(
        Evaluation.date >= start_of_last_week,
        Evaluation.date <= end_of_last_week
    ).first()

    # بيانات الشهر الحالي
    current_month_data = db.session.query(
        func.avg(EvaluationDetail.score).label('avg_score'),
        func.count(EvaluationDetail.id).label('evaluation_count')
    ).join(Evaluation).filter(
        Evaluation.date >= start_of_month,
        Evaluation.date <= end_of_month
    ).first()

    # بيانات الشهر الماضي
    last_month_data = db.session.query(
        func.avg(EvaluationDetail.score).label('avg_score'),
        func.count(EvaluationDetail.id).label('evaluation_count')
    ).join(Evaluation).filter(
        Evaluation.date >= start_of_last_month,
        Evaluation.date <= end_of_last_month
    ).first()

    return {
        'weekly': {
            'current': {
                'avg_score': round(current_week_data.avg_score or 0, 1),
                'evaluation_count': current_week_data.evaluation_count or 0
            },
            'last': {
                'avg_score': round(last_week_data.avg_score or 0, 1),
                'evaluation_count': last_week_data.evaluation_count or 0
            },
            'score_change': calculate_percentage_change(
                current_week_data.avg_score or 0,
                last_week_data.avg_score or 0
            ),
            'count_change': calculate_percentage_change(
                current_week_data.evaluation_count or 0,
                last_week_data.evaluation_count or 0
            )
        },
        'monthly': {
            'current': {
                'avg_score': round(current_month_data.avg_score or 0, 1),
                'evaluation_count': current_month_data.evaluation_count or 0
            },
            'last': {
                'avg_score': round(last_month_data.avg_score or 0, 1),
                'evaluation_count': last_month_data.evaluation_count or 0
            },
            'score_change': calculate_percentage_change(
                current_month_data.avg_score or 0,
                last_month_data.avg_score or 0
            ),
            'count_change': calculate_percentage_change(
                current_month_data.evaluation_count or 0,
                last_month_data.evaluation_count or 0
            )
        }
    }


def get_weekly_trends():
    """الحصول على اتجاهات الأداء الأسبوعية"""
    today = date.today()
    weeks_data = []

    for i in range(4):  # آخر 4 أسابيع
        start_date = today - timedelta(days=today.weekday() + (i * 7))
        end_date = start_date + timedelta(days=6)

        week_data = db.session.query(
            func.avg(EvaluationDetail.score).label('avg_score'),
            func.count(EvaluationDetail.id).label('evaluation_count')
        ).join(Evaluation).filter(
            Evaluation.date >= start_date,
            Evaluation.date <= end_date
        ).first()

        weeks_data.append({
            'week': f"أسبوع {4 - i}",
            'avg_score': round(week_data.avg_score or 0, 1),
            'evaluation_count': week_data.evaluation_count or 0,
            'start_date': start_date.strftime('%d/%m'),
            'end_date': end_date.strftime('%d/%m')
        })

    return list(reversed(weeks_data))  # عكس القائمة لتبدأ بالأقدم


def get_monthly_comparison():
    """مقارنة الأداء بين الشهور"""
    monthly_data = []

    for i in range(6):  # آخر 6 شهور
        month_start = (date.today().replace(day=1) - timedelta(days=30 * i)).replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)

        month_stats = db.session.query(
            func.avg(EvaluationDetail.score).label('avg_score'),
            func.count(EvaluationDetail.id).label('evaluation_count'),
            func.count(db.distinct(Evaluation.user_id)).label('active_users')
        ).join(Evaluation).filter(
            Evaluation.date >= month_start,
            Evaluation.date <= month_end
        ).first()

        monthly_data.append({
            'month': month_start.strftime('%Y-%m'),
            'month_name': month_start.strftime('%b %Y'),
            'avg_score': round(month_stats.avg_score or 0, 1),
            'evaluation_count': month_stats.evaluation_count or 0,
            'active_users': month_stats.active_users or 0
        })

    return list(reversed(monthly_data))


def get_daily_performance():
    """الحصول على أداء الأيام الأخيرة"""
    daily_data = []

    for i in range(7):  # آخر 7 أيام
        day = date.today() - timedelta(days=i)

        day_stats = db.session.query(
            func.avg(EvaluationDetail.score).label('avg_score'),
            func.count(EvaluationDetail.id).label('evaluation_count'),
            func.count(db.distinct(Evaluation.user_id)).label('active_users')
        ).join(Evaluation).filter(
            func.date(Evaluation.date) == day
        ).first()

        daily_data.append({
            'date': day,
            'day_name': day.strftime('%A'),
            'date_short': day.strftime('%d/%m'),
            'avg_score': round(day_stats.avg_score or 0, 1),
            'evaluation_count': day_stats.evaluation_count or 0,
            'active_users': day_stats.active_users or 0
        })

    return list(reversed(daily_data))


def calculate_percentage_change(current, previous):
    """حساب نسبة التغير المئوية"""
    if previous == 0:
        return 100 if current > 0 else 0
    return round(((current - previous) / previous) * 100, 1)

@app.route('/user_dashboard')
@login_required
def user_dashboard():
    return render_template('user/dashboard.html', users=users)

# صفحة تسجيل الدخول
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if user.check_password(form.password.data):
                if user.active:
                    login_user(user)
                    flash('تم تسجيل الدخول بنجاح', 'success')
                    return redirect(url_for('index'))  # توجه الصفحة الرئيسية حسب الدور
                else:
                    flash('الحساب غير نشط', 'danger')
            else:
                flash('كلمة المرور غير صحيحة', 'danger')
        else:
            flash('اسم المستخدم غير موجود', 'danger')
    return render_template('admin/login.html', form=form)

# تسجيل الخروج
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('تم تسجيل الخروج', 'info')
    return redirect(url_for('login'))

# --- إدارة المستخدمين ---
@app.route('/users')
@login_required
def users():
    if current_user.role != 'admin':
        flash('غير مصرح لك', 'danger')
        return redirect(url_for('index'))
    users = User.query.all()
    return render_template('admin/users.html', users=users)


# --- إضافة مستخدم ---
@app.route('/users/add', methods=['GET', 'POST'])
@login_required
def add_user():
    if current_user.role not in ['admin', 'supervisor']:
        flash('غير مصرح لك', 'danger')
        return redirect(url_for('index'))

    form = UserForm()
    form.active.choices = [('1', 'نعم'), ('0', 'لا')]
    # تمرير جميع المستخدمين والمناطق للقالب
    users_list = User.query.all()
    regions_list = Location.query.order_by(Location.name).all()

    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            flash('اسم المستخدم موجود مسبقاً', 'warning')
            return render_template('admin/user_form.html', form=form, users=users_list, regions=regions_list)
        # مثال: إضافة مستخدم
        user = User(
            fullname=form.fullname.data,
            username=form.username.data,
            email=form.email.data,
            role=form.role.data,
            active=(form.active.data == '1')
        )
        user.set_password(form.password.data)
        # ربط المستخدم بالمناطق المختارة
        user.regions = Location.query.filter(Location.id.in_(form.region_ids.data)).all()
        db.session.add(user)
        db.session.commit()

        if form.password.data:
            user.set_password(form.password.data)
        else:
            flash('كلمة المرور مطلوبة', 'warning')
            return render_template(
                'admin/user_form.html',
                form=form,
                users=users_list,
                regions=regions_list,
                selected_user_id=None  # لا يوجد مستخدم محدد
            )

        db.session.add(user)
        db.session.commit()
        flash('تم إضافة المستخدم بنجاح', 'success')
        return redirect(url_for('users'))


    return render_template('admin/user_form.html', form=form, users=users_list, regions=regions_list)


# --- تعديل مستخدم ---
@app.route('/users/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    if current_user.role not in ['admin', 'supervisor']:
        flash('غير مصرح لك', 'danger')
        return redirect(url_for('index'))

    user = User.query.get_or_404(user_id)
    form = UserForm(obj=user)
    form.active.choices = [('1', 'نعم'), ('0', 'لا')]
    form.user_id = user.id
    users_list = User.query.all()
    regions_list = Location.query.order_by(Location.name).all()

    # تعطيل التحقق الإجباري لكلمة المرور في التعديل
    form.password.validators = []
    form.password_confirm.validators = [EqualTo('password', message='كلمتا المرور غير متطابقتين')]

    # ✅ ضبط القيمة الافتراضية فقط عند GET
    if request.method == "GET":
        form.active.data = '1' if user.active else '0'
        form.region_ids.data = [r.id for r in user.regions]

    if form.validate_on_submit():
        if User.query.filter(User.id != user.id, User.username == form.username.data).first():
            flash('اسم المستخدم موجود مسبقاً', 'warning')
            return render_template(
                'admin/user_form.html',
                form=form,
                users=users_list,
                regions=regions_list,
                selected_user_id=user.id
            )

        user.fullname = form.fullname.data
        user.username = form.username.data
        user.email = form.email.data
        user.role = form.role.data
        user.active = True if form.active.data == '1' else False

        if form.password.data:
            user.set_password(form.password.data)

        # تحديث المناطق
        user.regions = Location.query.filter(Location.id.in_(form.region_ids.data)).all()
        db.session.commit()

        flash('تم تعديل بيانات المستخدم', 'success')
        return redirect(url_for('users'))

    return render_template('admin/user_form.html', form=form, users=users_list, regions=regions_list)

@app.route('/users/delete/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if current_user.role != 'admin':
        flash('غير مصرح لك', 'danger')
        return redirect(url_for('index'))

    user = User.query.get_or_404(user_id)

    if user.username == 'admin':
        flash('لا يمكن حذف المشرف الرئيسي', 'warning')
        return redirect(url_for('users'))

    if user.evaluations:
        # بدل الحذف، اجعل المستخدم غير نشط
        user.active = False
        db.session.commit()
        flash('المستخدم مرتبط بتقييمات، تم تغييره إلى غير نشط بدلاً من الحذف', 'info')
        return redirect(url_for('users'))

    # إذا لم يكن مرتبطاً بأي تقييم، يمكن حذفه
    db.session.delete(user)
    db.session.commit()
    flash('تم حذف المستخدم', 'success')
    return redirect(url_for('users'))


@app.route('/authorities', methods=['GET', 'POST'])
@login_required
def authorities():
    if current_user.role != 'admin':
        flash('غير مصرح لك', 'danger')
        return redirect(url_for('dashboard'))

    form = EvaluationAuthorityForm()

    # إضافة جهة جديدة
    if form.validate_on_submit():
        new_auth = EvaluationAuthority(name=form.name.data)
        db.session.add(new_auth)
        try:
            db.session.commit()
            flash('تمت إضافة الجهة بنجاح', 'success')
        except:
            db.session.rollback()
            flash('هذه الجهة موجودة مسبقاً', 'danger')
        return redirect(url_for('authorities'))

    authorities = EvaluationAuthority.query.order_by(EvaluationAuthority.name).all()
    return render_template('admin/authorities.html', form=form, authorities=authorities)


# تعديل جهة
@app.route('/authorities/edit/<int:auth_id>', methods=['POST'])
@login_required
def edit_authority(auth_id):
    if current_user.role != 'admin':
        flash('غير مصرح لك', 'danger')
        return redirect(url_for('authorities'))

    authority = EvaluationAuthority.query.get_or_404(auth_id)
    new_name = request.form.get('new_name')
    if new_name:
        authority.name = new_name
        db.session.commit()
        flash('تم تعديل اسم الجهة بنجاح', 'success')
    else:
        flash('اسم الجهة لا يمكن أن يكون فارغاً', 'warning')
    return redirect(url_for('authorities'))


# حذف جهة
@app.route('/authorities/delete/<int:auth_id>', methods=['POST'])
@login_required
def delete_authority(auth_id):
    if current_user.role != 'admin':
        flash('غير مصرح لك', 'danger')
        return redirect(url_for('authorities'))

    authority = EvaluationAuthority.query.get_or_404(auth_id)
    db.session.delete(authority)
    db.session.commit()
    flash('تم حذف الجهة بنجاح', 'success')
    return redirect(url_for('authorities'))

# تعديل المنطقة (Location)
from flask import request, redirect, url_for, flash, render_template
from flask_login import login_required, current_user
from sqlalchemy.orm import joinedload

# افترض أن لديك هذه النماذج:
# Location (المنطقة)
# Site (الموقع الفرعي)
# Place (المكان)

@app.route('/locations', methods=['GET', 'POST'])
@login_required
def locations():
    if current_user.role != 'admin':
        flash('غير مصرح لك', 'danger')
        return redirect(url_for('dashboard'))

    # تحديث خيارات اختيار المواقع والمناطق لنماذج الإدخال
    form_region = RegionForm(prefix='region')
    form_site = SiteForm(prefix='site')
    form_place = PlaceForm(prefix='place')

    form_site.region_id.choices = [(r.id, r.name) for r in Location.query.order_by(Location.name).all()]
    form_place.site_id.choices = [(s.id, s.name) for s in Site.query.order_by(Site.name).all()]

    # *** إضافة مناطق، مواقع، أماكن ***
    if request.method == 'POST':
        # إضافة منطقة
        if 'submit_region' in request.form and form_region.validate():
            new_region = Location(name=form_region.name.data)
            db.session.add(new_region)
            db.session.commit()
            flash('تمت إضافة المنطقة بنجاح', 'success')
            return redirect(url_for('locations'))

        # إضافة موقع
        elif 'submit_site' in request.form and form_site.validate():
            new_site = Site(name=form_site.name.data, region_id=form_site.region_id.data)
            db.session.add(new_site)
            db.session.commit()
            flash('تمت إضافة الموقع بنجاح', 'success')
            return redirect(url_for('locations'))

        # إضافة مكان
        elif 'submit_place' in request.form and form_place.validate():
            new_place = Place(name=form_place.name.data, site_id=form_place.site_id.data)
            db.session.add(new_place)
            db.session.commit()
            flash('تمت إضافة المكان بنجاح', 'success')
            return redirect(url_for('locations'))

    # جلب الهيكل مع العلاقات
    locations = Location.query.options(
        joinedload(Location.sites).joinedload(Site.places)
    ).order_by(Location.name).all()

    return render_template('admin/locations.html',
                           form_region=form_region,
                           form_site=form_site,
                           form_place=form_place,
                           locations=locations)


# --- تعديل وحذف المناطق (Locations) ---
@app.route('/locations/edit/location/<int:location_id>', methods=['POST'])
@login_required
def edit_location(location_id):
    if current_user.role != 'admin':
        flash('غير مصرح لك', 'danger')
        return redirect(url_for('locations'))

    location = Location.query.get_or_404(location_id)
    new_name = request.form.get('new_name')
    if new_name:
        location.name = new_name
        db.session.commit()
        flash('تم تعديل اسم المنطقة بنجاح', 'success')
    else:
        flash('اسم المنطقة لا يمكن أن يكون فارغاً', 'warning')
    return redirect(url_for('locations'))


@app.route('/locations/delete/location/<int:location_id>', methods=['POST'])
@login_required
def delete_location(location_id):
    if current_user.role != 'admin':
        flash('غير مصرح لك', 'danger')
        return redirect(url_for('locations'))

    location = Location.query.get_or_404(location_id)
    children_count = Site.query.filter_by(region_id=location_id).count()
    if children_count > 0:
        flash('لا يمكن حذف المنطقة لأنها تحتوي على مواقع فرعية', 'danger')
    else:
        db.session.delete(location)
        db.session.commit()
        flash('تم حذف المنطقة بنجاح', 'success')
    return redirect(url_for('locations'))


# --- تعديل وحذف المواقع (Sites) ---
@app.route('/locations/edit/site/<int:site_id>', methods=['POST'])
@login_required
def edit_site(site_id):
    if current_user.role != 'admin':
        flash('غير مصرح لك', 'danger')
        return redirect(url_for('locations'))

    site = Site.query.get_or_404(site_id)
    new_name = request.form.get('new_name')
    if new_name:
        site.name = new_name
        db.session.commit()
        flash('تم تعديل اسم الموقع بنجاح', 'success')
    else:
        flash('اسم الموقع لا يمكن أن يكون فارغاً', 'warning')
    return redirect(url_for('locations'))


@app.route('/locations/delete/site/<int:site_id>', methods=['POST'])
@login_required
def delete_site(site_id):
    if current_user.role != 'admin':
        flash('غير مصرح لك', 'danger')
        return redirect(url_for('locations'))

    site = Site.query.get_or_404(site_id)
    children_count = Place.query.filter_by(site_id=site_id).count()
    if children_count > 0:
        flash('لا يمكن حذف الموقع لأنه يحتوي على أماكن فرعية', 'danger')
    else:
        db.session.delete(site)
        db.session.commit()
        flash('تم حذف الموقع بنجاح', 'success')
    return redirect(url_for('locations'))


# --- تعديل وحذف الأماكن (Places) ---
@app.route('/locations/edit/place/<int:place_id>', methods=['POST'])
@login_required
def edit_place(place_id):
    if current_user.role != 'admin':
        flash('غير مصرح لك', 'danger')
        return redirect(url_for('locations'))

    place = Place.query.get_or_404(place_id)
    new_name = request.form.get('new_name')
    if new_name:
        place.name = new_name
        db.session.commit()
        flash('تم تعديل اسم المكان بنجاح', 'success')
    else:
        flash('اسم المكان لا يمكن أن يكون فارغاً', 'warning')
    return redirect(url_for('locations'))


@app.route('/locations/delete/place/<int:place_id>', methods=['POST'])
@login_required
def delete_place(place_id):
    if current_user.role != 'admin':
        flash('غير مصرح لك', 'danger')
        return redirect(url_for('locations'))

    place = Place.query.get_or_404(place_id)
    db.session.delete(place)
    db.session.commit()
    flash('تم حذف المكان بنجاح', 'success')
    return redirect(url_for('locations'))

@app.route('/hierarchy')
def hierarchy():
    locations = Location.query.all()
    return render_template('admin/hierarchy.html', locations=locations)

from threading import Lock

db_lock = Lock()

@app.route("/criteria", methods=["GET", "POST"])
@login_required
def criteria():
    if current_user.role != 'admin':
        flash('غير مصرح لك', 'danger')
        return redirect(url_for('dashboard'))

    from sqlalchemy.orm import joinedload
    criteria_list = (
        Criterion.query.options(
            joinedload(Criterion.place).joinedload(Place.site).joinedload(Site.location),
            joinedload(Criterion.authority)
        )
        .order_by(Criterion.place_id)
        .all()
    )

    locations = Location.query.order_by(Location.name).all()
    authorities = EvaluationAuthority.query.order_by(EvaluationAuthority.name).all()

    if request.method == "POST":
        place_id = request.form.get("place_id")
        name = request.form.get("name")
        min_score = request.form.get("min_score")
        max_score = request.form.get("max_score")
        authority_id = request.form.get("authority_id")
        add_type = request.form.get("add_type")  # الخيار: single أو all_similar

        if not (place_id and name and min_score and max_score and authority_id and add_type):
            flash("يجب تعبئة جميع الحقول المطلوبة", "danger")
            return redirect(url_for("criteria"))

        try:
            min_score = float(min_score)
            max_score = float(max_score)
        except ValueError:
            flash("يجب أن تكون الدرجات أرقاماً صحيحة أو عشرية", "danger")
            return redirect(url_for("criteria"))

        with db_lock:
            try:
                place = Place.query.get(int(place_id))

                if add_type == "single":
                    # إضافة للمكان المختار فقط
                    new_criterion = Criterion(
                        name=name,
                        place_id=int(place_id),
                        min_score=min_score,
                        max_score=max_score,
                        authority_id=int(authority_id)
                    )
                    db.session.add(new_criterion)
                    db.session.commit()
                    flash("تمت إضافة المعيار للمكان المحدد فقط.", "success")

                elif add_type == "all_similar":
                    # إضافة لجميع الأماكن المشابهة
                    similar_places = Place.query.filter_by(name=place.name).all()
                    added = 0
                    for p in similar_places:
                        exists = Criterion.query.filter_by(place_id=p.id, name=name).first()
                        if not exists:
                            db.session.add(
                                Criterion(
                                    name=name,
                                    place_id=p.id,
                                    min_score=min_score,
                                    max_score=max_score,
                                    authority_id=int(authority_id)
                                )
                            )
                            added += 1
                    db.session.commit()
                    flash(f"تمت إضافة المعيار لجميع الأماكن المشابهة ({added} مكان).", "success")

            except Exception as e:
                db.session.rollback()
                flash(f"حدث خطأ أثناء الإضافة: {e}", "danger")
            finally:
                db.session.close()

        return redirect(url_for("criteria"))

    return render_template(
        "admin/criteria.html",
        locations=locations,
        authorities=authorities,
        criteria=criteria_list
    )

@app.route('/criteria/edit/<int:criterion_id>', methods=['GET', 'POST'])
@login_required
def edit_criterion(criterion_id):
    if current_user.role != 'admin':
        flash('غير مصرح لك', 'danger')
        return redirect(url_for('dashboard'))

    criterion = Criterion.query.get_or_404(criterion_id)
    locations = Location.query.order_by(Location.name).all()
    authorities = EvaluationAuthority.query.order_by(EvaluationAuthority.name).all()

    if request.method == 'POST':
        name = request.form.get("name")
        min_score = request.form.get("min_score")
        max_score = request.form.get("max_score")
        place_id = request.form.get("place_id")
        authority_id = request.form.get("authority_id")

        if not (place_id and name and min_score and max_score and authority_id):
            flash("يجب تعبئة جميع الحقول المطلوبة", "danger")
        else:
            try:
                min_score = float(min_score)
                max_score = float(max_score)
            except ValueError:
                flash("يجب أن تكون الدرجات أرقاماً صحيحة أو عشرية", "danger")
                return redirect(url_for('edit_criterion', criterion_id=criterion_id))

            criterion.name = name
            criterion.min_score = min_score
            criterion.max_score = max_score
            criterion.place_id = int(place_id)
            criterion.authority_id = int(authority_id)

            db.session.commit()
            flash("تم تعديل المعيار بنجاح", "success")
            return redirect(url_for('criteria'))

    return render_template('admin/edit_criterion.html', criterion=criterion, locations=locations,
                           authorities=authorities)


@app.route('/criteria/delete/<int:criterion_id>', methods=['POST'])
@login_required
def delete_criterion(criterion_id):
    if current_user.role != 'admin':
        flash('غير مصرح لك', 'danger')
        return redirect(url_for('dashboard'))

    criterion = Criterion.query.get_or_404(criterion_id)
    db.session.delete(criterion)
    db.session.commit()
    flash('تم حذف المعيار بنجاح', 'success')
    return redirect(url_for('criteria'))

@app.route('/get_sites/<int:region_id>')
@login_required
def get_sites(region_id):
    sites = Site.query.filter_by(region_id=region_id).order_by(Site.name).all()
    return jsonify([{'id': s.id, 'name': s.name} for s in sites])

@app.route('/get_places/<int:site_id>')
@login_required
def get_places(site_id):
    places = Place.query.filter_by(site_id=site_id).order_by(Place.name).all()
    return jsonify([{'id': p.id, 'name': p.name} for p in places])


@app.route('/get_criteria/<int:place_id>')
@login_required
def get_criteria(place_id):
    criteria = Criterion.query.filter_by(place_id=place_id).all()
    result = []
    for c in criteria:
        result.append({
            "id": c.id,
            "name": c.name,
            "min_score": c.min_score,
            "max_score": c.max_score,
            "authority_name": c.authority.name if c.authority else "-"
        })
    return jsonify(result)

@app.route('/criteria/hierarchy')
@login_required
def criteria_hierarchy():
    if current_user.role != 'admin':
        flash('غير مصرح لك', 'danger')
        return redirect(url_for('dashboard'))

    regions = Location.query.options(
        joinedload(Location.sites).joinedload(Site.places).joinedload(Place.criteria)
    ).all()

    return render_template('admin/criteria_hierarchy.html', regions=regions)

# ---------------------
# صفحة التقييمات
# ---------------------
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Evaluation, EvaluationDetail,ActionPlan, Location, Site, Place, Criterion, EvaluationAuthority
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from models import db, Evaluation, EvaluationDetail, Location, Site, Place

# ---------------------
# دالة لجلب الأماكن + المعايير لموقع محدد
# ---------------------
@app.route('/get_site_criteria/<int:site_id>')
@login_required
def get_site_criteria(site_id):
    # جلب الأماكن المرتبطة بالموقع
    places = Place.query.filter_by(site_id=site_id).order_by(Place.name).all()
    result = []

    for p in places:
        criteria = Criterion.query.filter_by(place_id=p.id).all()
        criteria_data = []
        for c in criteria:
            criteria_data.append({
                "id": c.id,
                "name": c.name,
                "min_score": c.min_score,
                "max_score": c.max_score,
                "authority_id": c.authority_id,
                "authority_name": c.authority.name if c.authority else "-"
            })

        result.append({
            "place_id": p.id,
            "place_name": p.name,
            "criteria": criteria_data
        })

    return jsonify(result)


# ---------------------
# صفحة التقييمات (مع دعم place_id لكل معيار)
# ---------------------
# ---------------------
# صفحة التقييمات (مع دعم place_id لكل معيار)
# ---------------------
@app.route('/evaluations', methods=['GET', 'POST'])
@login_required
def evaluations():
    # ✅ جلب المناطق المرتبطة بالمستخدم (واحدة أو أكثر)
    regions = current_user.regions
    sites = Site.query.filter(Site.region_id.in_([r.id for r in current_user.regions])).order_by(Site.name).all()
    places = Place.query.join(Site).filter(Site.region_id.in_([r.id for r in current_user.regions])).order_by(Place.name).all()

    from datetime import datetime, date

    if request.method == 'POST':
        region_id = request.form.get('region_id')
        site_id = request.form.get('site_id')
        notes_overall = request.form.get('notes')

        criteria_ids = request.form.getlist('criteria_ids[]')
        scores = request.form.getlist('score[]')
        authorities = request.form.getlist('authority_ids[]')
        place_ids = request.form.getlist('place_ids[]')
        notes_list = request.form.getlist('criterion_notes[]')

        if not (criteria_ids and scores and place_ids):
            flash('لا توجد بيانات للتقييم', 'danger')
            return redirect(url_for('evaluations'))

        today = date.today()  # ← الاعتماد على تاريخ الجهاز المحلي

        # ✅ التحقق من وجود تقييم سابق لنفس المنطقة + الموقع + المكان في نفس اليوم
        for place_id in place_ids:
            existing_evaluation = Evaluation.query.join(EvaluationDetail).filter(
                Evaluation.region_id == int(region_id),
                Evaluation.site_id == site_id,
                EvaluationDetail.place_id == int(place_id),
                db.func.date(Evaluation.date) == today
            ).first()

            if existing_evaluation:
                flash(f'تم بالفعل تقييم المنطقة والموقع والمكان المحدد لهذا اليوم (Place ID: {place_id})', 'warning')
                return redirect(url_for('evaluations'))

        try:
            evaluation = Evaluation(
                user_id=current_user.id,
                region_id=int(region_id),
                site_id=int(site_id),
                notes=notes_overall,
                date=datetime.now()  # ← الاعتماد على التاريخ المحلي
            )
            db.session.add(evaluation)
            db.session.flush()

            for i in range(len(criteria_ids)):
                detail = EvaluationDetail(
                    evaluation_id=evaluation.id,
                    criterion_id=int(criteria_ids[i]),
                    score=float(scores[i]),
                    user_id=current_user.id,
                    authority_id=int(authorities[i]) if authorities[i] else None,
                    place_id=int(place_ids[i]) if place_ids[i] else None,
                    note=notes_list[i].strip() if notes_list and notes_list[i].strip() else None
                )
                db.session.add(detail)

            db.session.commit()
            flash('تم حفظ التقييم والمعايير بنجاح', 'success')
            return redirect(url_for('evaluations'))

        except Exception as e:
            db.session.rollback()
            flash(f"حدث خطأ أثناء الحفظ: {e}", "danger")

    # ✅ جلب التقييمات الخاصة بكل المناطق المرتبطة بالمستخدم
    evaluations_list = Evaluation.query.filter(
        Evaluation.region_id.in_([r.id for r in current_user.regions])
    ).order_by(Evaluation.date.desc()).all()

    return render_template(
        'user/evaluations.html',
        regions=regions,
        sites=sites,
        places=places,
        evaluations=evaluations_list
    )


@app.route('/evaluation_form', methods=['GET'])
@login_required
def evaluation_form():
    user = current_user

    # ✅ جلب كل المناطق الخاصة بالمستخدم مع المواقع والأماكن والمعايير
    regions = Location.query.options(
        joinedload(Location.sites)
        .joinedload(Site.places)
        .joinedload(Place.criteria)
        .joinedload(Criterion.authority)
    ).filter(Location.id.in_([r.id for r in user.regions])).all()

    if not regions:
        flash("لا توجد بيانات للمناطق المرتبطة بالمستخدم.", "warning")
        return render_template('user/evaluation_form.html', user=user, evaluation_details=[])

    evaluation_details = []

    for region in regions:
        for site in region.sites:
            for place in site.places:
                for criterion in place.criteria:
                    evaluation_details.append({
                        "region_name": region.name,
                        "site_name": site.name,
                        "place_id": place.id,
                        "place_name": place.name,
                        "criterion_id": criterion.id,
                        "criterion_name": criterion.name,
                        "min_score": criterion.min_score,
                        "max_score": criterion.max_score,
                        "authority_name": criterion.authority.name if criterion.authority else "-"
                    })

    return render_template(
        'evaluation_form_pdf.html',
        user=user,
        evaluation_details=evaluation_details
    )

from flask import render_template, request
from models import User, Evaluation  # استبدل Evaluation باسم جدول التقييمات لديك
from flask_login import login_required
@app.route("/select_user", methods=["GET", "POST"])
@login_required
def select_user():
    from flask_login import current_user

    selected_user = current_user  # المستخدم الحالي
    evaluation_details = []

    # استدعاء جميع المستخدمين (يمكنك إزالة هذا إذا المستخدم سيشاهد فقط بياناته)
    users_list = User.query.order_by(User.fullname).all()

    # جلب بيانات التقييم الخاصة بالمستخدم الحالي مباشرة
    evaluation_details = Evaluation.query.filter_by(user_id=selected_user.id).all()

    return render_template(
        'admin/select_user.html',
        users=users_list,
        selected_user=selected_user,
        evaluation_details=evaluation_details
    )

@app.route("/generate_user_pdf/<int:user_id>")
def generate_user_pdf(user_id):
    user = User.query.get(user_id)
    if not user:
        flash("المستخدم غير موجود", "danger")
        return redirect(url_for('evaluation_form'))

    # جلب جميع المناطق المرتبطة بالمستخدم
    regions = Location.query.options(
        joinedload(Location.sites)
        .joinedload(Site.places)
        .joinedload(Place.criteria)
        .joinedload(Criterion.authority)
    ).filter(Location.users.any(id=user.id)).all()  # كل المناطق التي يرتبط بها المستخدم

    if not regions:
        flash("لا توجد بيانات مرتبطة بالمستخدم.", "warning")
        return redirect(url_for('evaluation_form'))

    evaluation_details = []
    for region in regions:
        for site in region.sites:
            for place in site.places:
                for criterion in place.criteria:
                    evaluation_details.append({
                        "region_name": region.name,
                        "site_name": site.name,
                        "place_id": place.id,
                        "place_name": place.name,
                        "criterion_id": criterion.id,
                        "criterion_name": criterion.name,
                        "min_score": criterion.min_score,
                        "max_score": criterion.max_score,
                        "authority_name": criterion.authority.name if criterion.authority else "-"
                    })

    rendered = render_template("user/evaluation_form_pdf.html", user=user, evaluation_details=evaluation_details)

    import pdfkit
    path_wkhtmltopdf = r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
    config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)

    options = {
        'enable-local-file-access': '',
        'no-stop-slow-scripts': '',
    }

    pdf = pdfkit.from_string(rendered, False, configuration=config, options=options)

    from flask import make_response
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename={user.username}_evaluation.pdf'
    return response


# API Endpoints
# ---------------------


from flask_login import login_required, current_user
from datetime import datetime, timedelta
from sqlalchemy import func
from models import db, User, Location, Site, Place, Criterion, Evaluation, EvaluationDetail

@app.route('/reports')
@login_required
def reports():
    # الفلاتر
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    region_id = request.args.get('region_id')
    user_id = request.args.get('user_id')

    start_date = datetime.strptime(start_date_str, '%Y-%m-%d') if start_date_str else datetime.today()
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d') if end_date_str else datetime.today()

    # كل المستخدمين باستثناء المشرف
    users = User.query.filter(User.role != 'admin', User.active == True).all()

    locations = Location.query.all()

    # توليد قائمة الأيام ضمن الفترة
    dates = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]

    summary_list = []
    evaluations_list = []

    for user in users:
        # المستخدم مرتبط فقط بالمنطقة الخاصة به
        user_regions = user.regions  # العلاقة many-to-many

        for region in user_regions:
            # تطبيق فلترة إذا اختيرت
            if region_id and int(region_id) != region.id:
                continue
            if user_id and int(user_id) != user.id:
                continue

            # إجمالي درجات المنطقة وعدد المعايير
            total_region_score = db.session.query(func.sum(Criterion.max_score))\
                .join(Place).join(Site)\
                .filter(Site.region_id == region.id).scalar() or 0

            total_criteria_count = db.session.query(Criterion.id)\
                .join(Place).join(Site)\
                .filter(Site.region_id == region.id).count()

            # إجمالي درجات المستخدم وعدد المعايير المقيمة في الفترة
            user_total_score = db.session.query(func.sum(EvaluationDetail.score))\
                .join(Evaluation, Evaluation.id == EvaluationDetail.evaluation_id)\
                .filter(
                    Evaluation.user_id == user.id,
                    Evaluation.region_id == region.id,
                    func.date(Evaluation.date) >= start_date.date(),
                    func.date(Evaluation.date) <= end_date.date()
                ).scalar() or 0

            user_evaluated_criteria = db.session.query(EvaluationDetail.id)\
                .join(Evaluation, Evaluation.id == EvaluationDetail.evaluation_id)\
                .filter(
                    Evaluation.user_id == user.id,
                    Evaluation.region_id == region.id,
                    func.date(Evaluation.date) >= start_date.date(),
                    func.date(Evaluation.date) <= end_date.date()
                ).count()

            # حساب النسبة في الملخص
            percent_value = (user_evaluated_criteria / total_criteria_count * 100) if total_criteria_count else 0
            percent = f"{percent_value:.2f}%"


            # إضافة الملخص
            summary_list.append({
                "region": region.name,
                "user": user.fullname,
                "score": user_total_score if user_total_score > 0 else "لم يقيم",
                "percent": percent,
                "total_criteria": total_criteria_count,
                "evaluated_criteria": user_evaluated_criteria
            })

            # التفاصيل اليومية لكل يوم ضمن الفترة
            for date in dates:
                daily_score = db.session.query(func.sum(EvaluationDetail.score))\
                    .join(Evaluation, Evaluation.id == EvaluationDetail.evaluation_id)\
                    .filter(
                        Evaluation.user_id == user.id,
                        Evaluation.region_id == region.id,
                        func.date(Evaluation.date) == date.date()
                    ).scalar()

                daily_evaluated_criteria = db.session.query(EvaluationDetail.id)\
                    .join(Evaluation, Evaluation.id == EvaluationDetail.evaluation_id)\
                    .filter(
                        Evaluation.user_id == user.id,
                        Evaluation.region_id == region.id,
                        func.date(Evaluation.date) == date.date()
                    ).count()

                # حساب النسبة في التفاصيل اليومية
                daily_percent_value = (daily_evaluated_criteria / total_criteria_count * 100) if total_criteria_count else 0
                daily_percent = f"{daily_percent_value:.2f}%"

                evaluations_list.append({
                    "date": date.strftime('%Y-%m-%d'),
                    "region": region.name,
                    "user": user.fullname,
                    "score": daily_score if daily_score else "لم يقيم",
                    "percent": daily_percent,
                    "total_criteria": total_criteria_count,
                    "evaluated_criteria": daily_evaluated_criteria
                })

    return render_template(
        'admin/reports.html',
        evaluations=evaluations_list,
        summary=summary_list,
        users=users,
        locations=locations,
        selected_region_id=int(region_id) if region_id else None,
        selected_user_id=int(user_id) if user_id else None,
        start_date=start_date_str,
        end_date=end_date_str
    )


from collections import defaultdict
from datetime import datetime
from flask import render_template, request
from sqlalchemy import func
from flask_login import current_user
from models import EvaluationDetail, Evaluation, Criterion, User, Place, Site, Location
from sqlalchemy.orm import joinedload

@app.route('/report_summary')
def report_summary():
    date_from_str = request.args.get('start_date')
    date_to_str = request.args.get('end_date')

    date_exact_str = request.args.get('date_exact')

    today = datetime.now().date()

    # ✅ هنا التغيير
    date_exact = datetime.strptime(date_exact_str, '%Y-%m-%d').date() if date_exact_str else None
    date_from = datetime.strptime(date_from_str, '%Y-%m-%d').date() if date_from_str else None
    date_to = datetime.strptime(date_to_str, '%Y-%m-%d').date() if date_to_str else None

    # إذا ما فيه أي فلترة → اعرض اليوم فقط
    if not (date_from or date_to or date_exact):
        date_exact = today

    query = (
        EvaluationDetail.query
        .join(Evaluation, EvaluationDetail.evaluation_id == Evaluation.id)
        .join(Criterion, EvaluationDetail.criterion_id == Criterion.id)
        .join(User, EvaluationDetail.user_id == User.id)
        .options(
            joinedload(EvaluationDetail.evaluation).joinedload(Evaluation.region),
            joinedload(EvaluationDetail.evaluation).joinedload(Evaluation.site),
            joinedload(EvaluationDetail.evaluation).joinedload(Evaluation.place),
            joinedload(EvaluationDetail.criterion).joinedload(Criterion.authority),
            joinedload(EvaluationDetail.user)
        )
    )

    # فلترة المستخدم العادي حسب منطقته
    if not getattr(current_user, 'is_admin', False) and getattr(current_user, 'region_id', None):
        query = query.filter(Evaluation.region_id == current_user.region_id)

    # ✅ فلترة التاريخ بشكل صحيح
    if date_exact:
        query = query.filter(func.date(Evaluation.date) == date_exact)
    if date_from:
        query = query.filter(func.date(Evaluation.date) >= date_from)
    if date_to:
        query = query.filter(func.date(Evaluation.date) <= date_to)

    evaluation_details = query.order_by(EvaluationDetail.id.desc()).all()
    grouped_data = []

    for detail in evaluation_details:
        # الدرجة النهائية هي score نفسه بعد الإغلاق
        actual_score = detail.score or 0

        # تأكد أن الدرجة بين 1 و 10
        if actual_score < 1:
            actual_score = 1
        elif actual_score > 10:
            actual_score = 10

        place_name = (detail.place.name if detail.place
                      else detail.evaluation.place.name if detail.evaluation and detail.evaluation.place
        else "غير محدد")

        grouped_data.append({
            "region": detail.evaluation.region.name if detail.evaluation and detail.evaluation.region else "غير محدد",
            "site": detail.evaluation.site.name if detail.evaluation and detail.evaluation.site else "غير محدد",
            "place": place_name,
            "criterion": detail.criterion.name if detail.criterion else "غير محدد",
            "user": detail.user.fullname if detail.user else "غير محدد",
            "date": detail.evaluation.date.strftime(
                '%Y-%m-%d') if detail.evaluation and detail.evaluation.date else "-",
            "score": float(actual_score),
            "note": detail.note or '',
            "authority": detail.criterion.authority.name if detail.criterion and detail.criterion.authority else "غير محدد"
        })

    return render_template(
        'admin/report_summary.html',
        grouped_data=grouped_data,
        date_from=date_from_str,
        date_to=date_to_str,
        date_exact=date_exact_str or today.strftime('%Y-%m-%d')
    )
    # بعد تعديل الدرجة
    detail.score = new_score
    db.session.commit()
    # ثم عمل refresh للكائن (اختياري لكنه مفيد لضمان ظهور التغيير فورًا)
    db.session.refresh(detail)


from flask import render_template, request
from flask_login import current_user
from sqlalchemy.orm import joinedload
from sqlalchemy import func
from datetime import datetime
from models import EvaluationDetail, Evaluation, Criterion, User
@app.route('/responsibility_report', methods=['GET'])
def responsibility_report():
    date_from_str = request.args.get('start_date')
    date_to_str = request.args.get('end_date')
    date_exact_str = request.args.get('date_exact')
    selected_region_id = request.args.get('region_id')
    selected_user_id = request.args.get('user_id')

    today = datetime.now().date()

    # تحويل التواريخ
    date_exact = datetime.strptime(date_exact_str, '%Y-%m-%d').date() if date_exact_str else today
    date_from = datetime.strptime(date_from_str, '%Y-%m-%d').date() if date_from_str else None
    date_to = datetime.strptime(date_to_str, '%Y-%m-%d').date() if date_to_str else None

    query = (
        EvaluationDetail.query
        .join(Evaluation, EvaluationDetail.evaluation_id == Evaluation.id)
        .join(Criterion, EvaluationDetail.criterion_id == Criterion.id)
        .join(User, EvaluationDetail.user_id == User.id)
        .options(
            joinedload(EvaluationDetail.evaluation).joinedload(Evaluation.region),
            joinedload(EvaluationDetail.evaluation).joinedload(Evaluation.site),
            joinedload(EvaluationDetail.evaluation).joinedload(Evaluation.place),
            joinedload(EvaluationDetail.criterion).joinedload(Criterion.authority),
            joinedload(EvaluationDetail.user),
            joinedload(EvaluationDetail.action_plans)
        )
    )

    # فلترة المستخدم العادي حسب منطقته
    if not getattr(current_user, 'is_admin', False) and getattr(current_user, 'region_id', None):
        query = query.filter(Evaluation.region_id == current_user.region_id)

    # فلترة حسب المنطقة والمستخدم والتواريخ
    if selected_region_id:
        query = query.filter(Evaluation.region_id == int(selected_region_id))
    if selected_user_id:
        query = query.filter(EvaluationDetail.user_id == int(selected_user_id))
    if date_exact:
        query = query.filter(func.date(Evaluation.date) == date_exact)
    if date_from:
        query = query.filter(func.date(Evaluation.date) >= date_from)
    if date_to:
        query = query.filter(func.date(Evaluation.date) <= date_to)

    evaluation_details = query.order_by(EvaluationDetail.id.desc()).all()

    # إضافة actual_score لكل كائن
    for detail in evaluation_details:
        # استخدام الدرجة مباشرة بعد الاستبدال
        actual_score = detail.score or 0  # لا تجمع أي شيء من action_plans

    for detail in evaluation_details:
        base_score = detail.score or 0

    # تجميع حسب جهة المسؤولية
    grouped_by_authority = {}
    stats = {}
    ai_suggestions = {}

    for detail in evaluation_details:
        authority = detail.criterion.authority.name if detail.criterion and detail.criterion.authority else "غير محدد"
        grouped_by_authority.setdefault(authority, []).append(detail)

    for authority, details in grouped_by_authority.items():
        total_count = len(details)
        # استخدم score مباشرة
        avg_score = sum(d.score for d in details) / total_count if total_count > 0 else 0
        stats[authority] = {"total_count": total_count, "avg_score": avg_score}
        ai_suggestions[authority] = "تحليل تلقائي أو مقترحات بالذكاء الاصطناعي."

    users = User.query.all()
    locations = Location.query.all()

    return render_template(
        'admin/responsibility_report.html',
        grouped_by_authority=grouped_by_authority,
        stats=stats,
        ai_suggestions=ai_suggestions,
        users=users,
        locations=locations,
        selected_user_id=int(selected_user_id) if selected_user_id else None,
        selected_region_id=int(selected_region_id) if selected_region_id else None,
        start_date=date_from_str,
        end_date=date_to_str,
        date_exact=date_exact_str or today.strftime('%Y-%m-%d')
    )


from openai import OpenAI

# ---------------- OpenAI ----------------


# ---------------- Routes ----------------
from flask import render_template, flash
from openai import OpenAI, OpenAIError
from openai import OpenAI

OPENAI_API_KEY = "sk-XXXXXXXXXXXXXXXXXXXXXXXX"  # المفتاح هنا مباشرة
client = OpenAI(api_key=OPENAI_API_KEY)

import os
from openai import OpenAI
import os
print(os.getenv("OPENAI_API_KEY"))
import os
print(os.getenv("OPENAI_API_KEY"))

from flask import request, jsonify
from datetime import datetime
from models import ActionPlan  # استبدل بالمسار الصحيح لنموذجك

from flask import Flask, render_template, request, jsonify
from datetime import datetime
from models import db, ActionPlan  # استبدل بالمسار الصحيح لنموذجك

from sqlalchemy.orm import joinedload
from sqlalchemy.orm import joinedload

from sqlalchemy.orm import joinedload

from sqlalchemy.orm import joinedload, contains_eager
from sqlalchemy.orm import joinedload
from sqlalchemy import func

from collections import Counter
from collections import Counter
from flask import render_template
from sqlalchemy.orm import joinedload

from collections import Counter
from flask import render_template
from sqlalchemy.orm import joinedload


from collections import Counter
from flask import render_template
from sqlalchemy.orm import joinedload

from collections import Counter
from flask import render_template
from sqlalchemy.orm import joinedload

@app.route('/action_plans')
def action_plans():
    # جلب جميع تفاصيل التقييم مع الربط بالعلاقات
    evaluation_detail = (
        EvaluationDetail.query
        .options(
            joinedload(EvaluationDetail.evaluation).joinedload(Evaluation.region),
            joinedload(EvaluationDetail.evaluation).joinedload(Evaluation.site),
            joinedload(EvaluationDetail.place),
            joinedload(EvaluationDetail.criterion),
            joinedload(EvaluationDetail.action_plans)
        )
        .filter(EvaluationDetail.note.isnot(None))
        .all()
    )

    # تحضير عداد المعايير مرتبط بالمكان والموقع والمنطقة
    criterion_place_site_region_pairs = [
        (
            plan.criterion.name,
            plan.place.name if plan.place else '-',
            plan.evaluation.site.name if plan.evaluation and plan.evaluation.site else '-',
            plan.evaluation.region.name if plan.evaluation and plan.evaluation.region else '-'
        )
        for plan in evaluation_detail if plan.criterion
    ]

    # عد التكرارات لكل معيار-مكان-موقع-منطقة
    criterion_counts = Counter(criterion_place_site_region_pairs)

    # أكثر 5 معايير تكرارًا (مرتبة حسب العدد)
    top_criteria = []
    for (criterion_name, place_name, site_name, region_name), count in criterion_counts.most_common(5):
        top_criteria.append({
            "name": f"{criterion_name} ({region_name} / {site_name} / {place_name})",
            "count": count,
            "info": "-"  # نضيف المفتاح مباشرة لتجنب Undefined
        })

    # إعادة العدد لكل خطة عمل لتظهر في العمود "عدد التكرار" في الجدول
    criterion_count_lookup = {}
    for plan in evaluation_detail:
        if plan.criterion:
            key = (
                plan.criterion.name,
                plan.place.name if plan.place else '-',
                plan.evaluation.site.name if plan.evaluation and plan.evaluation.site else '-',
                plan.evaluation.region.name if plan.evaluation and plan.evaluation.region else '-'
            )
            criterion_count_lookup[key] = criterion_counts.get(key, 0)

    return render_template(
        'admin/action_plans.html',
        action_plans=evaluation_detail,
        criterion_counts=criterion_count_lookup,  # لعرض عدد التكرار لكل صف
        top_criteria=top_criteria
    )


@app.route('/add_note', methods=['POST'])
def add_note():
    evaluation_id = request.form['evaluation_detail_id']
    note = request.form['note']
    action_plan = generate_action_plan(note)

    new_plan = ActionPlan(
        evaluation_detail_id=evaluation_id,
        note=note,
        action_plan=action_plan
    )
    db.session.add(new_plan)
    db.session.commit()
    return redirect(url_for('action_plans'))

@app.route('/close_note/<int:note_id>', methods=['POST'])
def close_note(note_id):
    try:
        evaluation_detail = EvaluationDetail.query.get(note_id)
        if not evaluation_detail:
            return "الملاحظة غير موجودة", 404

        closed_date_str = request.form.get('closed_date')
        improvement_score = request.form.get('improvement_score')
        closing_note = request.form.get('closing_note')  # ملاحظات الإغلاق

        if not closed_date_str or improvement_score is None:
            return "الرجاء تحديد تاريخ الإغلاق والدرجة المحسنة", 400

        closed_date = datetime.strptime(closed_date_str, "%Y-%m-%d").date()
        improvement_score = float(improvement_score)

        # إنشاء أو تحديث ActionPlan
        if evaluation_detail.action_plans:
            action_plan = evaluation_detail.action_plans[0]
        else:
            action_plan = ActionPlan(evaluation_detail_id=evaluation_detail.id)
            db.session.add(action_plan)

        action_plan.closed = True
        action_plan.closed_date = closed_date
        action_plan.improvement_score = improvement_score
        action_plan.closing_note = closing_note

        # استبدال الدرجة القديمة بالدرجة الجديدة مع ضبط الحد بين 1 و10
        evaluation_detail.score = min(max(improvement_score, 1), 10)

        db.session.commit()
        return redirect(url_for('action_plans'))

    except Exception as e:
        db.session.rollback()
        return str(e), 400


@app.route('/health')
def health_check():
    try:
        db.session.execute('SELECT 1')
        database_status = 'connected'
    except Exception as e:
        database_status = f'error: {str(e)}'

    return jsonify({
        'status': 'healthy',
        'database': database_status,
        'timestamp': datetime.now().isoformat()
    })

def initialize_database():
    """تهيئة قاعدة البيانات وإنشاء المستخدم الافتراضي"""
    with app.app_context():
        try:
            # إنشاء الجداول
            db.create_all()

            # إنشاء المستخدم الافتراضي إذا لم يكن موجوداً
            if not User.query.filter_by(username='admin').first():
                admin = User(
                    fullname='المشرف الرئيسي',
                    username='admin',
                    email='admin@system.com',
                    role='admin',
                    active=True
                )
                admin.set_password('123456')
                db.session.add(admin)
                db.session.commit()
                print("✅ تم إنشاء المستخدم الافتراضي: admin / 123456")

            print("✅ تم تهيئة قاعدة البيانات بنجاح")

        except Exception as e:
            print(f"❌ خطأ في تهيئة قاعدة البيانات: {e}")
            db.session.rollback()


# استدعاء التهيئة عند التشغيل
initialize_database()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)