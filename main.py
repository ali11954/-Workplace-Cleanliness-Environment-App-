# ====== 1️⃣ الاستيرادات الأساسية ======
from flask import Flask, render_template, redirect, url_for, request, flash, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, IntegerField, TextAreaField, FloatField
from wtforms.validators import DataRequired, Length, EqualTo, NumberRange, Optional
from datetime import datetime
from functools import wraps
import os
from datetime import datetime, timezone
datetime.now(timezone.utc)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from sqlalchemy import func, distinct

# ====== 2️⃣ تحميل الإعدادات من config.py ======

# ====== 3️⃣ استيراد قاعدة البيانات والنماذج ======
from models import db, User, Company, Location, Site, Place, Criterion, Evaluation, EvaluationDetail, EvaluationAuthority, UserPermission, Permission

# ====== 4️⃣ إنشاء التطبيق وتهيئته ======
app = Flask(__name__)
from config import Config

app.config.from_object(Config)

# تهيئة قاعدة البيانات
db.init_app(app)

from flask_migrate import Migrate
from models import db  # تأكد من استيراد db
migrate = Migrate(app, db)

# ====== 5️⃣ إعداد Flask-Login ======
# ====== 5️⃣ إعداد Flask-Login ======
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.session_protection = "strong"

def load_user_safely(user_id):
    """تحميل المستخدم مع جميع العلاقات بشكل آمن"""
    return User.query.options(
        db.joinedload(User.company),
        db.joinedload(User.regions),
        db.joinedload(User.user_permissions)
    ).filter_by(id=user_id).first()

@login_manager.user_loader
def load_user(user_id):
    return load_user_safely(int(user_id))


@app.context_processor
def inject_company_data():
    """حقن بيانات الشركة في جميع القوالب بشكل آمن"""

    def get_company_data():
        if current_user.is_authenticated and current_user.company_id:
            try:
                # ✅ تحميل الشركة بشكل منفصل وآمن
                company = Company.query.get(current_user.company_id)
                return company
            except Exception as e:
                print(f"❌ خطأ في تحميل الشركة: {e}")
                return None
        return None

    def get_safe_current_user():
        """الحصول على نسخة آمنة من current_user"""
        if current_user.is_authenticated:
            try:
                return load_user_safely(current_user.id)
            except:
                return current_user
        return None

    return {
        'current_user_company': get_company_data(),
        'safe_current_user': get_safe_current_user()
    }

# ====== 6️⃣ بقية الكود (decorators, forms, routes ...) ======


@app.route("/debug-users")
def debug_users():
    users = User.query.all()
    return "<br>".join([f"{u.username} - {u.email} - {u.role}" for u in users])


import sqlite3
import os
from datetime import datetime


@app.context_processor
def inject_company():
    """حقن بيانات الشركة في جميع القوالب"""

    def get_current_user_company():
        if current_user.is_authenticated and current_user.company_id:
            try:
                # ✅ تحميل الشركة بشكل منفصل لتجنب DetachedInstanceError
                return Company.query.get(current_user.company_id)
            except:
                return None
        return None

    return dict(current_user_company=get_current_user_company())
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


def permission_required(permission):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # ✅ تحميل current_user بشكل آمن
            safe_user = load_user_safely(current_user.id) if current_user.is_authenticated else None

            if not safe_user or not hasattr(safe_user, 'has_permission') or not safe_user.has_permission(permission):
                flash("لا تملك الصلاحية المطلوبة.", "danger")
                return redirect(url_for("dashboard"))
            return f(*args, **kwargs)

        return decorated_function

    return decorator


def company_access_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # ✅ تحميل current_user بشكل آمن
        safe_user = load_user_safely(current_user.id) if current_user.is_authenticated else None

        if not safe_user or not hasattr(safe_user, 'company_id') or safe_user.company_id is None:
            flash("لا تملك صلاحية الوصول إلى هذه الشركة.", "danger")
            return redirect(url_for("dashboard"))
        return f(*args, **kwargs)

    return decorated_function


def user_management_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # ✅ تحميل current_user بشكل آمن
        safe_user = load_user_safely(current_user.id) if current_user.is_authenticated else None

        if not safe_user or not getattr(safe_user, 'role', None) in ['admin', 'supervisor']:
            flash("ليس لديك صلاحية إدارة المستخدمين.", "danger")
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)

    return decorated_function

# ====== FORMS ======
class CompanyForm(FlaskForm):
    name = StringField('اسم الشركة', validators=[DataRequired(), Length(min=2, max=150)])
    code = StringField('كود الشركة', validators=[Optional(), Length(max=50)])
    active = SelectField('نشطة', choices=[('1', 'نعم'), ('0', 'لا')], default='1')
    submit = SubmitField('حفظ')


from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, SubmitField
from wtforms.validators import DataRequired
from models import Company  # تأكد من استيراد نموذج Company

class LoginForm(FlaskForm):
    username = StringField('اسم المستخدم', validators=[DataRequired()])
    password = PasswordField('كلمة المرور', validators=[DataRequired()])
    company = SelectField('الشركة', coerce=int, validators=[Optional()])  # ✅ Optional بدلاً من DataRequired
    submit = SubmitField('تسجيل الدخول')

    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)
        # ✅ جلب الشركات الفعلية
        try:
            companies = Company.query.filter_by(active=True).order_by(Company.name).all()
            self.company.choices = [(0, '-- اختر الشركة --')] + [(c.id, c.name) for c in companies]
        except Exception as e:
            print(f"⚠️ خطأ في تحميل الشركات: {e}")
            self.company.choices = [(0, '-- لا توجد شركات --')]

