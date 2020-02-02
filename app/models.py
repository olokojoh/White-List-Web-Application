from app import db, admin
from datetime import datetime
from flask_login import UserMixin, AnonymousUserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from hashlib import md5
from app import login
from flask_admin.contrib.sqla import ModelView
from flask_admin import expose, BaseView
from flask import redirect, url_for
from flask_login import current_user, login_required


class AnonymousUser(AnonymousUserMixin):
    # confirmed = False
    root = 0
    @property
    def confirmed(self):
        return False

    def has_root(self):
        if self.root == 1:
            return True
        else:
            return False


login.anonymous_user = AnonymousUser


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    # email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    authority = db.Column(db.Enum('管理员', '操作员','查询员'), default='查询员')    
    last_seen = db.Column(db.DateTime, default=datetime.now)
    detail = db.Column(db.Boolean, default=False)

    def authority_level(self):
        if self.authority == '查询员':
            return 1
        if self.authority == '操作员':
            return 2
        if self.authority == '管理员':
            return 3


    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
            digest, size)

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class operationRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, nullable=False)
    username = db.Column(db.String(64))
    operation = db.Column(db.String(64))
    pp = db.Column(db.String(300))
    time = db.Column(db.DateTime, default=datetime.now)


class Private_placement(db.Model):

    __tablename__ = 'private_placement'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    pp_established_time = db.Column(db.String(200))
    pp_name = db.Column(db.String(200), unique=True)
    pp_management_scale = db.Column(db.Float, default=0)
    pp_futures_scale = db.Column(db.Float, default=0)
    pp_qualification = db.Column(db.String(200))
    pp_cooperation_mod = db.Column(db.String(200))
    pp_partner_bank = db.Column(db.String(200))
    pp_partner_broker = db.Column(db.String(200))
    memo = db.Column(db.String(200))
    note = db.Column(db.String(200))
    RoW_ratio = db.Column(db.Float, default=0)
    reward_within_3yrs = db.Column(db.String(200))

    # 表关系
    inv_scope = db.relationship('Inv_scope', backref='company', lazy='dynamic')
    vs = db.relationship('Visit', backref='company', lazy='dynamic')
    sg = db.relationship('Strategy', backref='company', lazy='dynamic')
    fund = db.relationship('Fund', backref='company', lazy='dynamic')


def __repr__(self):
    return '<Private Placement {}>'.format(self.pp_name)


class Inv_scope(db.Model):
    id = db.Column(db.BIGINT(), primary_key=True, autoincrement=True)
    stock = db.Column(db.String(200), default='')
    futures = db.Column(db.String(200), default='')
    bond = db.Column(db.String(200), default='')
    result = db.Column(db.String(200), default=0)
    pp_id = db.Column(db.Integer, db.ForeignKey('private_placement.id'))


class Visit(db.Model):
    id = db.Column(db.BIGINT(), primary_key=True, autoincrement=True)
    date = db.Column(db.Date)
    address = db.Column(db.String(200))
    visitor = db.Column(db.String(200))
    c_name = db.Column(db.String(200))
    c_position = db.Column(db.String(200))
    c_cellphone = db.Column(db.String(200))
    pp_id = db.Column(db.Integer, db.ForeignKey('private_placement.id'))


class Strategy(db.Model):
    id = db.Column(db.BIGINT(), primary_key=True, autoincrement=True)
    q_Stock_long = db.Column(db.String(200), default='')
    q_Market_neutral = db.Column(db.String(200), default='')
    q_Stock_high_frequency = db.Column(db.String(200), default='')
    nq_Stock_long = db.Column(db.String(200), default='')
    nq_Market_neutral = db.Column(db.String(200), default='')
    nq_Stock_high_frequency = db.Column(db.String(200), default='')
    q_Trend = db.Column(db.String(200), default='')
    q_Arbitrage = db.Column(db.String(200), default='')
    q_High_frequency = db.Column(db.String(200), default='')
    nq_Trend = db.Column(db.String(200), default='')
    nq_Arbitrage = db.Column(db.String(200), default='')
    nq_High_frequency = db.Column(db.String(200), default='')
    bond_s = db.Column(db.String(200), default='')
    mix = db.Column(db.String(200), default='')
    result = db.Column(db.String(200), default=0)
    pp_id = db.Column(db.Integer, db.ForeignKey('private_placement.id'))


