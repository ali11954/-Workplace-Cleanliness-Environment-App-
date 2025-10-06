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
        """خاصية بديلة مؤكدة لـ is_admin"""
        print(f"🔍 فحص is_administrator للمستخدم {self.username}:")
        print(f"   - is_admin (DB): {self.is_admin}")
        print(f"   - username: {self.username}")
        print(f"   - role: {self.role}")

        # إذا كان is_admin True في قاعدة البيانات
        if self.is_admin:
            print("   ✅ is_admin هو True في قاعدة البيانات")
            return True

        # إذا كان اسم المستخدم 'admin'
        if self.username == 'admin':
            print("   ✅ اسم المستخدم هو 'admin'")
            return True

        # إذا كان الدور 'admin'
        if self.role == 'admin':
            print("   ✅ الدور هو 'admin'")
            return True

        print("   ❌ المستخدم ليس مسؤولاً")
        return False

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

    def __repr__(self):
        return f'<User {self.username} - {self.role}>'

class Location(db.Model):
    __tablename__ = 'location'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('location.id'), nullable=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)

    company = db.relationship('Company', back_populates='locations')
    sites = db.relationship('Site', backref='location', cascade='all, delete-orphan')
    children = db.relationship('Location')


class Site(db.Model):
    __tablename__ = 'site'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

    region_id = db.Column(db.Integer, db.ForeignKey('location.id'), nullable=False)

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


    # العلاقات
    region = db.relationship('Location', foreign_keys=[region_id], backref='evaluations')
    site = db.relationship('Site', backref=db.backref('evaluations', lazy=True))
    place = db.relationship('Place', backref=db.backref('evaluations', lazy=True))
    user = db.relationship('User', backref=db.backref('evaluations', lazy=True))
    criterion = db.relationship('Criterion', backref=db.backref('evaluations', lazy=True))
    details = db.relationship('EvaluationDetail', backref='evaluation', cascade='all, delete-orphan')


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

class EvaluationAuthority(db.Model):
    __tablename__ = 'evaluation_authorities'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)  # 🔑 مفتاح أجنبي
    company = db.relationship('Company', back_populates='evaluation_authorities')

    def __repr__(self):
        return f"<EvaluationAuthority {self.name}>"


from datetime import datetime



class ActionPlan(db.Model):
    __tablename__ = "action_plans"
    id = db.Column(db.Integer, primary_key=True)
    note = db.Column(db.Text)
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
    closing_note = db.Column(db.Text, nullable=True)