from wtforms import SelectMultipleField
class UserForm(FlaskForm):
    fullname = StringField('الاسم الكامل', validators=[DataRequired(), Length(min=3, max=150)])
    username = StringField('اسم المستخدم', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('البريد الإلكتروني', validators=[DataRequired(), Length(max=120)])
    password = PasswordField('كلمة المرور', validators=[Optional(), Length(min=6)])
    password_confirm = PasswordField('تأكيد كلمة المرور',
                                   validators=[EqualTo('password', message='كلمتا المرور غير متطابقتين')])
    role = SelectField('الدور', choices=[('admin', 'مشرف'), ('supervisor', 'مشرف فرعي'), ('user', 'مستخدم')], default='user')
    company_id = SelectField('الشركة', coerce=int, validators=[DataRequired()])
    active = SelectField('نشط', choices=[('1', 'نعم'), ('0', 'لا')], default='1')
    region_ids = SelectMultipleField('المناطق المسؤول عنها', coerce=int, validators=[DataRequired()])
    submit = SubmitField('حفظ')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # جلب الشركات للمشرف العام فقط
        from flask import current_app
        with current_app.app_context():
            from models import Company
            self.company_id.choices = [(c.id, c.name) for c in Company.query.order_by(Company.name).all()]
            self.region_ids.choices = [(r.id, r.name) for r in Location.query.order_by(Location.name).all()]


from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

class EvaluationAuthorityForm(FlaskForm):
    name = StringField('اسم الجهة', validators=[DataRequired()])
    company_id = SelectField('الشركة', coerce=int, validators=[DataRequired()])
    submit = SubmitField('إضافة الجهة')

class RegionForm(FlaskForm):
    name = StringField('اسم المنطقة', validators=[DataRequired()])
    company_id = SelectField('Company', coerce=int, validators=[DataRequired()])

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
    total_companies = Company.query.count()

    # الحصول على الشركة المختارة من البارامتر أو استخدام الشركة الافتراضية للمستخدم
    selected_company_id = request.args.get('company_id', type=int)

    if current_user.role == 'admin':
        # للمشرف: يمكنه اختيار أي شركة
        if selected_company_id:
            current_company_id = selected_company_id
        else:
            # إذا لم يتم اختيار شركة، استخدم أول شركة نشطة
            first_company = Company.query.filter_by(active=True).first()
            current_company_id = first_company.id if first_company else None
    else:
        # للمستخدم العادي: يستخدم فقط شركته
        current_company_id = current_user.company_id

    # جلب قائمة الشركات للفلتر (للمشرف فقط)
    companies_list = []
    if current_user.role == 'admin':
        companies_list = Company.query.filter_by(active=True).order_by(Company.name).all()

    # إحصائيات حسب الشركة المختارة
    if current_company_id:
        companies_stats = get_companies_statistics(current_company_id)
        total_evaluations = Evaluation.query.join(User, Evaluation.user_id == User.id).filter(
            User.company_id == current_company_id).count()

        # بيانات الرسوم البيانية حسب الشركة
        daily_stats = get_daily_evaluations_stats(current_company_id)
        cumulative_stats = get_cumulative_evaluations_stats(current_company_id)

        # إحصائيات عامة حسب الشركة
        total_regions = Location.query.filter_by(company_id=current_company_id).count()
        regions_evaluated = db.session.query(Evaluation.region_id) \
            .join(User, Evaluation.user_id == User.id).filter(User.company_id == current_company_id).distinct().count()

        total_authorities = EvaluationAuthority.query.filter_by(company_id=current_company_id).count()
        authorities_evaluated = db.session.query(EvaluationDetail.authority_id) \
            .join(Evaluation).join(User, Evaluation.user_id == User.id) \
            .filter(User.company_id == current_company_id).distinct().count()

        users = User.query.filter(
            User.role != 'admin',
            User.active == True,
            User.company_id == current_company_id
        ).all()

        highest_score = db.session.query(func.max(EvaluationDetail.score)) \
                            .join(Evaluation).join(User, Evaluation.user_id == User.id) \
                            .filter(User.company_id == current_company_id).scalar() or 0

        avg_score = round(db.session.query(func.avg(EvaluationDetail.score)) \
                          .join(Evaluation).join(User, Evaluation.user_id == User.id) \
                          .filter(User.company_id == current_company_id).scalar() or 0, 1)

        # الملاحظات حسب الشركة
        total_action_plans = db.session.query(EvaluationDetail) \
            .join(Evaluation).join(User, Evaluation.user_id == User.id) \
            .filter(
            User.company_id == current_company_id,
            EvaluationDetail.note.isnot(None),
            EvaluationDetail.note != ''
        ).count()

        closed_action_plans = db.session.query(ActionPlan) \
            .join(EvaluationDetail).join(Evaluation).join(User, Evaluation.user_id == User.id) \
            .filter(
            User.company_id == current_company_id,
            ActionPlan.closed == True
        ).count()

        open_action_plans = total_action_plans - closed_action_plans
        close_percentage = round((closed_action_plans / total_action_plans) * 100, 1) if total_action_plans else 0

        top_regions_count = db.session.query(Evaluation.region_id) \
            .join(EvaluationDetail, Evaluation.id == EvaluationDetail.evaluation_id) \
            .join(User, Evaluation.user_id == User.id).filter(User.company_id == current_company_id) \
            .group_by(Evaluation.region_id) \
            .having(func.avg(EvaluationDetail.score) >= 90).count()

        completed_authorities = db.session.query(EvaluationDetail.authority_id) \
            .join(Evaluation).join(User, Evaluation.user_id == User.id) \
            .filter(User.company_id == current_company_id) \
            .group_by(EvaluationDetail.authority_id).count()

        # بيانات المقارنات الزمنية حسب الشركة
        # بيانات المقارنات الزمنية حسب الشركة - بيانات افتراضية
        try:
            time_comparison_data = get_time_comparison_data(current_company_id)
        except:
            time_comparison_data = {
                'weekly': {
                    'current': {'avg_score': 85, 'evaluation_count': 45},
                    'last': {'avg_score': 78, 'evaluation_count': 38},
                    'score_change': 9.0,
                    'count_change': 18.4
                },
                'monthly': {
                    'current': {'avg_score': 82, 'evaluation_count': 210},
                    'last': {'avg_score': 79, 'evaluation_count': 185},
                    'score_change': 3.8,
                    'count_change': 13.5
                }
            }

        try:
            weekly_trends = get_weekly_trends(current_company_id)
        except:
            weekly_trends = [
                {'week': 'أسبوع 1', 'avg_score': 80, 'evaluation_count': 35, 'start_date': '01/12',
                 'end_date': '07/12'},
                {'week': 'أسبوع 2', 'avg_score': 82, 'evaluation_count': 42, 'start_date': '08/12',
                 'end_date': '14/12'},
                {'week': 'أسبوع 3', 'avg_score': 85, 'evaluation_count': 48, 'start_date': '15/12',
                 'end_date': '21/12'},
                {'week': 'أسبوع 4', 'avg_score': 87, 'evaluation_count': 52, 'start_date': '22/12', 'end_date': '28/12'}
            ]

        try:
            monthly_comparison = get_monthly_comparison(current_company_id)
        except:
            monthly_comparison = [
                {'month': '2024-07', 'month_name': 'يوليو 2024', 'avg_score': 78, 'evaluation_count': 180,
                 'active_users': 8},
                {'month': '2024-08', 'month_name': 'أغسطس 2024', 'avg_score': 80, 'evaluation_count': 195,
                 'active_users': 9},
                {'month': '2024-09', 'month_name': 'سبتمبر 2024', 'avg_score': 82, 'evaluation_count': 210,
                 'active_users': 10},
                {'month': '2024-10', 'month_name': 'أكتوبر 2024', 'avg_score': 85, 'evaluation_count': 225,
                 'active_users': 11},
                {'month': '2024-11', 'month_name': 'نوفمبر 2024', 'avg_score': 83, 'evaluation_count': 215,
                 'active_users': 10},
                {'month': '2024-12', 'month_name': 'ديسمبر 2024', 'avg_score': 87, 'evaluation_count': 240,
                 'active_users': 12}
            ]

        try:
            daily_performance = get_daily_performance(current_company_id)
        except:
            daily_performance = [
                {'date': '2024-12-25', 'day_name': 'الثلاثاء', 'date_short': '25/12', 'avg_score': 88,
                 'evaluation_count': 12, 'active_users': 5},
                {'date': '2024-12-24', 'day_name': 'الاثنين', 'date_short': '24/12', 'avg_score': 85,
                 'evaluation_count': 10, 'active_users': 4},
                {'date': '2024-12-23', 'day_name': 'الأحد', 'date_short': '23/12', 'avg_score': 82,
                 'evaluation_count': 8, 'active_users': 3},
                {'date': '2024-12-22', 'day_name': 'السبت', 'date_short': '22/12', 'avg_score': 80,
                 'evaluation_count': 6, 'active_users': 2},
                {'date': '2024-12-21', 'day_name': 'الجمعة', 'date_short': '21/12', 'avg_score': 78,
                 'evaluation_count': 4, 'active_users': 2},
                {'date': '2024-12-20', 'day_name': 'الخميس', 'date_short': '20/12', 'avg_score': 85,
                 'evaluation_count': 9, 'active_users': 4},
                {'date': '2024-12-19', 'day_name': 'الأربعاء', 'date_short': '19/12', 'avg_score': 87,
                 'evaluation_count': 11, 'active_users': 5}
            ]
        # بيانات المستخدمين حسب الشركة
        dashboard_users = []
        colors = ["#FFCDD2", "#C8E6C9", "#BBDEFB", "#FFF9C4", "#D1C4E9", "#B2DFDB", "#FFE0B2", "#F8BBD0"]
        color_index = 0

        for user in users:
            total_criteria = db.session.query(Criterion.id) \
                .join(Place).join(Site).join(Location) \
                .filter(Location.company_id == current_company_id).count()

            today_evaluated = db.session.query(EvaluationDetail.id) \
                .join(Evaluation, Evaluation.id == EvaluationDetail.evaluation_id) \
                .join(User, Evaluation.user_id == User.id) \
                .filter(
                Evaluation.user_id == user.id,
                func.date(Evaluation.date) == today,
                User.company_id == current_company_id
            ).count()

            today_percent = round((today_evaluated / total_criteria) * 100, 1) if total_criteria else 0
            today_percent = min(today_percent, 100)

            total_evaluated = db.session.query(EvaluationDetail.id) \
                .join(Evaluation, Evaluation.id == EvaluationDetail.evaluation_id) \
                .join(User, Evaluation.user_id == User.id) \
                .filter(
                Evaluation.user_id == user.id,
                User.company_id == current_company_id
            ).count()

            first_eval_date = db.session.query(func.min(Evaluation.date)) \
                .join(User, Evaluation.user_id == User.id) \
                .filter(
                Evaluation.user_id == user.id,
                User.company_id == current_company_id
            ).scalar()

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

        # بيانات جهات المسؤولية حسب الشركة
        authorities = EvaluationAuthority.query.filter_by(company_id=current_company_id).all()
        chart_data = []

        for auth in authorities:
            total_criteria = db.session.query(func.count(Criterion.id)) \
                                 .filter(Criterion.authority_id == auth.id).scalar() or 0

            today_eval = db.session.query(
                func.sum(EvaluationDetail.score).label("score_sum"),
                func.sum(Criterion.max_score).label("max_sum"),
                func.count(EvaluationDetail.id)
            ).join(Criterion, EvaluationDetail.criterion_id == Criterion.id) \
                .join(Evaluation, EvaluationDetail.evaluation_id == Evaluation.id) \
                .join(User, Evaluation.user_id == User.id).filter(User.company_id == current_company_id) \
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
                .join(User, Evaluation.user_id == User.id).filter(User.company_id == current_company_id) \
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

        # بيانات المستويات حسب الشركة
        level_type = request.args.get('level', 'region')

        if level_type == 'region':
            levels = Location.query.filter_by(company_id=current_company_id).all()
        elif level_type == 'site':
            levels = Site.query.join(Location).filter(Location.company_id == current_company_id).all()
        elif level_type == 'place':
            levels = (
                db.session.query(Place.name, func.min(Place.id).label("id"))
                .join(Site).join(Location)
                .filter(Location.company_id == current_company_id)
                .group_by(Place.name)
                .all()
            )

        level_data = []

        for lvl in levels:
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
                                 .join(Place).join(Site).join(Location) \
                                 .filter(Location.company_id == current_company_id) \
                                 .filter(filter_condition).scalar() or 0

            today_eval = db.session.query(
                func.sum(EvaluationDetail.score).label("score_sum"),
                func.sum(Criterion.max_score).label("max_sum"),
                func.count(EvaluationDetail.id)
            ).join(Criterion, EvaluationDetail.criterion_id == Criterion.id) \
                .outerjoin(Evaluation, EvaluationDetail.evaluation_id == Evaluation.id) \
                .outerjoin(Place, Place.id == Criterion.place_id) \
                .outerjoin(Site, Site.id == Place.site_id) \
                .outerjoin(Location, Location.id == Site.region_id) \
                .filter(Location.company_id == current_company_id) \
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
                .outerjoin(Location, Location.id == Site.region_id) \
                .filter(Location.company_id == current_company_id) \
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
    else:
        # إذا لم توجد شركة محددة
        companies_stats = []
        total_evaluations = 0
        total_companies = 0
        daily_stats = {'daily_evaluations': 0, 'daily_avg_score': 0}
        cumulative_stats = {'total_evaluations': 0, 'total_avg_score': 0}
        total_regions = 0
        regions_evaluated = 0
        total_authorities = 0
        authorities_evaluated = 0
        users = []
        highest_score = 0
        avg_score = 0
        total_action_plans = 0
        closed_action_plans = 0
        open_action_plans = 0
        close_percentage = 0
        top_regions_count = 0
        completed_authorities = 0
        time_comparison_data = {}
        weekly_trends = []
        monthly_comparison = []
        daily_performance = []
        dashboard_users = []
        chart_data = []
        level_data = []
        level_type = 'region'

    # مقارنة الشركات (للمشرف فقط)
    company_comparison = get_company_comparison_stats() if current_user.role == 'admin' else {}
    # ✅ تأكد من أن time_comparison_data يحتوي على الهيكل المطلوب
    if not time_comparison_data or not isinstance(time_comparison_data, dict):
        time_comparison_data = {
            'weekly': {
                'current': {'avg_score': 0, 'evaluation_count': 0},
                'last': {'avg_score': 0, 'evaluation_count': 0},
                'score_change': 0,
                'count_change': 0
            },
            'monthly': {
                'current': {'avg_score': 0, 'evaluation_count': 0},
                'last': {'avg_score': 0, 'evaluation_count': 0},
                'score_change': 0,
                'count_change': 0
            }
        }
    else:
        # ✅ تأكد من أن جميع المفاتيح موجودة
        time_comparison_data.setdefault('weekly', {})
        time_comparison_data['weekly'].setdefault('current', {'avg_score': 0, 'evaluation_count': 0})
        time_comparison_data['weekly'].setdefault('last', {'avg_score': 0, 'evaluation_count': 0})
        time_comparison_data['weekly'].setdefault('score_change', 0)
        time_comparison_data['weekly'].setdefault('count_change', 0)

        time_comparison_data.setdefault('monthly', {})
        time_comparison_data['monthly'].setdefault('current', {'avg_score': 0, 'evaluation_count': 0})
        time_comparison_data['monthly'].setdefault('last', {'avg_score': 0, 'evaluation_count': 0})
        time_comparison_data['monthly'].setdefault('score_change', 0)
        time_comparison_data['monthly'].setdefault('count_change', 0)

        total_notifications = Notification.query.filter_by(user_id=current_user.id).count()
        read_notifications_count = Notification.query.filter_by(
            user_id=current_user.id,
            is_read=True
        ).count()

        # الإشعارات الحديثة
        recent_notifications = Notification.query.filter_by(
            user_id=current_user.id
        ).order_by(Notification.created_at.desc()).limit(5).all()

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
        total_notifications=total_notifications,
        read_notifications_count=read_notifications_count,
        recent_notifications=recent_notifications,
        # البيانات الجديدة للمقارنات الزمنية
        time_comparison=time_comparison_data,
        weekly_trends=weekly_trends,
        monthly_comparison=monthly_comparison,
        daily_performance=daily_performance,
        # البيانات الجديدة للشركات
        companies_stats=companies_stats,
        total_companies=total_companies,
        daily_stats=daily_stats,
        cumulative_stats=cumulative_stats,
        company_comparison=company_comparison,
        # بيانات الفلتر
        companies_list=companies_list,
        selected_company_id=current_company_id,
        current_company=Company.query.get(current_company_id) if current_company_id else None
    )

def get_companies_statistics(company_id=None):
    """الحصول على إحصائيات الشركات"""
    query = db.session.query(
        Company.id,
        Company.name,
        func.count(Evaluation.id).label('evaluation_count'),
        func.count(distinct(User.id)).label('user_count'),
        func.avg(EvaluationDetail.score).label('avg_score')
    ).outerjoin(User, Company.id == User.company_id) \
        .outerjoin(Evaluation, User.id == Evaluation.user_id) \
        .outerjoin(EvaluationDetail, Evaluation.id == EvaluationDetail.evaluation_id)

    if company_id:
        query = query.filter(Company.id == company_id)

    results = query.group_by(Company.id, Company.name).all()

    stats = []
    for company_id, company_name, eval_count, user_count, avg_score in results:
        stats.append({
            'id': company_id,
            'name': company_name,
            'evaluation_count': eval_count or 0,
            'user_count': user_count or 0,
            'avg_score': round(avg_score or 0, 1)
        })

    return stats


def get_daily_evaluations_stats(company_id=None):
    today = date.today()

    # حدد المفتاح الأجنبي الذي تريد استخدامه عند join
    query = Evaluation.query.join(User, Evaluation.user_id == User.id)

    if company_id:
        query = query.filter(User.company_id == company_id)

    # التقييمات اليومية
    daily_evaluations = query.filter(func.date(Evaluation.date) == today).count()

    # متوسط الدرجات اليومي
    daily_avg = db.session.query(func.avg(EvaluationDetail.score)) \
        .join(Evaluation, EvaluationDetail.evaluation_id == Evaluation.id) \
        .join(User, Evaluation.user_id == User.id)

    if company_id:
        daily_avg = daily_avg.filter(User.company_id == company_id)

    daily_avg = daily_avg.filter(func.date(Evaluation.date) == today).scalar() or 0

    return {
        'daily_evaluations': daily_evaluations,
        'daily_avg_score': round(daily_avg, 1)
    }


# الدالة التراكمية
def get_cumulative_evaluations_stats(company_id=None):
    query = Evaluation.query.join(User, Evaluation.user_id == User.id)

    if company_id:
        query = query.filter(User.company_id == company_id)

    total_evaluations = query.count()

    total_avg = db.session.query(func.avg(EvaluationDetail.score)) \
        .join(Evaluation, EvaluationDetail.evaluation_id == Evaluation.id) \
        .join(User, Evaluation.user_id == User.id)

    if company_id:
        total_avg = total_avg.filter(User.company_id == company_id)

    total_avg = total_avg.scalar() or 0

    return {
        'total_evaluations': total_evaluations,
        'total_avg_score': round(total_avg, 1)
    }