class Fund(db.Model):
    id = db.Column(db.BIGINT(), primary_key=True, autoincrement=True)
    fof = db.Column(db.String(200), default='')
    own = db.Column(db.String(200), default='')
    regular = db.Column(db.String(200), default='')
    result = db.Column(db.String(200), default=0)
    pp_id = db.Column(db.Integer, db.ForeignKey('private_placement.id'))


# class Fund_manager(db.Model):
#     id = db.Column(db.BIGINT(), primary_key=True, autoincrement=True)
#     name = db.Column(db.String(200))
#     cv = db.Column(db.String(200))
#     fund_list = db.Column(db.String(200))
#     pp_id = db.Column(db.Integer, db.ForeignKey('private_placement.id'))


class MyModelView(ModelView):
    can_create = True
    page_size = 15
    can_view_details = True
    column_searchable_list = ['username']
    column_filters = ['username', 'authority']
    create_modal = True
    edit_modal = True
    can_export = True
    column_labels = dict(username=u'用户名', authority=u'权限', last_seen=u'上一次登录时间')
    column_exclude_list = ('password_hash')
    form_widget_args = {'last_seen': {'readonly':True }} 
    # inline_models = [Inv_scope, ]

    form_args = {
        'username': {'label': '用户名'},
        'password_hash': {'label': '密码'},
        'root': {'label': '管理员权限'},
        'read': {'label': '查询权限'}
    }

    def user_validator(form, field):
        if form._obj is not None:
            user_id = form._obj.id
            # 调用user表的方法，通过用户名得到用户信息
            user = User.get_user_info(user_id=user_id)
            if user.username == 'reyn':
                if field.data != 'reyn ':
                    raise ValidationError(u'reyn为最高权限用户，不允许修改')

    def is_accessible(self):
        if current_user.is_authenticated and current_user.authority == '管理员':
            return True
        else:
            return False

    def inaccessible_callback(self, name, **kwargs):
        # redirect to login page if user doesn't have access
        return redirect('login')

    def on_model_change(self, form, User, is_created=False):
        # 调用用户模型中定义的set方法
        User.set_password(form.password_hash.data)


class LogoutView(BaseView):
    @expose('/')
    @login_required
    def logout(self):
        return redirect(url_for('logout'))


class ReturnView(BaseView):
    @expose('/')
    @login_required
    def return_(self):
        return redirect(url_for('index'))


class pp(ModelView):
    pass
    # form_ajax_refs = {
    #     'inv_scope': {'fields': ['company'], 'page_size': 10},
    #     'vs': {'fields': ['company'], 'page_size': 10},
    #     'sg': {'fields': ['company'], 'page_size': 10},
    #     'fund': {'fields': ['company'], 'page_size': 10},
    #     'fund_manager': {'fields': ['company'], 'page_size': 10}
    # }


class inv_scope(ModelView):
    pass


class vs(ModelView):
    pass


class sg(ModelView):
    pass


class fund(ModelView):
    pass


class fund_manager(ModelView):
    pass


class operationR(ModelView):
    can_create = False
    can_delete = False
    page_size = 20
    can_export = True
    column_searchable_list = ['username', 'operation', 'pp', 'time']
    column_filters = ['username', 'operation', 'pp', 'time']

    column_labels = dict(user_id=u'uid', username=u'用户名', operation=u'操作', pp=u'私募名称', time=u'操作时间')

    def is_accessible(self):
        if current_user.is_authenticated and current_user.authority == '管理员':
            return True
        else:
            return False

    def inaccessible_callback(self, name, **kwargs):
        # redirect to login page if user doesn't have access
        return redirect('login')


admin.add_view(MyModelView(User, db.session, name='用户'))
admin.add_view(operationR(operationRecord, db.session, name='操作日志'))
# admin.add_view(pp(Private_placement, db.session, name='私募'))
# admin.add_view(inv_scope(Inv_scope, db.session, name='投资范围'))
# admin.add_view(vs(Visit, db.session, name='拜访'))
# admin.add_view(sg(Strategy, db.session, name='投资策略'))
# admin.add_view(fund(Fund, db.session, name='可投资金'))
# admin.add_view(fund_manager(Fund_manager, db.session, name='基金经理'))
admin.add_view(LogoutView(name='注销'))
admin.add_view(ReturnView(name='返回'))


@staticmethod
@login.user_loader
def load_user(id):
    return User.query.get(int(id))
