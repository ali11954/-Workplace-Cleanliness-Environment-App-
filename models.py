from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import Enum
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


# جدول الشركات
class Company(db.Model):
    __tablename__ = 'companies'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False, unique=True)

    code = db.Column(db.String(50), unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    active = db.Column(db.Boolean, default=True)

    # العلاقات
    users = db.relationship('User', back_populates='company')
    locations = db.relationship('Location', back_populates='company')
    evaluation_authorities = db.relationship('EvaluationAuthority', back_populates='company')

    def __repr__(self):
        return f'<Company {self.name}>'



user_regions = db.Table('user_regions',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('region_id', db.Integer, db.ForeignKey('location.id'), primary_key=True)
)


# models.py - تحديث النماذج مع الهيكل الحالي

# جدول الصلاحيات
class Permission(db.Model):
    __tablename__ = 'permissions'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=db.func.now())


# جدول صلاحيات المستخدمين
class UserPermission(db.Model):
    __tablename__ = 'user_permissions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    permission_code = db.Column(db.String(50), nullable=False)
    granted_at = db.Column(db.DateTime, default=db.func.now())

    user = db.relationship('User', back_populates='user_permissions')


# تحديث نموذج User الحالي
class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(150))
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    role = db.Column(db.String(50))  # admin, supervisor, sub_admin, user
    active = db.Column(db.Boolean, default=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'))
    region_id = db.Column(db.Integer, db.ForeignKey('location.id'))

    company = db.relationship('Company', back_populates='users')
    regions = db.relationship('Location', secondary=user_regions, backref='users')

    # ✅ ✅ ✅ أضف العلاقات المقابلة
    owned_evaluations = db.relationship(
        'Evaluation',
        foreign_keys='Evaluation.user_id',
        back_populates='user',
        lazy=True
    )

    # إضافة العلاقة مع الصلاحيات المخصصة
    user_permissions = db.relationship('UserPermission', back_populates='user', lazy=True, cascade='all, delete-orphan')

    def set_password(self, pw):
        self.password_hash = generate_password_hash(pw)

    def check_password(self, pw):
        return check_password_hash(self.password_hash, pw)

    @property
    def is_active(self):
        return self.active

    @property
    def is_administrator(self):
        """خاصية متوافقة مع Flask-Login - الإصدار النهائي"""
        # استخدام الحقل المباشر أولاً
        if hasattr(self, '_is_admin') and self._is_admin is not None:
            return bool(self._is_admin)

        # ثم الشروط الأخرى
        return self.role == 'admin' or self.username == 'admin'

    # جعل is_admin كمسمى بديل لنفس الخاصية
    @property
    def is_admin(self):
        return self.is_administrator

    @is_admin.setter
    def is_admin(self, value):
        """تعيين قيمة is_admin"""
        self._is_admin = bool(value)

    # ========== دوال الصلاحيات الجديدة والمحدثة ==========

    @property
    def all_permissions(self):
        """الحصول على جميع صلاحيات المستخدم"""
        permissions = set()

        # صلاحيات الدور الأساسية
        role_permissions = self.get_role_permissions()
        permissions.update(role_permissions)

        # الصلاحيات المخصصة
        user_perms = [up.permission_code for up in self.user_permissions]
        permissions.update(user_perms)

        return list(permissions)

    def get_role_permissions(self):
        """الحصول على الصلاحيات الافتراضية للدور"""
        role_permissions_map = {
            'admin': [
                'users_view', 'users_add', 'users_edit', 'users_delete',
                'evaluations_view', 'evaluations_add', 'evaluations_edit', 'evaluations_delete',
                'reports_view', 'reports_export', 'settings_view', 'settings_edit',
                'manage_permissions', 'companies_manage',
                'authorities_view', 'authorities_manage',
                'locations_view', 'locations_manage',
                'criteria_view', 'criteria_manage',
                'dashboard_admin'
            ],
            'supervisor': [
                'users_view', 'users_add', 'users_edit',
                'evaluations_view', 'evaluations_add', 'evaluations_edit',
                'reports_view', 'reports_export',
                'authorities_view',
                'locations_view',
                'criteria_view',
                'dashboard_manager'
            ],
            'sub_admin': [
                'users_view',
                'evaluations_view', 'evaluations_add',
                'reports_view',
                'authorities_view',
                'locations_view',
                'criteria_view',
                'dashboard_sub_admin'
            ],
            'user': [
                'evaluations_view',
                'reports_view',
                'dashboard_user'
            ]
        }

        return role_permissions_map.get(self.role, [])

    def has_permission(self, permission_code):
        """التحقق من وجود صلاحية معينة"""
        if self.is_admin or self.role == 'admin':
            return True  # للمسؤولين صلاحيات كاملة

        return permission_code in self.all_permissions

    def can_access_company(self, company_id):
        """التحقق من إمكانية الوصول لشركة معينة"""
        if self.is_admin or self.role == 'admin':
            return True
        if self.role in ['supervisor', 'sub_admin'] and self.company_id:
            return self.company_id == company_id
        return False

    def can_manage_user(self, target_user):
        """التحقق من إمكانية إدارة مستخدم آخر"""
        if self.is_admin or self.role == 'admin':
            return True
        if self.role in ['supervisor', 'sub_admin'] and self.company_id:
            return target_user.company_id == self.company_id
        return False

    # ========== دوال جديدة للداشبورد ==========

    @property
    def dashboard_features(self):
        """الحصول على البطاقات المتاحة في الداشبورد حسب الدور"""
        features_map = {
            'admin': [
                {'url': 'users', 'icon': 'fa-users-cog', 'text': 'إدارة المستخدمين', 'bg': 'bg-users',
                 'permission': 'users_view'},
                {'url': 'companies', 'icon': 'fa-building', 'text': 'إدارة الشركات', 'bg': 'bg-companies',
                 'permission': 'companies_manage'},
                {'url': 'evaluations', 'icon': 'fa-clipboard-check', 'text': 'التقييمات', 'bg': 'bg-evaluations',
                 'permission': 'evaluations_view'},
                {'url': 'authorities', 'icon': 'fa-users', 'text': 'الجهات المسؤولة', 'bg': 'bg-authorities',
                 'permission': 'authorities_view'},
                {'url': 'locations', 'icon': 'fa-map-marker-alt', 'text': 'المناطق', 'bg': 'bg-locations',
                 'permission': 'locations_view'},
                {'url': 'criteria', 'icon': 'fa-list-check', 'text': 'معايير التقييم', 'bg': 'bg-criteria',
                 'permission': 'criteria_view'},
                {'url': 'report_summary', 'icon': 'fa-broom', 'text': 'تقرير المناطق', 'bg': 'bg-report-evaluation',
                 'permission': 'reports_view'},
                {'url': 'reports', 'icon': 'fa-file-alt', 'text': 'تقرير المستخدمين', 'bg': 'bg-report-general',
                 'permission': 'reports_view'},
                {'url': 'responsibility_report', 'icon': 'fa-balance-scale', 'text': 'تقرير الجهات',
                 'bg': 'bg-report-responsibility', 'permission': 'reports_view'},
                {'url': 'system_settings', 'icon': 'fa-cogs', 'text': 'إعدادات النظام', 'bg': 'bg-settings',
                 'permission': 'settings_view'}
            ],
            'supervisor': [
                {'url': 'users', 'icon': 'fa-users', 'text': 'إدارة المستخدمين', 'bg': 'bg-users',
                 'permission': 'users_view'},
                {'url': 'evaluations', 'icon': 'fa-clipboard-check', 'text': 'التقييمات', 'bg': 'bg-evaluations',
                 'permission': 'evaluations_view'},
                {'url': 'authorities', 'icon': 'fa-users', 'text': 'الجهات المسؤولة', 'bg': 'bg-authorities',
                 'permission': 'authorities_view'},
                {'url': 'locations', 'icon': 'fa-map-marker-alt', 'text': 'المناطق', 'bg': 'bg-locations',
                 'permission': 'locations_view'},
                {'url': 'criteria', 'icon': 'fa-list-check', 'text': 'معايير التقييم', 'bg': 'bg-criteria',
                 'permission': 'criteria_view'},
                {'url': 'report_summary', 'icon': 'fa-broom', 'text': 'تقرير المناطق', 'bg': 'bg-report-evaluation',
                 'permission': 'reports_view'},
                {'url': 'reports', 'icon': 'fa-file-alt', 'text': 'تقرير المستخدمين', 'bg': 'bg-report-general',
                 'permission': 'reports_view'},
                {'url': 'responsibility_report', 'icon': 'fa-balance-scale', 'text': 'تقرير الجهات',
                 'bg': 'bg-report-responsibility', 'permission': 'reports_view'},
                {'url': 'action_plans', 'icon': 'fa-tasks', 'text': 'خطط العمل', 'bg': 'bg-action-plans',
                 'permission': 'evaluations_edit'}
            ],
            'sub_admin': [
                {'url': 'evaluations', 'icon': 'fa-clipboard-check', 'text': 'التقييمات', 'bg': 'bg-evaluations',
                 'permission': 'evaluations_view'},
                {'url': 'locations', 'icon': 'fa-map-marker-alt', 'text': 'المناطق', 'bg': 'bg-locations',
                 'permission': 'locations_view'},
                {'url': 'report_summary', 'icon': 'fa-broom', 'text': 'تقرير المناطق', 'bg': 'bg-report-evaluation',
                 'permission': 'reports_view'},
                {'url': 'responsibility_report', 'icon': 'fa-balance-scale', 'text': 'تقرير الجهات',
                 'bg': 'bg-report-responsibility', 'permission': 'reports_view'},
                {'url': 'action_plans', 'icon': 'fa-tasks', 'text': 'خطط العمل', 'bg': 'bg-action-plans',
                 'permission': 'evaluations_edit'},
                {'url': 'daily_tasks', 'icon': 'fa-list-check', 'text': 'المهام اليومية', 'bg': 'bg-tasks',
                 'permission': 'evaluations_view'},
                {'url': 'reports_list', 'icon': 'fa-flag', 'text': 'البلاغات', 'bg': 'bg-reports',
                 'permission': 'reports_view'}
            ],
            'user': [
                {'url': 'evaluations', 'icon': 'fa-clipboard-check', 'text': 'التقييمات', 'bg': 'user-bg-evaluations',
                 'permission': 'evaluations_view'},
                {'url': 'report_summary', 'icon': 'fa-broom', 'text': 'تقرير المناطق',
                 'bg': 'user-bg-report-evaluation', 'permission': 'reports_view'},
                {'url': 'responsibility_report', 'icon': 'fa-balance-scale', 'text': 'تقرير الجهات',
                 'bg': 'user-bg-report-responsibility', 'permission': 'reports_view'}
            ]
        }

        # الحصول على البطاقات حسب الدور مع التحقق من الصلاحيات
        base_features = features_map.get(self.role, features_map['user'])

        # تصفية البطاقات بناءً على الصلاحيات الفعلية
        available_features = []
        for feature in base_features:
            if self.has_permission(feature.get('permission', '')):
                available_features.append(feature)

        return available_features

    @property
    def dashboard_title(self):
        """عنوان الداشبورد حسب الدور"""
        titles = {
            'admin': 'لوحة تحكم المسؤول العام',
            'supervisor': 'لوحة تحكم مدير الشؤون',
            'sub_admin': 'لوحة تحكم المشرف الفرعي',
            'user': 'لوحة تحكم المستخدم'
        }
        return titles.get(self.role, 'لوحة التحكم')

    @property
    def dashboard_description(self):
        """وصف الداشبورد حسب الدور"""
        descriptions = {
            'admin': 'إدارة كاملة للنظام وجميع الإعدادات',
            'supervisor': 'إدارة العمليات والتقييمات اليومية',
            'sub_admin': 'المهام والصلاحيات المحددة',
            'user': 'الواجهة الأساسية للمستخدم'
        }
        return descriptions.get(self.role, 'الواجهة الرئيسية')

    @property
    def role_badge_style(self):
        """نمط شارة الدور"""
        styles = {
            'admin': {'background': 'linear-gradient(45deg, #198754, #20c997)', 'icon': 'fa-crown'},
            'supervisor': {'background': 'linear-gradient(45deg, #007bff, #0056b3)', 'icon': 'fa-user-tie'},
            'sub_admin': {'background': 'linear-gradient(45deg, #fd7e14, #e44d26)', 'icon': 'fa-user-shield'},
            'user': {'background': 'linear-gradient(45deg, #6c757d, #495057)', 'icon': 'fa-user'}
        }
        return styles.get(self.role, styles['user'])

    def get_accessible_companies(self):
        """الحصول على الشركات التي يمكن للمستخدم الوصول إليها"""
        from models import Company  # تجنب الاستيراد الدائري

        if self.is_admin or self.role == 'admin':
            return Company.query.filter_by(active=True).all()
        elif self.company_id:
            return Company.query.filter_by(id=self.company_id, active=True).all()
        else:
            return []

    def get_dashboard_url(self):
        """الحصول على رابط الداشبورد المناسب"""
        if self.role == 'admin':
            return 'admin_dashboard'
        elif self.role == 'supervisor':
            return 'manager_dashboard'
        elif self.role == 'sub_admin':
            return 'sub_admin_dashboard'
        else:
            return 'user_dashboard'


    def get_accessible_locations(self):
        """الحصول على المناطق التي يمكن للمستخدم الوصول إليها"""
        if self.is_admin or self.role == 'admin':
            return Location.query.filter_by(is_active=True).all()
        elif self.regions:
            return self.regions
        elif self.company_id:
            return Location.query.filter_by(company_id=self.company_id, is_active=True).all()
        return []

    def can_access_location(self, location_id):
        """التحقق من إمكانية الوصول لمنطقة معينة"""
        if self.is_admin or self.role == 'admin':
            return True

        accessible_locations = self.get_accessible_locations()
        return any(loc.id == location_id for loc in accessible_locations)


    def get_regions_safe(self):
        """الحصول على المناطق بشكل آمن يتجنب DetachedInstanceError"""
        try:
                # إذا كان الكائن مرتبطاً بالجلسة
            if self in db.session:
                return self.regions
            else:
                    # استعلام منفصل إذا كان الكائن منفصلاً
                return db.session.query(Location).join(
                    user_regions, Location.id == user_regions.c.region_id
                ).filter(user_regions.c.user_id == self.id).all()
        except Exception as e:
            print(f"❌ خطأ في get_regions_safe: {e}")
            return []

    def __repr__(self):
        return f'<User {self.username} - {self.role}>'

# تحسين العلاقات في نموذج Location
class Location(db.Model):
    __tablename__ = 'location'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('location.id'), nullable=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)

    # تحسين العلاقات
    company = db.relationship('Company', back_populates='locations')
    parent = db.relationship('Location', remote_side=[id], backref='sub_locations')
    sites = db.relationship('Site', back_populates='location', cascade='all, delete-orphan')

    # إضافة حقول مفيدة
    code = db.Column(db.String(50), unique=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Site(db.Model):
    __tablename__ = 'site'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

    region_id = db.Column(db.Integer, db.ForeignKey('location.id'), nullable=False)
    location = db.relationship('Location', back_populates='sites')

    # علاقة مع الأماكن (Places)
    places = db.relationship('Place', backref='site', cascade='all, delete-orphan')


class Place(db.Model):
    __tablename__ = 'place'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

    site_id = db.Column(db.Integer, db.ForeignKey('site.id'), nullable=False)
    criteria = db.relationship('Criterion', back_populates='place', cascade='all, delete-orphan')

    # علاقة مع المعايير (Criteria)


class Criterion(db.Model):
    __tablename__ = 'criterion'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    min_score = db.Column(db.Float, nullable=False)
    max_score = db.Column(db.Float, nullable=False)
    place_id = db.Column(db.Integer, db.ForeignKey('place.id'), nullable=False)
    authority_id = db.Column(db.Integer, db.ForeignKey('evaluation_authorities.id'))  # ✅ هذا جديد

    place = db.relationship('Place', back_populates='criteria')

    authority = db.relationship('EvaluationAuthority', backref='criteria')



class Evaluation(db.Model):
    __tablename__ = 'evaluation'
    id = db.Column(db.Integer, primary_key=True)
    region_id = db.Column(db.Integer, db.ForeignKey('location.id'))
    site_id = db.Column(db.Integer, db.ForeignKey('site.id'))
    place_id = db.Column(db.Integer, db.ForeignKey('place.id'))
    criterion_id = db.Column(db.Integer, db.ForeignKey('criterion.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    total_score = db.Column(db.Integer)
    percent = db.Column(db.Float)
    notes = db.Column(db.Text)
    date = db.Column(db.DateTime, default=datetime.utcnow)

    # إضافة حالة التقييم
    status = db.Column(Enum('draft', 'submitted', 'approved', 'rejected',
                            name='evaluation_status'), default='draft')

    # إضافة حقول للتحقق
    submitted_at = db.Column(db.DateTime)
    approved_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    approved_at = db.Column(db.DateTime)

    # ✅ تأكد من إضافة هذه الحقول إذا كانت موجودة في DB
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    updated_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    # ✅ ✅ ✅ العلاقات مع backref فريدة
    approved_user = db.relationship('User', foreign_keys=[approved_by], backref='approved_evaluations')

    user = db.relationship('User', foreign_keys=[user_id], back_populates='owned_evaluations')


    created_by = db.relationship('User', foreign_keys=[created_by_id], backref='created_evaluations')
    updated_by = db.relationship('User', foreign_keys=[updated_by_id], backref='updated_evaluations')

    region = db.relationship('Location', foreign_keys=[region_id], backref='evaluations')
    site = db.relationship('Site', foreign_keys=[site_id], backref='evaluations')
    place = db.relationship('Place', foreign_keys=[place_id], backref='evaluations')
    criterion = db.relationship('Criterion', foreign_keys=[criterion_id], backref='evaluations')
    details = db.relationship('EvaluationDetail', backref='evaluation', cascade='all, delete-orphan')

    __table_args__ = (
        db.Index('idx_evaluation_user_date', 'user_id', 'date'),
        db.Index('idx_evaluation_region_date', 'region_id', 'date'),
        db.Index('idx_evaluation_status', 'status'),
    )

    @property
    def is_editable(self):
        return self.status in ['draft', 'rejected']

    # ... باقي الكود
class EvaluationDetail(db.Model):
    __tablename__ = "evaluation_detail"   # ← لازم يتطابق مع foreign key
    id = db.Column(db.Integer, primary_key=True)
    evaluation_id = db.Column(db.Integer, db.ForeignKey('evaluation.id'), nullable=False)
    criterion_id = db.Column(db.Integer, db.ForeignKey('criterion.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    score = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    # إضافة جهة المسؤولية
    authority_id = db.Column(db.Integer, db.ForeignKey('evaluation_authorities.id'), nullable=True)
    place_id = db.Column(db.Integer, db.ForeignKey('place.id'), nullable=True)
    place = db.relationship('Place', backref='evaluation_details')
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    company = db.relationship('Company', backref='evaluation_details')

    # العلاقات
    note = db.Column(db.Text, nullable=True)

    criterion = db.relationship('Criterion', backref=db.backref('evaluation_details', cascade='all, delete-orphan'))
    user = db.relationship('User')
    authority = db.relationship('EvaluationAuthority', backref='evaluation_details')

    __table_args__ = (
        db.Index('idx_eval_detail_evaluation', 'evaluation_id'),
        db.Index('idx_eval_detail_criterion', 'criterion_id'),
        db.Index('idx_eval_detail_authority', 'authority_id'),
    )
class EvaluationAuthority(db.Model):
    __tablename__ = 'evaluation_authorities'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)  # 🔑 مفتاح أجنبي
    company = db.relationship('Company', back_populates='evaluation_authorities')

    @classmethod
    def get_authorities_by_company(cls, company_id):
        """الحصول على جهات التقييم لشركة معينة"""
        return cls.query.filter_by(company_id=company_id).all()

    def get_related_criteria(self):
        """الحصول على المعايير المرتبطة بجهة التقييم"""
        return Criterion.query.filter_by(authority_id=self.id).all()

    def __repr__(self):
        return f"<EvaluationAuthority {self.name}>"


from datetime import datetime



class ActionPlan(db.Model):
    __tablename__ = "action_plan"
    id = db.Column(db.Integer, primary_key=True)
    note = db.Column(db.Text, nullable=False)  # ✅ غير إلى nullable=False
    plan_text = db.Column(db.Text)
    action_plan = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    closed = db.Column(db.Boolean, default=False)
    closed_date = db.Column(db.DateTime, nullable=True)
    improvement_score = db.Column(db.Float, nullable=True)

    evaluation_detail_id = db.Column(db.Integer, db.ForeignKey("evaluation_detail.id"))
    location_id = db.Column(db.Integer, db.ForeignKey("location.id"), nullable=True)
    site_id = db.Column(db.Integer, db.ForeignKey("site.id"), nullable=True)
    place_id = db.Column(db.Integer, db.ForeignKey("place.id"), nullable=True)
    criterion_id = db.Column(db.Integer, db.ForeignKey("criterion.id"), nullable=True)

    # ✅ العلاقات
    evaluation_detail = db.relationship("EvaluationDetail", backref="action_plans")
    location = db.relationship("Location", backref="action_plans")
    site = db.relationship("Site", backref="action_plans")
    place = db.relationship("Place", backref="action_plans")
    criterion = db.relationship("Criterion", backref="action_plans")

    def __init__(self, **kwargs):
        # ✅ هذا يحل المشكلة - تعيين قيم افتراضية للحقول الإلزامية
        kwargs.setdefault('note', 'لا توجد ملاحظات')
        kwargs.setdefault('plan_text', '')
        kwargs.setdefault('action_plan', '')
        super().__init__(**kwargs)

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    action = db.Column(db.String(100), nullable=False)
    table_name = db.Column(db.String(100), nullable=False)
    record_id = db.Column(db.Integer, nullable=False)
    old_values = db.Column(db.Text)
    new_values = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='audit_logs')


class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    notification_type = db.Column(db.String(50))  # info, warning, success, danger
    related_url = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='notifications')




from flask import request
import json
from datetime import datetime


class AuditLogService:

    @staticmethod
    def create_audit_log(user_id, action, table_name, record_id, old_values=None, new_values=None):
        """إنشاء سجل تدقيق جديد"""
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            table_name=table_name,
            record_id=record_id,
            old_values=json.dumps(old_values) if old_values else None,
            new_values=json.dumps(new_values) if new_values else None,
            ip_address=request.remote_addr if request else None,
            user_agent=request.headers.get('User-Agent') if request else None
        )
        db.session.add(audit_log)
        db.session.commit()
        return audit_log

    @staticmethod
    def get_user_audit_logs(user_id, page=1, per_page=20):
        """الحصول على سجلات التدقيق للمستخدم"""
        return AuditLog.query.filter_by(user_id=user_id) \
            .order_by(AuditLog.created_at.desc()) \
            .paginate(page=page, per_page=per_page, error_out=False)

    @staticmethod
    def get_table_audit_logs(table_name, record_id=None, page=1, per_page=20):
        """الحصول على سجلات التدقيق لجدول معين"""
        query = AuditLog.query.filter_by(table_name=table_name)
        if record_id:
            query = query.filter_by(record_id=record_id)

        return query.order_by(AuditLog.created_at.desc()) \
            .paginate(page=page, per_page=per_page, error_out=False)

    @staticmethod
    def search_audit_logs(search_term, page=1, per_page=20):
        """بحث في سجلات التدقيق"""
        return AuditLog.query.filter(
            db.or_(
                AuditLog.action.ilike(f'%{search_term}%'),
                AuditLog.table_name.ilike(f'%{search_term}%'),
                AuditLog.old_values.ilike(f'%{search_term}%'),
                AuditLog.new_values.ilike(f'%{search_term}%')
            )
        ).order_by(AuditLog.created_at.desc()) \
            .paginate(page=page, per_page=per_page, error_out=False)


class NotificationService:

    @staticmethod
    def create_notification(user_id, title, message, notification_type='info', related_url=None):
        """إنشاء إشعار جديد"""
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type,
            related_url=related_url
        )
        db.session.add(notification)
        db.session.commit()
        return notification

    @staticmethod
    def get_user_notifications(user_id, unread_only=False, page=1, per_page=10):
        """الحصول على إشعارات المستخدم"""
        query = Notification.query.filter_by(user_id=user_id)

        if unread_only:
            query = query.filter_by(is_read=False)

        return query.order_by(Notification.created_at.desc()) \
            .paginate(page=page, per_page=per_page, error_out=False)

    @staticmethod
    def mark_as_read(notification_id, user_id):
        """تحديد الإشعار كمقروء"""
        notification = Notification.query.filter_by(id=notification_id, user_id=user_id).first()
        if notification:
            notification.is_read = True
            db.session.commit()
        return notification

    @staticmethod
    def mark_all_as_read(user_id):
        """تحديد جميع إشعارات المستخدم كمقروءة"""
        Notification.query.filter_by(user_id=user_id, is_read=False).update(
            {'is_read': True}
        )
        db.session.commit()

    @staticmethod
    def get_unread_count(user_id):
        """الحصول على عدد الإشعارات غير المقروءة"""
        return Notification.query.filter_by(user_id=user_id, is_read=False).count()

    @staticmethod
    def delete_notification(notification_id, user_id):
        """حذف إشعار"""
        notification = Notification.query.filter_by(id=notification_id, user_id=user_id).first()
        if notification:
            db.session.delete(notification)
            db.session.commit()
        return notification