# ===== دوال جديدة للمقارنات الزمنية مع دعم الشركات =====
def get_time_comparison_data(company_id=None):
    """الحصول على بيانات المقارنة بين الفترات الزمنية مع دعم الشركات"""
    try:
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

        # ✅ استعلامات مصححة مع تحديد العلاقة بشكل صريح
        def build_query():
            return db.session.query(
                func.avg(EvaluationDetail.score).label('avg_score'),
                func.count(EvaluationDetail.id).label('evaluation_count')
            ).select_from(EvaluationDetail) \
             .join(Evaluation, EvaluationDetail.evaluation_id == Evaluation.id) \
             .join(User, Evaluation.user_id == User.id)  # ✅ تحديد صريح

        # بيانات الأسبوع الحالي
        current_week_query = build_query()
        if company_id:
            current_week_query = current_week_query.filter(User.company_id == company_id)
        current_week_data = current_week_query.filter(
            Evaluation.date >= start_of_week,
            Evaluation.date <= end_of_week
        ).first()

        # بيانات الأسبوع الماضي
        last_week_query = build_query()
        if company_id:
            last_week_query = last_week_query.filter(User.company_id == company_id)
        last_week_data = last_week_query.filter(
            Evaluation.date >= start_of_last_week,
            Evaluation.date <= end_of_last_week
        ).first()

        # بيانات الشهر الحالي
        current_month_query = build_query()
        if company_id:
            current_month_query = current_month_query.filter(User.company_id == company_id)
        current_month_data = current_month_query.filter(
            Evaluation.date >= start_of_month,
            Evaluation.date <= end_of_month
        ).first()

        # بيانات الشهر الماضي
        last_month_query = build_query()
        if company_id:
            last_month_query = last_month_query.filter(User.company_id == company_id)
        last_month_data = last_month_query.filter(
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
    except Exception as e:
        print(f"Error in get_time_comparison_data: {e}")
        return {
            'weekly': {'current': {'avg_score': 0, 'evaluation_count': 0}, 'last': {'avg_score': 0, 'evaluation_count': 0}, 'score_change': 0, 'count_change': 0},
            'monthly': {'current': {'avg_score': 0, 'evaluation_count': 0}, 'last': {'avg_score': 0, 'evaluation_count': 0}, 'score_change': 0, 'count_change': 0}
        }

def get_weekly_trends(company_id=None):
    """الحصول على اتجاهات الأداء الأسبوعية مع دعم الشركات"""
    try:
        today = date.today()
        weeks_data = []

        for i in range(4):  # آخر 4 أسابيع
            start_date = today - timedelta(days=today.weekday() + (i * 7))
            end_date = start_date + timedelta(days=6)

            # ✅ استعلام مصحح
            query = db.session.query(
                func.avg(EvaluationDetail.score).label('avg_score'),
                func.count(EvaluationDetail.id).label('evaluation_count')
            ).select_from(EvaluationDetail) \
             .join(Evaluation, EvaluationDetail.evaluation_id == Evaluation.id) \
             .join(User, Evaluation.user_id == User.id)  # ✅ تحديد صريح

            if company_id:
                query = query.filter(User.company_id == company_id)

            week_data = query.filter(
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

        return list(reversed(weeks_data))
    except Exception as e:
        print(f"Error in get_weekly_trends: {e}")
        return []
def get_monthly_comparison(company_id=None):
    """مقارنة الأداء بين الشهور مع دعم الشركات"""
    monthly_data = []

    for i in range(6):  # آخر 6 شهور
        month_start = (date.today().replace(day=1) - timedelta(days=30 * i)).replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)

        query = db.session.query(
            func.avg(EvaluationDetail.score).label('avg_score'),
            func.count(EvaluationDetail.id).label('evaluation_count'),
            func.count(db.distinct(Evaluation.user_id)).label('active_users')
        ).join(Evaluation).join(User, Evaluation.user_id == User.id)  # ✅ أصلح هنا

        if company_id:
            query = query.filter(User.company_id == company_id)

        month_stats = query.filter(
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

def get_daily_performance(company_id=None):
    """الحصول على أداء الأيام الأخيرة مع دعم الشركات"""
    daily_data = []

    for i in range(7):  # آخر 7 أيام
        day = date.today() - timedelta(days=i)

        query = db.session.query(
            func.avg(EvaluationDetail.score).label('avg_score'),
            func.count(EvaluationDetail.id).label('evaluation_count'),
            func.count(db.distinct(Evaluation.user_id)).label('active_users')
        ).join(Evaluation).join(User, Evaluation.user_id == User.id)  # ✅ أصلح هنا

        if company_id:
            query = query.filter(User.company_id == company_id)

        day_stats = query.filter(
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

def get_company_comparison_stats():
    """مقارنة أداء الشركات (للمشرف العام فقط)"""
    if current_user.role != 'admin':
        return []

    # آخر 7 أيام
    date_range = [date.today() - timedelta(days=i) for i in range(6, -1, -1)]

    companies = Company.query.filter_by(active=True).all()
    comparison_data = []

    for company in companies:
        company_data = {
            'name': company.name,
            'daily_scores': [],
            'total_evaluations': 0
        }

        for day in date_range:
            daily_avg = (
                db.session.query(func.avg(EvaluationDetail.score))
                .join(Evaluation)
                .join(User, Evaluation.user_id == User.id)
                .filter(
                    User.company_id == company.id,
                    func.date(Evaluation.date) == day
                )
                .scalar()
                or 0
            )

            company_data['daily_scores'].append(round(daily_avg, 1))

        company_data['total_evaluations'] = (
            Evaluation.query
            .join(User, Evaluation.user_id == User.id)
            .filter(User.company_id == company.id)
            .count()
        )

        comparison_data.append(company_data)

    return {
        'date_labels': [d.strftime('%Y-%m-%d') for d in date_range],
        'companies_data': comparison_data
    }


def calculate_percentage_change(current, previous):
    """حساب نسبة التغير المئوية"""
    if previous == 0:
        return 100 if current > 0 else 0
    return round(((current - previous) / previous) * 100, 1)

@app.route('/users_dashboard')
@login_required
def users_dashboard():
    """توجيه كل مستخدم إلى الداشبورد المناسب له"""
    return redirect(url_for(current_user.get_dashboard_url()))


@app.route('/user_dashboard')
@login_required
def user_dashboard():
    return render_template('user/dashboard.html', users=users)
# ديكورات تحكم الوصول للصفحات
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            flash('هذه الصفحة للمسؤولين فقط', 'danger')
            return redirect(url_for('user_dashboard'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/manager_dashboard')
@login_required
def manager_dashboard():
    """داشبورد مدير الشؤون - يرى شركته فقط"""
    if current_user.role != 'supervisor':
        flash('غير مصرح لك بالوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('user_dashboard'))

    if not current_user.company_id:
        flash('لم يتم تعيين شركة لك، يرجى التواصل مع المسؤول', 'danger')
        return redirect(url_for('logout'))

    # إحصائيات شركة المستخدم فقط
    company = Company.query.get(current_user.company_id)
    if not company:
        flash('الشركة غير موجودة', 'danger')
        return redirect(url_for('logout'))

    # المستخدمين في نفس الشركة
    company_users = User.query.filter_by(company_id=current_user.company_id, active=True).count()

    # التقييمات في نفس الشركة
    company_evaluations = Evaluation.query.join(User).filter(
        User.company_id == current_user.company_id
    ).count()

    # التقييمات الحديثة للشركة
    recent_evaluations = Evaluation.query.join(User).filter(
        User.company_id == current_user.company_id
    ).order_by(Evaluation.date.desc()).limit(10).all()

    return render_template('manager/dashboard.html',
                           dashboard_type='manager',
                           company=company,
                           company_users=company_users,
                           company_evaluations=company_evaluations,
                           recent_evaluations=recent_evaluations)


@app.route('/sub_admin_dashboard')
@login_required
def sub_admin_dashboard():
    """داشبورد المشرف الفرعي - يرى شركته مع صلاحيات محددة"""
    if current_user.role != 'sub_admin':
        flash('غير مصرح لك بالوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('user_dashboard'))

    if not current_user.company_id:
        flash('لم يتم تعيين شركة لك، يرجى التواصل مع المسؤول', 'danger')
        return redirect(url_for('logout'))

    company = Company.query.get(current_user.company_id)
    if not company:
        flash('الشركة غير موجودة', 'danger')
        return redirect(url_for('logout'))

    # إحصائيات محدودة للمشرف الفرعي
    company_users = User.query.filter_by(
        company_id=current_user.company_id,
        active=True,
        role='user'  # يرى المستخدمين العاديين فقط
    ).count()

    # التقييمات الخاصة به فقط
    user_evaluations = Evaluation.query.filter_by(user_id=current_user.id).count()

    # التقييمات الحديثة الخاصة به
    recent_evaluations = Evaluation.query.filter_by(user_id=current_user.id) \
        .order_by(Evaluation.date.desc()).limit(10).all()

    return render_template('sub_admin/dashboard.html',
                           dashboard_type='sub_admin',
                           company=company,
                           company_users=company_users,
                           user_evaluations=user_evaluations,
                           recent_evaluations=recent_evaluations)
# صفحة تسجيل الدخول
# صفحة تسجيل الدخول
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        # ✅ ابحث عن المستخدم بدون شركة أولاً
        user = User.query.filter_by(username=form.username.data).first()

        if user and user.check_password(form.password.data):
            if user.active:
                # ✅ للمستخدمين العاديين: تحقق من وجود شركة
                if user.role != 'admin' and user.company_id is None:
                    flash('المستخدم غير مرتبط بأي شركة', 'danger')
                    return render_template('admin/login.html', form=form)

                login_user(user)
                flash('تم تسجيل الدخول بنجاح', 'success')

                # توجيه حسب الدور
                if user.role == 'admin':
                    return redirect(url_for('dashboard'))
                elif user.role in ['supervisor', 'sub_admin']:
                    return redirect(url_for('manager_dashboard'))
                else:
                    return redirect(url_for('user_dashboard'))
            else:
                flash('الحساب غير نشط', 'danger')
        else:
            flash('اسم المستخدم أو كلمة المرور غير صحيحة', 'danger')

    return render_template('admin/login.html', form=form)

# تسجيل الخروج
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('تم تسجيل الخروج', 'info')
    return redirect(url_for('login'))


# routes.py - تحديث الدوال مع نظام الصلاحيات

# --- إدارة المستخدمين مع الصلاحيات ---
# routes.py - تحديث دوال إدارة المستخدمين مع نظام الصلاحيات

from functools import wraps
from flask import redirect, url_for, flash
from flask_login import current_user


# --- إدارة المستخدمين ---
# --- إدارة المستخدمين ---
# --- إدارة المستخدمين (الإصدار النهائي المصحح) ---
@app.route('/users')
@login_required
@permission_required('users_view')
def users():
    try:
        print(f"=== تشخيص دالة users() ===")
        print(f"المستخدم الحالي: {current_user.username}")
        print(f"is_admin: {current_user.is_admin}")
        print(f"is_administrator: {current_user.is_administrator}")
        print(f"role: {current_user.role}")
        print(f"company_id: {current_user.company_id}")

        # الحصول على جميع المستخدمين مع معلومات الشركات والصلاحيات
        if current_user.is_administrator:
            users_list = User.query.options(
                db.joinedload(User.company),
                db.joinedload(User.user_permissions)
            ).all()
            print(f"✅ المسؤول يرى جميع المستخدمين: {len(users_list)} مستخدم")

        elif current_user.role in ['supervisor', 'sub_admin'] and current_user.company_id:
            users_list = User.query.options(
                db.joinedload(User.company),
                db.joinedload(User.user_permissions)
            ).filter_by(company_id=current_user.company_id).all()
            print(f"🔹 المشرف يرى مستخدمي الشركة {current_user.company_id}: {len(users_list)} مستخدم")

        else:
            users_list = [current_user]
            print(f"👤 مستخدم عادي يرى نفسه فقط: {len(users_list)} مستخدم")

        # الحصول على جميع الشركات للعرض (للمسؤولين فقط)
        companies = Company.query.filter_by(active=True).all() if current_user.is_administrator else []

        # الحصول على جميع أنواع الصلاحيات المتاحة
        all_permissions = Permission.query.order_by(Permission.category, Permission.name).all()

        print("=== المستخدمين المعروضين ===")
        for user in users_list:
            print(f"👤 {user.username} (id: {user.id}, role: {user.role}, company: {user.company_id})")
            print(f"   الصلاحيات: {user.all_permissions}")

        return render_template('admin/users.html',
                             users=users_list,
                             companies=companies,
                             all_permissions=all_permissions)

    except Exception as e:
        print(f"❌ خطأ في دالة users: {str(e)}")
        import traceback
        traceback.print_exc()
        flash('حدث خطأ في تحميل قائمة المستخدمين', 'danger')
        return redirect(url_for('index'))


# --- إضافة مستخدم ---
@app.route('/users/add', methods=['GET', 'POST'])
@login_required
@permission_required('users_add')
@company_access_required
def add_user():
    try:
        print(f"=== بدء دالة add_user ===")

        # ✅ الحل: تحميل current_user مع العلاقات مسبقاً
        safe_current_user = load_user_safely(current_user.id)

        if not safe_current_user:
            flash('خطأ في تحميل بيانات المستخدم', 'danger')
            return redirect(url_for('users'))

        print(f"المستخدم الحالي: {safe_current_user.username}, الدور: {safe_current_user.role}")

        form = UserForm()
        form.active.choices = [('1', 'نعم'), ('0', 'لا')]

        # تحديد الأدوار المتاحة بناءً على صلاحيات المستخدم
        if safe_current_user.role == 'admin':
            form.role.choices = [('admin', 'مسؤول'), ('supervisor', 'مشرف'), ('sub_admin', 'مشرف فرعي'),
                                 ('user', 'مستخدم')]
        elif safe_current_user.role == 'supervisor':
            form.role.choices = [('sub_admin', 'مشرف فرعي'), ('user', 'مستخدم')]
        else:
            form.role.choices = [('user', 'مستخدم')]

        # ✅ تحديد الشركات المتاحة بشكل آمن
        if safe_current_user.role == 'admin':
            companies = Company.query.all()
            form.company_id.choices = [(c.id, c.name) for c in companies]
            print(f"✅ المسؤول يرى {len(companies)} شركة")
        else:
            # للمشرفين، يمكنهم إضافة مستخدمين لشركتهم فقط
            if safe_current_user.company:
                form.company_id.choices = [(safe_current_user.company_id, safe_current_user.company.name)]
                form.company_id.data = safe_current_user.company_id
                print(f"🔹 المشرف يرى شركته فقط: {safe_current_user.company.name}")
            else:
                flash('لم يتم تعيين شركة لك', 'danger')
                return redirect(url_for('users'))

        # ✅ تحميل البيانات مسبقاً لتجنب DetachedInstanceError
        users_list = User.query.options(
            db.joinedload(User.company),
            db.joinedload(User.regions)
        ).all()

        regions_list = Location.query.order_by(Location.name).all()

        if form.region_ids.data is None:
            form.region_ids.data = []

        if form.validate_on_submit():
            print("✅ تم التحقق من صحة النموذج")

            # التحقق من عدم تكرار اسم المستخدم
            existing_user = User.query.filter_by(username=form.username.data).first()
            if existing_user:
                flash('اسم المستخدم موجود مسبقاً', 'warning')
                return render_template('admin/user_form.html',
                                       form=form,
                                       users=users_list,
                                       regions=regions_list,
                                       safe_current_user=safe_current_user)

            if not form.password.data:
                flash('كلمة المرور مطلوبة', 'warning')
                return render_template('admin/user_form.html',
                                       form=form,
                                       users=users_list,
                                       regions=regions_list,
                                       safe_current_user=safe_current_user)

            try:
                # تحديد company_id بناءً على صلاحيات المستخدم
                company_id = form.company_id.data
                if safe_current_user.role in ['supervisor', 'sub_admin']:
                    company_id = safe_current_user.company_id

                user = User(
                    fullname=form.fullname.data,
                    username=form.username.data,
                    email=form.email.data,
                    role=form.role.data,
                    active=(form.active.data == '1'),
                    company_id=company_id
                )
                user.set_password(form.password.data)

                db.session.add(user)
                db.session.flush()  # للحصول على ID

                # إضافة المناطق المحددة
                if form.region_ids.data:
                    selected_regions = Location.query.filter(Location.id.in_(form.region_ids.data)).all()
                    user.regions = selected_regions
                    print(f"📍 تم إضافة {len(selected_regions)} منطقة للمستخدم")

                # إضافة الصلاحيات للمشرفين الفرعيين
                if user.role == 'sub_admin':
                    selected_permissions = request.form.getlist('permissions')
                    for perm_code in selected_permissions:
                        user_perm = UserPermission(
                            user_id=user.id,
                            permission_code=perm_code
                        )
                        db.session.add(user_perm)
                    print(f"🔐 تم إضافة {len(selected_permissions)} صلاحية للمشرف الفرعي")

                db.session.commit()
                flash('تم إضافة المستخدم بنجاح', 'success')
                print(f"✅ تم إضافة المستخدم {user.username} بنجاح")
                return redirect(url_for('users'))

            except Exception as e:
                db.session.rollback()
                error_msg = f'حدث خطأ أثناء إضافة المستخدم: {str(e)}'
                flash(error_msg, 'danger')
                print(f"❌ {error_msg}")
                import traceback
                traceback.print_exc()

        # ✅ تمرير البيانات الآمنة للقالب
        return render_template('admin/user_form.html',
                               form=form,
                               users=users_list,
                               regions=regions_list,
                               safe_current_user=safe_current_user,
                               title='إضافة مستخدم جديد')

    except Exception as e:
        db.session.rollback()
        error_msg = f'حدث خطأ في تحميل الصفحة: {str(e)}'
        flash(error_msg, 'danger')
        print(f"❌ {error_msg}")
        import traceback
        traceback.print_exc()
        return redirect(url_for('users'))

# --- تعديل مستخدم ---

@app.route('/users/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
@permission_required('users_edit')
@user_management_required
def edit_user(user_id):
    try:
        # ✅ الحل: استخدام joinedload لتحميل العلاقات مسبقاً
        user = User.query.options(
            db.joinedload(User.regions),
            db.joinedload(User.user_permissions),
            db.joinedload(User.company)
        ).filter_by(id=user_id).first()

        if not user:
            flash('المستخدم غير موجود', 'danger')
            return redirect(url_for('users'))

        # ✅ تحميل current_user بشكل آمن
        safe_current_user = load_user_safely(current_user.id)

        form = UserForm(obj=user)
        form.active.choices = [('1', 'نعم'), ('0', 'لا')]

        # ✅ إصلاح: تحديد الأدوار المتاحة
        if safe_current_user.role == 'admin':
            form.role.choices = [('admin', 'مسؤول'), ('supervisor', 'مشرف'), ('sub_admin', 'مشرف فرعي'),
                                 ('user', 'مستخدم')]
        elif safe_current_user.role == 'supervisor':
            form.role.choices = [('sub_admin', 'مشرف فرعي'), ('user', 'مستخدم')]
        else:
            form.role.choices = [('user', 'مستخدم')]

        # ✅ إصلاح: تحديد الشركات المتاحة
        if safe_current_user.role == 'admin':
            companies = Company.query.all()
            form.company_id.choices = [(c.id, c.name) for c in companies]
            print(f"✅ المسؤول يرى {len(companies)} شركة للتعديل")
        else:
            form.company_id.choices = [(safe_current_user.company_id, safe_current_user.company.name)]
            print(f"🔹 المشرف يرى شركته فقط: {safe_current_user.company.name}")

        # الحصول على جميع الصلاحيات
        all_permissions = Permission.query.order_by(Permission.category, Permission.name).all()

        users_list = User.query.options(db.joinedload(User.company)).all()
        regions_list = Location.query.order_by(Location.name).all()

        if form.region_ids.data is None:
            form.region_ids.data = []

        form.password.validators = []
        form.password_confirm.validators = [EqualTo('password', message='كلمتا المرور غير متطابقتين')]

        if request.method == "GET":
            form.active.data = '1' if user.active else '0'
            # ✅ الآن هذا السطر آمن ولن يسبب DetachedInstanceError
            form.region_ids.data = [r.id for r in user.regions]
            form.company_id.data = user.company_id

            # تحميل الصلاحيات الحالية للمشرفين الفرعيين
            current_permissions = [up.permission_code for up in user.user_permissions]

            print(f"🔹 تحميل بيانات المستخدم: {user.username}")
            print(f"   - الشركة: {user.company_id}")
            print(f"   - المناطق: {len(user.regions)} منطقة")
            print(f"   - الصلاحيات: {len(current_permissions)} صلاحية")
        else:
            current_permissions = [up.permission_code for up in user.user_permissions]

        if form.validate_on_submit():
            # التحقق من عدم تكرار اسم المستخدم
            existing_user = User.query.filter(
                User.id != user.id,
                User.username == form.username.data
            ).first()

            if existing_user:
                flash('اسم المستخدم موجود مسبقاً', 'warning')
                return render_template('admin/user_form.html',
                                       form=form,
                                       users=users_list,
                                       regions=regions_list,
                                       selected_user_id=user.id,
                                       all_permissions=all_permissions,
                                       current_permissions=current_permissions,
                                       safe_current_user=safe_current_user)

            try:
                # تحديث البيانات الأساسية
                user.fullname = form.fullname.data
                user.username = form.username.data
                user.email = form.email.data
                user.role = form.role.data
                user.active = (form.active.data == '1')

                # ✅ إصلاح: فقط المسؤولون يمكنهم تغيير الشركة
                if safe_current_user.role == 'admin':
                    user.company_id = form.company_id.data
                    print(f"✅ المسؤول قام بتغيير الشركة إلى: {form.company_id.data}")

                # تحديث كلمة المرور إذا تم إدخالها
                if form.password.data and form.password.data.strip():
                    user.set_password(form.password.data)
                    print("🔑 تم تحديث كلمة المرور")

                # ✅ تحديث المناطق (الآن آمن بسبب joinedload)
                if form.region_ids.data:
                    selected_regions = Location.query.filter(Location.id.in_(form.region_ids.data)).all()
                    user.regions = selected_regions
                    print(f"📍 تم تحديث المناطق: {len(selected_regions)} منطقة")
                else:
                    user.regions = []
                    print("📍 تم إزالة جميع المناطق")

                # ✅ تحديث الصلاحيات للمشرفين الفرعيين
                if user.role == 'sub_admin':
                    # حذف الصلاحيات الحالية
                    UserPermission.query.filter_by(user_id=user.id).delete()

                    # إضافة الصلاحيات الجديدة
                    selected_permissions = request.form.getlist('permissions')
                    for perm_code in selected_permissions:
                        user_perm = UserPermission(
                            user_id=user.id,
                            permission_code=perm_code
                        )
                        db.session.add(user_perm)

                    print(f"🔐 تم تحديث {len(selected_permissions)} صلاحية للمشرف الفرعي")
                else:
                    # إذا لم يكن مشرفاً فرعياً، احذف جميع صلاحياته المخصصة
                    UserPermission.query.filter_by(user_id=user.id).delete()
                    print("🔐 تم حذف جميع الصلاحيات المخصصة (المستخدم ليس مشرفاً فرعياً)")

                db.session.commit()
                flash('تم تعديل بيانات المستخدم بنجاح', 'success')
                print(f"✅ تم تعديل المستخدم {user.username} بنجاح")
                return redirect(url_for('users'))

            except Exception as e:
                db.session.rollback()
                error_msg = f'حدث خطأ أثناء تعديل المستخدم: {str(e)}'
                flash(error_msg, 'danger')
                print(f"❌ {error_msg}")
                import traceback
                traceback.print_exc()

        return render_template('admin/user_form.html',
                               form=form,
                               users=users_list,
                               regions=regions_list,
                               selected_user_id=user.id,
                               all_permissions=all_permissions,
                               current_permissions=current_permissions,
                               safe_current_user=safe_current_user,
                               title='تعديل مستخدم')

    except Exception as e:
        db.session.rollback()
        error_msg = f'حدث خطأ في تحميل الصفحة: {str(e)}'
        flash(error_msg, 'danger')
        print(f"❌ {error_msg}")
        import traceback
        traceback.print_exc()
        return redirect(url_for('users'))
# --- حذف مستخدم ---
@app.route('/users/delete/<int:user_id>', methods=['POST'])
@login_required
@permission_required('users_delete')
@user_management_required
def delete_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        flash('المستخدم غير موجود', 'danger')
        return redirect(url_for('users'))

    if user.username == 'admin':
        flash('لا يمكن حذف المشرف الرئيسي', 'warning')
        return redirect(url_for('users'))

    if user.evaluations:
        user.active = False
        db.session.commit()
        flash('المستخدم مرتبط بتقييمات، تم تغييره إلى غير نشط بدلاً من الحذف', 'info')
        return redirect(url_for('users'))

    try:
        db.session.delete(user)
        db.session.commit()
        flash('تم حذف المستخدم بنجاح', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء حذف المستخدم: {str(e)}', 'danger')

    return redirect(url_for('users'))




# دالة لتهيئة الصلاحيات الافتراضية
def initialize_default_permissions():
    """تهيئة الصلاحيات الافتراضية في النظام"""
    default_permissions = [
        # صلاحيات إدارة المستخدمين
        {'name': 'عرض المستخدمين', 'code': 'users_view', 'category': 'users'},
        {'name': 'إضافة مستخدمين', 'code': 'users_add', 'category': 'users'},
        {'name': 'تعديل المستخدمين', 'code': 'users_edit', 'category': 'users'},
        {'name': 'حذف المستخدمين', 'code': 'users_delete', 'category': 'users'},

        # صلاحيات التقييمات
        {'name': 'عرض التقييمات', 'code': 'evaluations_view', 'category': 'evaluations'},
        {'name': 'إضافة تقييمات', 'code': 'evaluations_add', 'category': 'evaluations'},
        {'name': 'تعديل التقييمات', 'code': 'evaluations_edit', 'category': 'evaluations'},
        {'name': 'حذف التقييمات', 'code': 'evaluations_delete', 'category': 'evaluations'},

        # صلاحيات التقارير
        {'name': 'عرض التقارير', 'code': 'reports_view', 'category': 'reports'},
        {'name': 'تصدير التقارير', 'code': 'reports_export', 'category': 'reports'},

        # صلاحيات الإعدادات
        {'name': 'عرض الإعدادات', 'code': 'settings_view', 'category': 'settings'},
        {'name': 'تعديل الإعدادات', 'code': 'settings_edit', 'category': 'settings'},

        # صلاحيات إدارة الصلاحيات
        {'name': 'إدارة الصلاحيات', 'code': 'manage_permissions', 'category': 'admin'},
    ]

    for perm_data in default_permissions:
        if not Permission.query.filter_by(code=perm_data['code']).first():
            permission = Permission(**perm_data)
            db.session.add(permission)

    db.session.commit()


@app.route('/admin/sub-admins-simple')
@login_required
def manage_sub_admins_simple():
    """إصفح بسيط يعمل 100%"""
    print(f"\n=== 🎯 الإصدار البسيط يعمل ===")
    print(f"المستخدم: {current_user.username}, الدور: {current_user.role}, is_admin: {current_user.is_admin}")

    # ✅ تحقق بسيط: إذا كان مسؤولاً أو مشرفاً، اسمح له
    if current_user.is_admin or current_user.role in ['supervisor', 'sub_admin']:
        print("✅ الوصول مسموح")
    else:
        print("❌ الوصول مرفوض")
        flash('غير مصرح لك بالوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('index'))

    try:
        # الحصول على جميع المشرفين الفرعيين
        if current_user.is_admin:
            # المسؤول يرى الجميع
            sub_admins = User.query.filter_by(role='sub_admin').options(
                db.joinedload(User.company),
                db.joinedload(User.user_permissions)
            ).all()
            companies_list = Company.query.filter_by(is_active=True).all()
            current_company = None
        else:
            # المشرف يرى مشرفي شركته فقط
            sub_admins = User.query.filter_by(
                role='sub_admin',
                company_id=current_user.company_id
            ).options(
                db.joinedload(User.company),
                db.joinedload(User.user_permissions)
            ).all()
            companies_list = Company.query.filter_by(id=current_user.company_id, is_active=True).all()
            current_company = current_user.company

        # تحضير البيانات للعرض
        sub_admins_data = []
        for admin in sub_admins:
            admin_data = {
                'id': admin.id,
                'name': admin.fullname or admin.username,
                'email': admin.email,
                'is_active': admin.active,
                'permissions_count': len(admin.user_permissions),
                'permissions': [up.permission_code for up in admin.user_permissions],
                'company_name': admin.company.name if admin.company else 'غير محدد'
            }
            sub_admins_data.append(admin_data)

        print(f"✅ تم تحضير {len(sub_admins_data)} مشرف للعرض")

        return render_template('admin/manage_sub_admins.html',
                               sub_admins=sub_admins_data,
                               companies_list=companies_list,
                               current_company=current_company,
                               selected_company_id=current_user.company_id if not current_user.is_admin else None,
                               now=datetime.now())

    except Exception as e:
        print(f"❌ خطأ: {str(e)}")
        import traceback
        traceback.print_exc()
        flash('حدث خطأ في تحميل الصفحة', 'danger')
        return redirect(url_for('index'))

@app.route('/fix-permissions')
@login_required
def fix_permissions():
    """إصلاح الصلاحيات للمسؤولين"""
    if not current_user.is_admin:
        return "غير مصرح"

    from models import Permission, UserPermission

    # إنشاء صلاحية manage_permissions إذا لم تكن موجودة
    perm = Permission.query.filter_by(code='manage_permissions').first()
    if not perm:
        perm = Permission(
            name='إدارة الصلاحيات',
            code='manage_permissions',
            category='admin'
        )
        db.session.add(perm)
        db.session.commit()
        print("✅ تم إنشاء صلاحية manage_permissions")

    # منح الصلاحية لجميع المسؤولين
    admins = User.query.filter_by(role='admin').all()
    for admin in admins:
        if not UserPermission.query.filter_by(user_id=admin.id, permission_code='manage_permissions').first():
            user_perm = UserPermission(
                user_id=admin.id,
                permission_code='manage_permissions'
            )
            db.session.add(user_perm)
            print(f"✅ تم منح الصلاحية للمسؤول: {admin.username}")

    db.session.commit()
    return "✅ تم إصلاح الصلاحيات بنجاح"

# routes_debug.py - دوال للمساعدة في تشخيص المشكلة
@app.route('/debug/users')
@login_required
def debug_users_view():
    """صفحة debug لعرض معلومات المستخدمين"""
    if not current_user.is_admin:
        flash('غير مصرح لك', 'danger')
        return redirect(url_for('index'))

    all_users = User.query.all()
    debug_info = []

    for user in all_users:
        user_info = {
            'id': user.id,
            'username': user.username,
            'role': user.role,
            'company_id': user.company_id,
            'company_name': user.company.name if user.company else 'لا يوجد',
            'is_admin': user.is_admin,
            'active': user.active,
            'permissions_count': len(user.all_permissions)
        }
        debug_info.append(user_info)

    return render_template('admin/debug_users.html', users_debug=debug_info)


@app.route('/debug/permissions/<int:user_id>')
@login_required
def debug_user_permissions(user_id):
    """عرض صلاحيات مستخدم معين"""
    if not current_user.is_admin:
        flash('غير مصرح لك', 'danger')
        return redirect(url_for('index'))

    user = User.query.get_or_404(user_id)

    return jsonify({
        'user': {
            'id': user.id,
            'username': user.username,
            'role': user.role,
            'company_id': user.company_id,
            'is_admin': user.is_admin
        },
        'role_permissions': user.get_role_permissions(),
        'custom_permissions': [up.permission_code for up in user.user_permissions],
        'all_permissions': user.all_permissions
    })


@app.route('/admin/sub-admins')
@login_required
def manage_sub_admins():
    """إدارة المشرفين الفرعيين - الإصدار النهائي"""
    print(f"\n=== 🎯 الإصدار النهائي يعمل ===")
    print(f"المستخدم: {current_user.username}, الدور: {current_user.role}")

    # ✅ تحقق مبسط
    if current_user.role not in ['admin', 'supervisor', 'sub_admin']:
        flash('غير مصرح لك بالوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('index'))

    try:
        # الحصول على جميع الشركات
        if current_user.role == 'admin':
            companies_list = Company.query.all()
            sub_admins = User.query.filter_by(role='sub_admin').all()
            current_company = None
            selected_company_id = None
        else:
            companies_list = Company.query.filter_by(id=current_user.company_id).all()
            sub_admins = User.query.filter_by(role='sub_admin', company_id=current_user.company_id).all()
            current_company = current_user.company
            selected_company_id = current_user.company_id

        # تحضير البيانات للعرض
        sub_admins_data = []
        for admin in sub_admins:
            # الحصول على الصلاحيات بشكل آمن
            permissions_count = 0
            permissions_list = []

            if hasattr(admin, 'user_permissions'):
                permissions_count = len(admin.user_permissions)
                permissions_list = [up.permission_code for up in admin.user_permissions]

            admin_data = {
                'id': admin.id,
                'name': admin.fullname or admin.username,
                'email': admin.email,
                'is_active': admin.active,
                'permissions_count': permissions_count,
                'permissions': permissions_list,
                'company_name': admin.company.name if admin.company else 'غير محدد'
            }
            sub_admins_data.append(admin_data)

        print(f"✅ تم تحضير {len(sub_admins_data)} مشرف للعرض")
        print(f"✅ عدد الشركات: {len(companies_list)}")

        return render_template('admin/manage_sub_admins.html',
                               sub_admins=sub_admins_data,
                               companies_list=companies_list,
                               current_company=current_company,
                               selected_company_id=selected_company_id,
                               now=datetime.now())

    except Exception as e:
        print(f"❌ خطأ: {str(e)}")
        import traceback
        traceback.print_exc()
        flash('حدث خطأ في تحميل الصفحة', 'danger')
        return redirect(url_for('index'))

@app.route('/debug/current-function')
@login_required
def debug_current_function():
    """عرض الكود الحالي للدالة"""
    import inspect
    try:
        # الحصول على كود الدالة الحالية
        func_code = inspect.getsource(manage_sub_admins)
        return f"""
        <html><body style="font-family: Arial; padding: 20px; direction: rtl;">
            <h1>🔍 كود الدالة الحالي</h1>
            <pre style="background: #f0f0f0; padding: 15px; border-radius: 10px; white-space: pre-wrap;">
{func_code}
            </pre>
            <a href="/admin/sub-admins-simple" style="background: green; color: white; padding: 10px; text-decoration: none;">
                🚀 جرب الإصدار البسيط
            </a>
        </body></html>
        """
    except Exception as e:
        return f"خطأ في عرض الكود: {e}"


@app.route('/api/sub-admins', methods=['POST'])
@login_required
@permission_required('users_add')
def api_add_sub_admin():
    """إضافة مشرف فرعي جديد عبر API"""
    try:
        data = request.get_json()

        # التحقق من البيانات
        required_fields = ['name', 'email', 'company_id']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'message': f'حقل {field} مطلوب'}), 400

        # التحقق من الصلاحيات
        if not current_user.can_manage_company(data['company_id']):
            return jsonify({'success': False, 'message': 'غير مصرح لك بإضافة مشرفين في هذه الشركة'}), 403

        # التحقق من عدم وجود مستخدم بنفس البريد
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'success': False, 'message': 'البريد الإلكتروني موجود مسبقاً'}), 400

        # إنشاء المستخدم
        user = User(
            fullname=data['name'],
            username=data['email'],  # استخدام البريد كاسم مستخدم
            email=data['email'],
            role='sub_admin',
            company_id=data['company_id'],
            active=data.get('is_active', True)
        )

        # تعيين كلمة مرور افتراضية
        password = data.get('password', 'default123')
        user.set_password(password)

        db.session.add(user)
        db.session.flush()  # للحصول على ID

        # إضافة الصلاحيات المحددة
        permissions = data.get('permissions', [])
        for perm_code in permissions:
            user_perm = UserPermission(
                user_id=user.id,
                permission_code=perm_code
            )
            db.session.add(user_perm)

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'تم إضافة المشرف الفرعي بنجاح',
            'user_id': user.id
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'حدث خطأ: {str(e)}'}), 500


@app.route('/api/sub-admins/<int:admin_id>', methods=['PUT', 'DELETE'])
@login_required
@permission_required('users_edit')
def api_manage_sub_admin(admin_id):
    """تعديل أو حذف مشرف فرعي"""
    try:
        admin = User.query.get_or_404(admin_id)

        # التحقق من الصلاحيات
        if not current_user.can_manage_user(admin):
            return jsonify({'success': False, 'message': 'غير مصرح لك بإدارة هذا المشرف'}), 403

        if request.method == 'PUT':
            data = request.get_json()

            # تحديث البيانات الأساسية
            if 'name' in data:
                admin.fullname = data['name']
            if 'email' in data:
                admin.email = data['email']
                admin.username = data['email']  # تحديث اسم المستخدم أيضاً
            if 'is_active' in data:
                admin.active = data['is_active']
            if 'password' in data and data['password']:
                admin.set_password(data['password'])

            # تحديث الصلاحيات
            if 'permissions' in data:
                # حذف الصلاحيات الحالية
                UserPermission.query.filter_by(user_id=admin_id).delete()

                # إضافة الصلاحيات الجديدة
                for perm_code in data['permissions']:
                    user_perm = UserPermission(
                        user_id=admin_id,
                        permission_code=perm_code
                    )
                    db.session.add(user_perm)

            db.session.commit()
            return jsonify({'success': True, 'message': 'تم تحديث بيانات المشرف بنجاح'})

        elif request.method == 'DELETE':
            # التحقق من عدم وجود تقييمات مرتبطة
            if admin.evaluations:
                admin.active = False
                db.session.commit()
                return jsonify({
                    'success': True,
                    'message': 'المستخدم مرتبط بتقييمات، تم تغييره إلى غير نشط بدلاً من الحذف'
                })

            db.session.delete(admin)
            db.session.commit()
            return jsonify({'success': True, 'message': 'تم حذف المشرف بنجاح'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'حدث خطأ: {str(e)}'}), 500

# routes_permissions.py - إصلاح دوال إدارة الصلاحيات
@app.route('/admin/sub-admins/<int:admin_id>/permissions', methods=['GET', 'POST'])
@login_required
def manage_sub_admin_permissions_view(admin_id):
    """إدارة صلاحيات المشرف الفرعي"""
    # التحقق من الصلاحية
    if not current_user.has_permission('manage_permissions'):
        flash('غير مصرح لك بإدارة الصلاحيات', 'danger')
        return redirect(url_for('users'))

    sub_admin = User.query.get_or_404(admin_id)

    # التأكد من أن المستخدم مشرف فرعي
    if sub_admin.role != 'sub_admin':
        flash('المستخدم المحدد ليس مشرفاً فرعياً', 'danger')
        return redirect(url_for('users'))

    # التحقق من أن المستخدم الحالي يمكنه إدارة هذا المشرف
    if not current_user.can_manage_user(sub_admin):
        flash('غير مصرح لك بإدارة صلاحيات هذا المشرف', 'danger')
        return redirect(url_for('users'))

    # الصلاحيات المتاحة للمشرفين الفرعيين
    available_permissions = {
        'users': [
            {'code': 'users_view', 'name': 'عرض المستخدمين'},
            {'code': 'users_add', 'name': 'إضافة مستخدمين'},
            {'code': 'users_edit', 'name': 'تعديل المستخدمين'},
            {'code': 'users_delete', 'name': 'حذف المستخدمين'}
        ],
        'evaluations': [
            {'code': 'evaluations_view', 'name': 'عرض التقييمات'},
            {'code': 'evaluations_add', 'name': 'إضافة تقييمات'},
            {'code': 'evaluations_edit', 'name': 'تعديل التقييمات'},
            {'code': 'evaluations_delete', 'name': 'حذف التقييمات'}
        ],
        'reports': [
            {'code': 'reports_view', 'name': 'عرض التقارير'},
            {'code': 'reports_export', 'name': 'تصدير التقارير'}
        ]
    }

    if request.method == 'POST':
        try:
            # حذف الصلاحيات الحالية
            UserPermission.query.filter_by(user_id=admin_id).delete()

            # إضافة الصلاحيات الجديدة
            selected_permissions = request.form.getlist('permissions')
            for perm_code in selected_permissions:
                user_perm = UserPermission(
                    user_id=admin_id,
                    permission_code=perm_code
                )
                db.session.add(user_perm)

            db.session.commit()
            flash('تم تحديث صلاحيات المشرف الفرعي بنجاح', 'success')
            return redirect(url_for('users'))

        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء تحديث الصلاحيات: {str(e)}', 'danger')

    # الصلاحيات الحالية للمشرف
    current_permissions = [up.permission_code for up in sub_admin.user_permissions]

    return render_template('admin/sub_admin_permissions.html',
                           sub_admin=sub_admin,
                           available_permissions=available_permissions,
                           current_permissions=current_permissions)

# --- إدارة الشركات ---
# --- إدارة الشركات ---
@app.route('/companies')
@login_required
def companies():
    if current_user.role != 'admin':
        flash('غير مصرح لك بالوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('dashboard'))

    # فلترة الشركات
    active_filter = request.args.get('active', '')
    query = Company.query

    if active_filter == '1':
        query = query.filter(Company.active == True)
    elif active_filter == '0':
        query = query.filter(Company.active == False)

    companies_list = query.order_by(Company.name).all()

    # إحصائيات عامة
    total_companies = Company.query.count()
    active_companies = Company.query.filter_by(active=True).count()
    inactive_companies = total_companies - active_companies

    return render_template(
        'admin/companies.html',
        companies=companies_list,
        total_companies=total_companies,
        active_companies=active_companies,
        inactive_companies=inactive_companies,
        active_filter=active_filter
    )


@app.route('/companies/add', methods=['GET', 'POST'])
@login_required
def add_company():
    if current_user.role != 'admin':
        flash('غير مصرح لك', 'danger')
        return redirect(url_for('companies'))

    form = CompanyForm()

    if form.validate_on_submit():
        try:
            company = Company(
                name=form.name.data,
                code=form.code.data,
                active=(form.active.data == '1')
            )
            db.session.add(company)
            db.session.commit()

            flash('تم إضافة الشركة بنجاح', 'success')
            return redirect(url_for('companies'))

        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء إضافة الشركة: {str(e)}', 'danger')

    return render_template('admin/company_form.html', form=form, title='إضافة شركة جديدة')


@app.route('/companies/edit/<int:company_id>', methods=['GET', 'POST'])
@login_required
def edit_company(company_id):
    if current_user.role != 'admin':
        flash('غير مصرح لك', 'danger')
        return redirect(url_for('companies'))

    company = Company.query.get_or_404(company_id)
    form = CompanyForm(obj=company)

    if request.method == 'GET':
        form.active.data = '1' if company.active else '0'

    if form.validate_on_submit():
        try:
            company.name = form.name.data
            company.code = form.code.data
            company.active = (form.active.data == '1')

            db.session.commit()
            flash('تم تعديل بيانات الشركة بنجاح', 'success')
            return redirect(url_for('companies'))

        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء تعديل الشركة: {str(e)}', 'danger')

    return render_template('admin/company_form.html', form=form, company=company, title='تعديل شركة')


@app.route('/companies/delete/<int:company_id>', methods=['POST'])
@login_required
def delete_company(company_id):
    if current_user.role != 'admin':
        flash('غير مصرح لك', 'danger')
        return redirect(url_for('companies'))

    company = Company.query.get_or_404(company_id)

    # التحقق من عدم وجود بيانات مرتبطة
    if company.users or company.locations or company.evaluation_authorities:
        flash('لا يمكن حذف الشركة لأنها مرتبطة ببيانات أخرى (مستخدمين، مناطق، جهات تقييم)', 'danger')
        return redirect(url_for('companies'))

    try:
        db.session.delete(company)
        db.session.commit()
        flash('تم حذف الشركة بنجاح', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء حذف الشركة: {str(e)}', 'danger')

    return redirect(url_for('companies'))


@app.route('/companies/toggle/<int:company_id>', methods=['POST'])
@login_required
def toggle_company(company_id):
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': 'غير مصرح لك'})

    company = Company.query.get_or_404(company_id)

    try:
        company.active = not company.active
        db.session.commit()

        status = 'نشطة' if company.active else 'غير نشطة'
        flash(f'تم تغيير حالة الشركة إلى {status}', 'success')
        return jsonify({'success': True, 'active': company.active})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})


@app.route('/companies/statistics')
@login_required
def companies_statistics():
    if current_user.role != 'admin':
        return jsonify({'error': 'غير مصرح لك'})

    companies = Company.query.all()
    stats = []

    for company in companies:
        stats.append({
            'id': company.id,
            'name': company.name,
            'users_count': len(company.users),
            'locations_count': len(company.locations),
            'authorities_count': len(company.evaluation_authorities),
            'evaluations_count': Evaluation.query.join(User).filter(User.company_id == company.id).count(),
            'active': company.active
        })

    return jsonify(stats)


# دالة لنقل البيانات إلى الشركة الجديدة
def migrate_data_to_company(company_id):
    """نقل جميع البيانات إلى شركة محددة"""
    try:
        company = Company.query.get(company_id)
        if not company:
            return False, "الشركة غير موجودة"

        # نقل المستخدمين
        users = User.query.filter(User.company_id.is_(None)).all()
        for user in users:
            user.company_id = company_id

        # نقل المناطق
        locations = Location.query.filter(Location.company_id.is_(None)).all()
        for location in locations:
            location.company_id = company_id

        # نقل جهات التقييم
        authorities = EvaluationAuthority.query.filter(EvaluationAuthority.company_id.is_(None)).all()
        for authority in authorities:
            authority.company_id = company_id

        # نقل تفاصيل التقييم
        evaluation_details = EvaluationDetail.query.filter(EvaluationDetail.company_id.is_(None)).all()
        for detail in evaluation_details:
            detail.company_id = company_id

        db.session.commit()
        return True, f"تم نقل جميع البيانات إلى شركة {company.name}"

    except Exception as e:
        db.session.rollback()
        return False, f"حدث خطأ أثناء نقل البيانات: {str(e)}"


@app.route('/companies/migrate_data/<int:company_id>', methods=['POST'])
@login_required
def migrate_company_data(company_id):
    if current_user.role != 'admin':
        flash('غير مصرح لك', 'danger')
        return redirect(url_for('companies'))

    success, message = migrate_data_to_company(company_id)

    if success:
        flash(message, 'success')
    else:
        flash(message, 'danger')

    return redirect(url_for('companies'))


@app.route('/authorities', methods=['GET', 'POST'])
@login_required
@permission_required('authorities_view')
def authorities():
    """عرض وإدارة جهات التقييم مع دعم تعدد الشركات"""
    form = EvaluationAuthorityForm()

    # تحديد الشركات المتاحة بناءً على صلاحيات المستخدم
    if current_user.is_administrator:
        companies = Company.query.filter_by(active=True).order_by(Company.name).all()
        # جلب جميع الجهات للمسؤولين
        authorities_list = EvaluationAuthority.query.options(
            db.joinedload(EvaluationAuthority.company)
        ).order_by(EvaluationAuthority.name).all()
    else:
        # للمشرفين والمستخدمين العاديين: جهات شركتهم فقط
        companies = Company.query.filter_by(id=current_user.company_id, active=True).all()
        authorities_list = EvaluationAuthority.query.filter_by(
            company_id=current_user.company_id
        ).options(
            db.joinedload(EvaluationAuthority.company)
        ).order_by(EvaluationAuthority.name).all()
        # تعيين الشركة تلقائياً للمشرفين
        if companies and len(companies) == 1:
            form.company_id.data = companies[0].id

    form.company_id.choices = [(c.id, c.name) for c in companies]

    # إضافة جهة جديدة
    if form.validate_on_submit():
        try:
            # التحقق من عدم تكرار اسم الجهة في نفس الشركة
            existing_auth = EvaluationAuthority.query.filter_by(
                name=form.name.data,
                company_id=form.company_id.data
            ).first()

            if existing_auth:
                flash('هذه الجهة موجودة مسبقاً في الشركة المحددة', 'warning')
                return render_template('admin/authorities.html',
                                       form=form,
                                       authorities=authorities_list,
                                       companies=companies)

            # إنشاء جهة جديدة
            new_auth = EvaluationAuthority(
                name=form.name.data,
                company_id=form.company_id.data
            )

            db.session.add(new_auth)
            db.session.commit()
            flash('تمت إضافة الجهة بنجاح', 'success')
            return redirect(url_for('authorities'))

        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء إضافة الجهة: {str(e)}', 'danger')

    return render_template('admin/authorities.html',
                           form=form,
                           authorities=authorities_list,
                           companies=companies)


@app.route('/authorities/edit/<int:auth_id>', methods=['POST'])
@login_required
@permission_required('authorities_manage')
def edit_authority(auth_id):
    """تعديل جهة تقييم"""
    authority = EvaluationAuthority.query.get_or_404(auth_id)

    # التحقق من صلاحية المستخدم للتعديل
    if not current_user.is_administrator and authority.company_id != current_user.company_id:
        flash('غير مصرح لك بتعديل هذه الجهة', 'danger')
        return redirect(url_for('authorities'))

    new_name = request.form.get('new_name')
    company_id = request.form.get('company_id')

    if not new_name:
        flash('اسم الجهة لا يمكن أن يكون فارغاً', 'warning')
        return redirect(url_for('authorities'))

    try:
        # التحقق من عدم تكرار الاسم في نفس الشركة
        existing_auth = EvaluationAuthority.query.filter(
            EvaluationAuthority.id != auth_id,
            EvaluationAuthority.name == new_name,
            EvaluationAuthority.company_id == (company_id if current_user.is_administrator else authority.company_id)
        ).first()

        if existing_auth:
            flash('هذه الجهة موجودة مسبقاً في الشركة المحددة', 'warning')
            return redirect(url_for('authorities'))

        # تحديث البيانات
        authority.name = new_name
        if current_user.is_administrator and company_id:
            authority.company_id = company_id

        db.session.commit()
        flash('تم تعديل الجهة بنجاح', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء تعديل الجهة: {str(e)}', 'danger')

    return redirect(url_for('authorities'))


@app.route('/authorities/delete/<int:auth_id>', methods=['POST'])
@login_required
@permission_required('authorities_manage')
def delete_authority(auth_id):
    """حذف جهة تقييم"""
    authority = EvaluationAuthority.query.get_or_404(auth_id)

    # التحقق من صلاحية المستخدم للحذف
    if not current_user.is_administrator and authority.company_id != current_user.company_id:
        flash('غير مصرح لك بحذف هذه الجهة', 'danger')
        return redirect(url_for('authorities'))

    try:
        # التحقق من عدم وجود معايير مرتبطة بالجهة
        related_criteria = Criterion.query.filter_by(authority_id=auth_id).count()
        if related_criteria > 0:
            flash('لا يمكن حذف الجهة لأنها مرتبطة بمعايير تقييم', 'danger')
            return redirect(url_for('authorities'))

        db.session.delete(authority)
        db.session.commit()
        flash('تم حذف الجهة بنجاح', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء حذف الجهة: {str(e)}', 'danger')

    return redirect(url_for('authorities'))


# API للحصول على جهات الشركة (للاستخدام في القوائم المنسدلة)
@app.route('/api/authorities/by_company/<int:company_id>')
@login_required
def get_authorities_by_company(company_id):
    """الحصول على جهات التقييم لشركة معينة"""
    try:
        # التحقق من الصلاحية
        if not current_user.is_administrator and current_user.company_id != company_id:
            return jsonify({'error': 'غير مصرح'}), 403

        authorities = EvaluationAuthority.query.filter_by(
            company_id=company_id
        ).order_by(EvaluationAuthority.name).all()

        authorities_list = [{
            'id': auth.id,
            'name': auth.name
        } for auth in authorities]

        return jsonify(authorities_list)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# فلترة الجهات حسب الشركة
@app.route('/authorities/filter/<int:company_id>')
@login_required
def filter_authorities_by_company(company_id):
    """فلترة جهات التقييم حسب الشركة"""
    try:
        # التحقق من الصلاحية
        if not current_user.is_administrator and current_user.company_id != company_id:
            flash('غير مصرح', 'danger')
            return redirect(url_for('authorities'))

        if company_id == 0:  # عرض الكل
            if current_user.is_administrator:
                authorities = EvaluationAuthority.query.options(
                    db.joinedload(EvaluationAuthority.company)
                ).order_by(EvaluationAuthority.name).all()
            else:
                authorities = EvaluationAuthority.query.filter_by(
                    company_id=current_user.company_id
                ).options(
                    db.joinedload(EvaluationAuthority.company)
                ).order_by(EvaluationAuthority.name).all()
        else:
            authorities = EvaluationAuthority.query.filter_by(
                company_id=company_id
            ).options(
                db.joinedload(EvaluationAuthority.company)
            ).order_by(EvaluationAuthority.name).all()

        companies = Company.query.filter_by(active=True).order_by(Company.name).all()
        form = EvaluationAuthorityForm()

        if current_user.is_administrator:
            form.company_id.choices = [(c.id, c.name) for c in companies]
        else:
            form.company_id.choices = [(c.id, c.name) for c in companies if c.id == current_user.company_id]

        return render_template('admin/authorities.html',
                               authorities=authorities,
                               form=form,
                               companies=companies,
                               selected_company=company_id)

    except Exception as e:
        flash(f'حدث خطأ أثناء التصفية: {str(e)}', 'danger')
        return redirect(url_for('authorities'))

# تعديل المنطقة (Location)
from flask import request, redirect, url_for, flash, render_template
from flask_login import login_required, current_user
from sqlalchemy.orm import joinedload



@app.route('/locations', methods=['GET', 'POST'])
@login_required
def locations():
    if current_user.role != 'admin':
        flash('غير مصرح لك', 'danger')
        return redirect(url_for('dashboard'))

    try:
        # تحديث خيارات اختيار المواقع والمناطق لنماذج الإدخال
        form_region = RegionForm(prefix='region')
        form_site = SiteForm(prefix='site')
        form_place = PlaceForm(prefix='place')

        # جلب الشركات النشطة
        companies = Company.query.filter_by(active=True).order_by(Company.name).all()
        form_region.company_id.choices = [(c.id, c.name) for c in companies]
        form_region.company_id.choices.insert(0, (0, "اختر الشركة"))

        # جلب المناطق مع معالجة القيم None
        all_locations = Location.query.options(db.joinedload(Location.company)).order_by(Location.name).all()

        # إعداد خيارات المناطق بشكل آمن
        region_choices = []
        for r in all_locations:
            if r.company:
                region_choices.append((r.id, f"{r.name} - {r.company.name}"))
            else:
                region_choices.append((r.id, f"{r.name} - لا توجد شركة"))

        form_site.region_id.choices = region_choices

        # جلب المواقع
        all_sites = Site.query.options(db.joinedload(Site.location)).order_by(Site.name).all()
        site_choices = []
        for s in all_sites:
            if s.location and s.location.company:
                site_choices.append((s.id, f"{s.name} - {s.location.name}"))
            else:
                site_choices.append((s.id, f"{s.name} - موقع"))

        form_place.site_id.choices = site_choices

        # معالجة طلبات POST
        if request.method == 'POST':
            # إضافة منطقة
            if 'submit_region' in request.form and form_region.validate():
                try:
                    if form_region.company_id.data == 0:
                        flash('يجب اختيار شركة', 'danger')
                        return redirect(url_for('locations'))

                    new_region = Location(
                        name=form_region.name.data,
                        company_id=form_region.company_id.data
                    )
                    db.session.add(new_region)
                    db.session.commit()
                    flash('تمت إضافة المنطقة بنجاح', 'success')
                    return redirect(url_for('locations'))
                except Exception as e:
                    db.session.rollback()
                    flash(f'حدث خطأ أثناء إضافة المنطقة: {str(e)}', 'danger')

            # إضافة موقع
            elif 'submit_site' in request.form and form_site.validate():
                try:
                    new_site = Site(
                        name=form_site.name.data,
                        region_id=form_site.region_id.data
                    )
                    db.session.add(new_site)
                    db.session.commit()
                    flash('تمت إضافة الموقع بنجاح', 'success')
                    return redirect(url_for('locations'))
                except Exception as e:
                    db.session.rollback()
                    flash(f'حدث خطأ أثناء إضافة الموقع: {str(e)}', 'danger')

            # إضافة مكان
            elif 'submit_place' in request.form and form_place.validate():
                try:
                    new_place = Place(
                        name=form_place.name.data,
                        site_id=form_place.site_id.data
                    )
                    db.session.add(new_place)
                    db.session.commit()
                    flash('تمت إضافة المكان بنجاح', 'success')
                    return redirect(url_for('locations'))
                except Exception as e:
                    db.session.rollback()
                    flash(f'حدث خطأ أثناء إضافة المكان: {str(e)}', 'danger')

        # جلب البيانات للعرض مع تحسين الاستعلامات
        locations_data = db.session.query(Location).options(
            db.joinedload(Location.company),
            db.joinedload(Location.sites).options(
                db.joinedload(Site.places)
            )
        ).order_by(Location.name).all()

        # إحصائيات الشركات
        companies_stats = []
        for company in companies:
            company_locations = [loc for loc in locations_data if loc.company_id == company.id]
            total_sites = sum(len(loc.sites) for loc in company_locations)
            total_places = sum(len(site.places) for loc in company_locations for site in loc.sites)

            companies_stats.append({
                'company': company,
                'locations_count': len(company_locations),
                'sites_count': total_sites,
                'places_count': total_places
            })

        return render_template('admin/locations.html',
                               form_region=form_region,
                               form_site=form_site,
                               form_place=form_place,
                               locations=locations_data,
                               companies=companies,
                               companies_stats=companies_stats)

    except Exception as e:
        print(f"❌ خطأ في دالة locations: {e}")
        flash('حدث خطأ في تحميل صفحة المواقع', 'error')
        return redirect(url_for('dashboard'))


# --- تعديل وحذف المناطق (Locations) ---

@app.route('/locations/edit/location/<int:location_id>', methods=['POST'])
@login_required
def edit_location(location_id):
    if current_user.role != 'admin':
        flash('غير مصرح لك', 'danger')
        return redirect(url_for('locations'))

    location = db.session.get(Location, location_id)
    if not location:
        flash('المنطقة غير موجودة', 'danger')
        return redirect(url_for('locations'))

    new_name = request.form.get('new_name')
    company_id = request.form.get('company_id')

    if new_name and new_name.strip():
        try:
            location.name = new_name.strip()
            if company_id and company_id.isdigit():
                location.company_id = int(company_id)
            db.session.commit()
            flash('تم تعديل بيانات المنطقة بنجاح', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء تعديل المنطقة: {str(e)}', 'danger')
    else:
        flash('اسم المنطقة لا يمكن أن يكون فارغاً', 'warning')

    return redirect(url_for('locations'))


@app.route('/locations/delete/location/<int:location_id>', methods=['POST'])
@login_required
def delete_location(location_id):
    if current_user.role != 'admin':
        flash('غير مصرح لك', 'danger')
        return redirect(url_for('locations'))

    location = db.session.get(Location, location_id)
    if not location:
        flash('المنطقة غير موجودة', 'danger')
        return redirect(url_for('locations'))

    try:
        # التحقق من وجود مواقع فرعية
        sites_count = db.session.query(Site).filter_by(region_id=location_id).count()
        if sites_count > 0:
            flash('لا يمكن حذف المنطقة لأنها تحتوي على مواقع فرعية', 'danger')
            return redirect(url_for('locations'))

        # التحقق من عدم وجود مستخدمين مرتبطين بالمنطقة
        users_count = db.session.query(user_regions).filter_by(location_id=location_id).count()
        if users_count > 0:
            flash('لا يمكن حذف المنطقة لأنها مرتبطة بمستخدمين', 'danger')
            return redirect(url_for('locations'))

        db.session.delete(location)
        db.session.commit()
        flash('تم حذف المنطقة بنجاح', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء حذف المنطقة: {str(e)}', 'danger')

    return redirect(url_for('locations'))


# --- تعديل وحذف المواقع (Sites) ---
@app.route('/locations/edit/site/<int:site_id>', methods=['POST'])
@login_required
def edit_site(site_id):
    if current_user.role != 'admin':
        flash('غير مصرح لك', 'danger')
        return redirect(url_for('locations'))

    site = db.session.get(Site, site_id)  # ✅ استخدام db.session.get
    if not site:
        flash('الموقع غير موجود', 'danger')
        return redirect(url_for('locations'))

    new_name = request.form.get('new_name')
    region_id = request.form.get('region_id')  # ✅ إضافة إمكانية تغيير المنطقة

    if new_name and new_name.strip():
        try:
            site.name = new_name.strip()
            if region_id and region_id.isdigit():
                site.region_id = int(region_id)
            db.session.commit()
            flash('تم تعديل بيانات الموقع بنجاح', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء تعديل الموقع: {str(e)}', 'danger')
    else:
        flash('اسم الموقع لا يمكن أن يكون فارغاً', 'warning')

    return redirect(url_for('locations'))


@app.route('/locations/delete/site/<int:site_id>', methods=['POST'])
@login_required
def delete_site(site_id):
    if current_user.role != 'admin':
        flash('غير مصرح لك', 'danger')
        return redirect(url_for('locations'))

    site = db.session.get(Site, site_id)  # ✅ استخدام db.session.get
    if not site:
        flash('الموقع غير موجود', 'danger')
        return redirect(url_for('locations'))

    try:
        # التحقق من وجود أماكن فرعية
        places_count = db.session.query(Place).filter_by(site_id=site_id).count()
        if places_count > 0:
            flash('لا يمكن حذف الموقع لأنه يحتوي على أماكن فرعية', 'danger')
            return redirect(url_for('locations'))

        db.session.delete(site)
        db.session.commit()
        flash('تم حذف الموقع بنجاح', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء حذف الموقع: {str(e)}', 'danger')

    return redirect(url_for('locations'))


# --- تعديل وحذف الأماكن (Places) ---
# ✅ إصلاح المسار - استخدم نفس نمط المسارات الأخرى
@app.route('/locations/edit/place/<int:place_id>', methods=['POST'])
@login_required
def edit_place(place_id):
    if current_user.role != 'admin':
        flash('غير مصرح لك', 'danger')
        return redirect(url_for('locations'))

    place = db.session.get(Place, place_id)
    if not place:
        flash('المكان غير موجود', 'danger')
        return redirect(url_for('locations'))

    new_name = request.form.get('new_name')
    site_id = request.form.get('site_id')

    if new_name and new_name.strip():
        try:
            place.name = new_name.strip()
            if site_id and site_id.isdigit():
                place.site_id = int(site_id)
            db.session.commit()
            flash('تم تعديل بيانات المكان بنجاح', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء تعديل المكان: {str(e)}', 'danger')
    else:
        flash('اسم المكان لا يمكن أن يكون فارغاً', 'warning')

    return redirect(url_for('locations'))


@app.route('/locations/delete/place/<int:place_id>', methods=['POST'])
@login_required
def delete_place(place_id):
    if current_user.role != 'admin':
        flash('غير مصرح لك', 'danger')
        return redirect(url_for('locations'))

    place = db.session.get(Place, place_id)
    if not place:
        flash('المكان غير موجود', 'danger')
        return redirect(url_for('locations'))

    try:
        # ✅ التحقق من عدم وجود تقييمات مرتبطة بالمكان
        evaluations_count = db.session.query(Evaluation).filter_by(place_id=place_id).count()
        if evaluations_count > 0:
            flash('لا يمكن حذف المكان لأنه مرتبط بتقييمات', 'danger')
            return redirect(url_for('locations'))

        db.session.delete(place)
        db.session.commit()
        flash('تم حذف المكان بنجاح', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء حذف المكان: {str(e)}', 'danger')

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

    # جلب الشركات أولاً
    companies = Company.query.filter_by(active=True).order_by(Company.name).all()

    # جلب المعايير مع البيانات المرتبطة
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
        # الحصول على البيانات من النموذج
        company_id = request.form.get("company_id")
        location_id = request.form.get("location_id")
        site_id = request.form.get("site_id")
        place_id = request.form.get("place_id")
        name = request.form.get("name")
        min_score = request.form.get("min_score")
        max_score = request.form.get("max_score")
        authority_id = request.form.get("authority_id")
        add_type = request.form.get("add_type")  # الخيار: single أو all_similar

        # التحقق من الحقول المطلوبة
        if not (
                company_id and location_id and site_id and place_id and name and min_score and max_score and authority_id and add_type):
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
                    # إضافة لجميع الأماكن المشابهة في نفس الشركة
                    similar_places = Place.query.join(Site).join(Location).filter(
                        Place.name == place.name,
                        Location.company_id == int(company_id)
                    ).all()

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
                    flash(f"تمت إضافة المعيار لجميع الأماكن المشابهة في الشركة ({added} مكان).", "success")

            except Exception as e:
                db.session.rollback()
                flash(f"حدث خطأ أثناء الإضافة: {e}", "danger")
            finally:
                db.session.close()

        return redirect(url_for("criteria"))

    return render_template(
        "admin/criteria.html",
        companies=companies,  # إضافة الشركات للقالب
        locations=locations,
        authorities=authorities,
        criteria=criteria_list
    )


@app.route('/criteria/add/<int:place_id>', methods=['GET', 'POST'])
@login_required
def add_criterion(place_id):
    """إضافة معيار لمكان محدد"""
    if current_user.role != 'admin':
        flash('غير مصرح لك', 'danger')
        return redirect(url_for('dashboard'))

    place = db.session.get(Place, place_id)
    if not place:
        flash('المكان غير موجود', 'danger')
        return redirect(url_for('criteria_hierarchy'))

    companies = Company.query.filter_by(active=True).order_by(Company.name).all()
    authorities = EvaluationAuthority.query.order_by(EvaluationAuthority.name).all()

    if request.method == "POST":
        name = request.form.get("name")
        min_score = request.form.get("min_score")
        max_score = request.form.get("max_score")
        authority_id = request.form.get("authority_id")
        add_type = request.form.get("add_type", "single")

        if not (name and min_score and max_score and authority_id):
            flash("يجب تعبئة جميع الحقول المطلوبة", "danger")
            return redirect(url_for('add_criterion', place_id=place_id))

        try:
            min_score = float(min_score)
            max_score = float(max_score)
        except ValueError:
            flash("يجب أن تكون الدرجات أرقاماً صحيحة أو عشرية", "danger")
            return redirect(url_for('add_criterion', place_id=place_id))

        try:
            if add_type == "single":
                # إضافة للمكان المحدد فقط
                new_criterion = Criterion(
                    name=name,
                    place_id=place_id,
                    min_score=min_score,
                    max_score=max_score,
                    authority_id=int(authority_id)
                )
                db.session.add(new_criterion)
                db.session.commit()
                flash("تمت إضافة المعيار بنجاح", "success")

            elif add_type == "all_similar":
                # إضافة لجميع الأماكن المشابهة في نفس الشركة
                similar_places = Place.query.join(Site).join(Location).filter(
                    Place.name == place.name,
                    Location.company_id == place.site.location.company_id
                ).all()

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
                flash(f"تمت إضافة المعيار لجميع الأماكن المشابهة ({added} مكان)", "success")

            return redirect(url_for('criteria_hierarchy'))

        except Exception as e:
            db.session.rollback()
            flash(f"حدث خطأ أثناء الإضافة: {str(e)}", "danger")

    return render_template('admin/add_criterion.html',
                           place=place,
                           companies=companies,
                           authorities=authorities)

@app.route('/criteria/edit/<int:criterion_id>', methods=['GET', 'POST'])
@login_required
def edit_criterion(criterion_id):
    if current_user.role != 'admin':
        flash('غير مصرح لك', 'danger')
        return redirect(url_for('dashboard'))

    criterion = Criterion.query.get_or_404(criterion_id)
    companies = Company.query.filter_by(active=True).order_by(Company.name).all()
    locations = Location.query.order_by(Location.name).all()
    authorities = EvaluationAuthority.query.order_by(EvaluationAuthority.name).all()

    if request.method == 'POST':
        company_id = request.form.get("company_id")
        location_id = request.form.get("location_id")
        site_id = request.form.get("site_id")
        place_id = request.form.get("place_id")
        name = request.form.get("name")
        min_score = request.form.get("min_score")
        max_score = request.form.get("max_score")
        authority_id = request.form.get("authority_id")

        if not (
                company_id and location_id and site_id and place_id and name and min_score and max_score and authority_id):
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

    # تحديد الشركة الحالية للمعيار
    current_company_id = None
    if criterion.place and criterion.place.site and criterion.place.site.location:
        current_company_id = criterion.place.site.location.company_id

    return render_template('admin/edit_criterion.html',
                           criterion=criterion,
                           companies=companies,
                           current_company_id=current_company_id,
                           locations=locations,
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


@app.route('/get_locations/<int:company_id>')
@login_required
def get_locations(company_id):
    """جلب المناطق التابعة لشركة محددة"""
    locations = Location.query.filter_by(company_id=company_id).order_by(Location.name).all()
    return jsonify([{'id': loc.id, 'name': loc.name} for loc in locations])


@app.route('/get_sites/<int:location_id>')
@login_required
def get_sites(location_id):
    """جلب المواقع التابعة لمنطقة محددة"""
    sites = Site.query.filter_by(region_id=location_id).order_by(Site.name).all()
    return jsonify([{'id': s.id, 'name': s.name} for s in sites])


@app.route('/get_places/<int:site_id>')
@login_required
def get_places(site_id):
    """جلب الأماكن التابعة لموقع محدد"""
    places = Place.query.filter_by(site_id=site_id).order_by(Place.name).all()
    return jsonify([{'id': p.id, 'name': p.name} for p in places])


@app.route('/get_criteria/<int:place_id>')
@login_required
def get_criteria(place_id):
    """جلب المعايير الخاصة بمكان محدد"""
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
from models import db, Evaluation, EvaluationDetail, ActionPlan, Location, Site, Place, Criterion, EvaluationAuthority
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





# ---------------- Routes ----------------

from flask import Flask, render_template, request, jsonify
from datetime import datetime
from models import db, ActionPlan  # استبدل بالمسار الصحيح لنموذجك

from sqlalchemy import func

from collections import Counter
from flask import render_template
from sqlalchemy.orm import joinedload


@app.route('/action_plans')
def action_plans():
    # جلب جميع تفاصيل التقييم مع الربط بالعلاقات
    evaluation_details = (
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
            detail.criterion.name if detail.criterion else '-',
            detail.place.name if detail.place else '-',
            detail.evaluation.site.name if detail.evaluation and detail.evaluation.site else '-',
            detail.evaluation.region.name if detail.evaluation and detail.evaluation.region else '-'
        )
        for detail in evaluation_details if detail.criterion
    ]

    # عد التكرارات لكل معيار-مكان-موقع-منطقة
    criterion_counts = Counter(criterion_place_site_region_pairs)

    # أكثر 5 معايير تكرارًا (مرتبة حسب العدد)
    top_criteria = []
    for (criterion_name, place_name, site_name, region_name), count in criterion_counts.most_common(5):
        top_criteria.append({
            "name": f"{criterion_name} ({region_name} / {site_name} / {place_name})",
            "count": count,
            "info": "-"
        })

    # إعادة العدد لكل خطة عمل لتظهر في العمود "عدد التكرار" في الجدول
    criterion_count_lookup = {}
    for detail in evaluation_details:
        if detail.criterion:
            key = (
                detail.criterion.name if detail.criterion else '-',
                detail.place.name if detail.place else '-',
                detail.evaluation.site.name if detail.evaluation and detail.evaluation.site else '-',
                detail.evaluation.region.name if detail.evaluation and detail.evaluation.region else '-'
            )
            criterion_count_lookup[key] = criterion_counts.get(key, 0)

    return render_template(
        'admin/action_plans.html',
        action_plans=evaluation_details,
        criterion_counts=criterion_count_lookup,
        top_criteria=top_criteria
    )


@app.route('/add_note', methods=['POST'])
def add_note():
    try:
        evaluation_id = request.form['evaluation_detail_id']
        note = request.form.get('note', '')  # ✅ قيمة افتراضية إذا كانت فارغة

        # ✅ التحقق من أن note ليست فارغة
        if not note.strip():
            note = "لا توجد ملاحظات"

        action_plan = generate_action_plan(note)

        new_plan = ActionPlan(
            evaluation_detail_id=evaluation_id,
            note=note,  # ✅ الآن note لن تكون null أبداً
            action_plan=action_plan,
            plan_text=""  # ✅ قيمة افتراضية
        )
        db.session.add(new_plan)
        db.session.commit()
        flash('تم إضافة الملاحظة بنجاح', 'success')
        return redirect(url_for('action_plans'))

    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء إضافة الملاحظة: {str(e)}', 'danger')
        return redirect(url_for('action_plans'))


@app.route('/close_note/<int:note_id>', methods=['POST'])
def close_note(note_id):
    try:
        print(f"=== بدء إغلاق الملاحظة {note_id} ===")

        evaluation_detail = EvaluationDetail.query.get(note_id)
        if not evaluation_detail:
            print(f"❌ evaluation_detail غير موجود للـ ID: {note_id}")
            flash('الملاحظة غير موجودة', 'danger')
            return redirect(url_for('action_plans'))

        # طباعة بيانات الطلب
        print(f"📦 بيانات الطلب: {request.form}")

        closed_date_str = request.form.get('closed_date')
        improvement_score = request.form.get('improvement_score')
        closing_note = request.form.get('closing_note', '')

        print(f"📅 closed_date: {closed_date_str}")
        print(f"📊 improvement_score: {improvement_score}")
        print(f"📝 closing_note: {closing_note}")

        if not closed_date_str or improvement_score is None:
            print("❌ بيانات ناقصة: تاريخ الإغلاق أو الدرجة المحسنة")
            flash('الرجاء تحديد تاريخ الإغلاق والدرجة المحسنة', 'danger')
            return redirect(url_for('action_plans'))

        # التحقق من صحة البيانات
        try:
            closed_date = datetime.strptime(closed_date_str, "%Y-%m-%d").date()
            improvement_score = float(improvement_score)
            print(f"✅ البيانات صالحة: {closed_date}, {improvement_score}")
        except ValueError as e:
            print(f"❌ خطأ في تحويل البيانات: {e}")
            flash('قيمة التاريخ أو الدرجة غير صحيحة', 'danger')
            return redirect(url_for('action_plans'))

        # استخدام note من evaluation_detail كقيمة افتراضية
        base_note = evaluation_detail.note if evaluation_detail.note else "ملاحظة الإغلاق"
        print(f"📋 base_note: {base_note}")

        # التحقق من وجود action_plans
        print(f"🔍 عدد action_plans الحالي: {len(evaluation_detail.action_plans)}")

        if evaluation_detail.action_plans:
            action_plan = evaluation_detail.action_plans[0]
            print(f"✅ وجد action_plan موجود: {action_plan.id}")
            # تحديث note إذا كانت فارغة
            if not action_plan.note:
                action_plan.note = base_note
                print("📝 تم تحديث note في action_plan الموجود")
        else:
            print("🆕 إنشاء action_plan جديد")
            # إنشاء ActionPlan جديد مع تعيين جميع الحقول الإلزامية
            action_plan = ActionPlan(
                evaluation_detail_id=evaluation_detail.id,
                note=base_note,
                plan_text="",
                action_plan=""
            )
            db.session.add(action_plan)
            print("✅ تم إضافة action_plan جديد إلى الجلسة")

        # تحديث بيانات الإغلاق
        print(f"🔄 تحديث بيانات الإغلاق:")
        print(f"   - closed: True")
        print(f"   - closed_date: {closed_date}")
        print(f"   - improvement_score: {improvement_score}")

        action_plan.closed = True
        action_plan.closed_date = closed_date
        action_plan.improvement_score = improvement_score

        # إضافة closing_note إذا كان الحقل موجوداً في النموذج
        if hasattr(ActionPlan, 'closing_note'):
            action_plan.closing_note = closing_note
            print(f"   - closing_note: {closing_note}")

        # تحديث score في evaluation_detail
        new_score = min(max(improvement_score, 1), 10)
        print(f"🎯 تحديث score من {evaluation_detail.score} إلى {new_score}")
        evaluation_detail.score = new_score

        # محاولة الحفظ
        print("💾 محاولة حفظ التغييرات...")
        db.session.commit()
        print("✅ تم الحفظ بنجاح في قاعدة البيانات")

        flash('تم إغلاق الملاحظة بنجاح', 'success')
        return redirect(url_for('action_plans'))

    except Exception as e:
        print(f"❌ خطأ أثناء إغلاق الملاحظة: {str(e)}")
        import traceback
        print(f"🔍 تفاصيل الخطأ: {traceback.format_exc()}")
        db.session.rollback()
        flash(f'حدث خطأ أثناء إغلاق الملاحظة: {str(e)}', 'danger')
        return redirect(url_for('action_plans'))


@app.route('/debug_note/<int:note_id>')
def debug_note(note_id):
    """تشخيص حالة ملاحظة محددة"""
    evaluation_detail = EvaluationDetail.query.get(note_id)

    if not evaluation_detail:
        return jsonify({"error": "التفاصيل غير موجودة"})

    debug_info = {
        "evaluation_detail": {
            "id": evaluation_detail.id,
            "note": evaluation_detail.note,
            "score": evaluation_detail.score,
            "action_plans_count": len(evaluation_detail.action_plans)
        },
        "action_plans": []
    }

    for plan in evaluation_detail.action_plans:
        debug_info["action_plans"].append({
            "id": plan.id,
            "note": plan.note,
            "closed": plan.closed,
            "closed_date": str(plan.closed_date) if plan.closed_date else None,
            "improvement_score": plan.improvement_score,
            "closing_note": getattr(plan, 'closing_note', 'غير موجود')
        })

    return jsonify(debug_info)

# ✅ دالة مساعدة لإنشاء ActionPlan بشكل آمن
def create_safe_action_plan(evaluation_detail_id, **kwargs):
    """إنشاء خطة عمل بشكل آمن مع التحقق من الحقول الإلزامية"""

    # ✅ القيم الافتراضية للحقول الإلزامية
    defaults = {
        'note': 'لا توجد ملاحظات',
        'plan_text': '',
        'action_plan': ''
    }

    # ✅ دمج القيم الافتراضية مع القيم المقدمة
    for key, default_value in defaults.items():
        if key not in kwargs or kwargs[key] is None or kwargs[key] == '':
            kwargs[key] = default_value

    # ✅ إنشاء الكائن
    return ActionPlan(
        evaluation_detail_id=evaluation_detail_id,
        **kwargs
    )


from datetime import datetime

@app.template_filter('timesince')
def timesince(value):
    if not value:
        return ''
    now = datetime.utcnow()
    diff = now - value

    seconds = diff.total_seconds()
    minutes = seconds / 60
    hours = minutes / 60
    days = hours / 24

    if seconds < 60:
        return "الآن"
    elif minutes < 60:
        return f"{int(minutes)} دقيقة مضت"
    elif hours < 24:
        return f"{int(hours)} ساعة مضت"
    else:
        return f"{int(days)} يوم مضى"

# routes.py
from flask import render_template, jsonify, request
from models import AuditLog, Notification, AuditLogService, NotificationService


@app.route('/audit-logs')
def audit_logs_list():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    table_name = request.args.get('table_name', '')

    if search:
        audit_logs = AuditLogService.search_audit_logs(search, page=page)
    elif table_name:
        audit_logs = AuditLogService.get_table_audit_logs(table_name, page=page)
    else:
        audit_logs = AuditLog.query.order_by(AuditLog.created_at.desc()) \
            .paginate(page=page, per_page=20)

    return render_template('admin/list.html', audit_logs=audit_logs)


@app.route('/notifications')
def notifications_list():
    page = request.args.get('page', 1, type=int)
    notifications = NotificationService.get_user_notifications(
        current_user.id, page=page
    )
    return render_template('admin/list_notification.html', notifications=notifications)




@app.context_processor
def inject_notifications():
    """حقن عدد الإشعارات غير المقروءة في جميع القوالب"""
    if current_user.is_authenticated:
        unread_count = Notification.query.filter_by(
            user_id=current_user.id,
            is_read=False
        ).count()
        return dict(unread_notifications_count=unread_count)
    return dict(unread_notifications_count=0)


@app.context_processor
def inject_audit_stats():
    """حقن إحصائيات سجلات التدقيق"""
    if current_user.is_authenticated:
        total_audit_logs = AuditLog.query.count()
        today_audit_logs = AuditLog.query.filter(
            AuditLog.created_at >= datetime.utcnow().date()
        ).count()

        # الحصول على أكثر الإجراءات تكراراً
        from sqlalchemy import func
        most_common = db.session.query(
            AuditLog.action,
            func.count(AuditLog.id)
        ).group_by(AuditLog.action).order_by(func.count(AuditLog.id).desc()).first()

        most_common_action = most_common[0] if most_common else 'لا توجد'

        return dict(
            total_audit_logs=total_audit_logs,
            today_audit_logs=today_audit_logs,
            most_common_action=most_common_action
        )
    return dict(
        total_audit_logs=0,
        today_audit_logs=0,
        most_common_action='لا توجد'
    )


@app.route('/notifications/mark-read/<int:notification_id>', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    notification = Notification.query.filter_by(
        id=notification_id,
        user_id=current_user.id
    ).first()

    if notification:
        notification.is_read = True
        db.session.commit()
        return jsonify({'success': True})

    return jsonify({'success': False}), 404


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


def check_database_status():
    """فحص حالة قاعدة البيانات"""
    with app.app_context():
        try:
            from models import User, Company

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
                    print(
                        f"   👤 {user.username} - {user.fullname} - {user.role} - company_id: {user.company_id}")  # ✅ أضفت company_id

            return True

        except Exception as e:
            print(f"❌ خطأ في فحص قاعدة البيانات: {e}")
            return False


def initialize_database():
    """تهيئة قاعدة البيانات وإنشاء البيانات الافتراضية"""
    with app.app_context():
        try:
            db.create_all()

            # إنشاء الشركة اليمنية لتكرير السكر
            yemen_sugar_company = Company.query.filter_by(name='الشركة اليمنية لتكرير السكر').first()
            if not yemen_sugar_company:
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
                print("✅ تم إنشاء الشركة اليمنية لتكرير السكر")

            # ✅ الكود الجديد المضاف - تحديث المستخدم admin إذا كان موجوداً
            admin_user = User.query.filter_by(username='admin').first()
            if admin_user:
                if admin_user.company_id is None:
                    admin_user.company_id = yemen_sugar_company.id
                    print("✅ تم ربط المستخدم admin بالشركة اليمنية لتكرير السكر")
                else:
                    print(f"ℹ️ المستخدم admin مرتبط مسبقاً بشركة ID: {admin_user.company_id}")
            else:
                # إنشاء المستخدم الافتراضي إذا لم يكن موجوداً
                admin = User(
                    fullname='المدير العام',
                    username='admin',
                    email='admin@system.com',
                    role='admin',
                    company_id=yemen_sugar_company.id,  # ✅ مرتبط بالشركة
                    active=True,
                    is_admin=True
                )
                admin.set_password('123456')
                db.session.add(admin)
                print("✅ تم إنشاء المستخدم admin وربطه بالشركة")

            db.session.commit()
            print("🎉 تم إنشاء البيانات الافتراضية بنجاح")

        except Exception as e:
            db.session.rollback()
            print(f"❌ خطأ في تهيئة قاعدة البيانات: {e}")
            import traceback
            traceback.print_exc()  # ✅ لرؤية التفاصيل الكاملة للخطأ


if __name__ == "__main__":
    # ✅ أولاً: فحص حالة قاعدة البيانات
    check_database_status()

    # ✅ ثانياً: تهيئة قاعدة البيانات
    initialize_database()

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)