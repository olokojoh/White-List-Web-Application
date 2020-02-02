from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, BooleanField, DateField, FloatField, TextAreaField, PasswordField, RadioField
from flask_admin.form.widgets import DatePickerWidget
from wtforms import MultipleFileField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length
from app.models import User
from flask_login import current_user, login_user, logout_user, login_required


class LoginForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired(message='请输入用户名')])
    password = PasswordField('密码', validators=[DataRequired(message='请输入密码')])
    remember_me = BooleanField('记住我')
    submit = SubmitField('登录')


class RegistrationForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired()])
    oldpassword = PasswordField('旧密码', validators=[DataRequired()])
    password = PasswordField('新密码', validators=[DataRequired()])
    password2 = PasswordField(
        '请再次输入密码', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('保存')

    # def validate_username(self, username):
    #     user = User.query.filter_by(username=username.data).first()
    #     if user is not None:
    #         raise ValidationError('用户名已存在')

    # def validate_email(self, email):
    #     email = User.query.filter_by(email=email.data).first()
    #     if email is not None:
    #         raise ValidationError('邮箱已存在')

    def validate_oldpassword(self, oldpassword):
        user = User.query.filter_by(username=current_user.username).first()
        print(User.check_password(user, oldpassword.data))
        if not User.check_password(user, oldpassword.data):
            raise ValidationError('密码错误')


class EditProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('密码', validators=[DataRequired()])
    password2 = PasswordField(
        '请再次输入密码', validators=[DataRequired(), EqualTo('password')])    
    submit = SubmitField('Submit')

    def __init__(self, original_username, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=self.username.data).first()
            if user is not None:
                raise ValidationError('用户名已存在')


class PPform(FlaskForm):
    pp_id = StringField('id')
    pp_name = StringField('私募名称:', validators=[DataRequired(message='请输入用户名')])
    # pp_established_time = DateField('成立时间:', validators=[DataRequired()], format='%Y-%m-%d', widget=DatePickerWidget())
    pp_established_time = StringField('成立时间:')
    pp_management_scale = FloatField('管理规模:', validators=[DataRequired()])
    pp_futures_scale = FloatField('期货规模:', validators=[DataRequired()])
    pp_qualification = RadioField('私募资质:')

    RoW_ratio = FloatField('收益回撤比:', validators=[DataRequired()])
    reward_within_3yrs = StringField('近3年所获奖项:')
    
    pp_inv_scope = StringField('投资范围:')
    stock = BooleanField('股票')
    futures = BooleanField('期货')
    bond = BooleanField('债券')
    pp_cooperation_mod = StringField('合作模式:', validators=[DataRequired()])

    allS = BooleanField('全选')
    pp_inv_strategy = StringField('策略:')
    q_Stock_long = BooleanField('量化-股票多头')
    q_Market_neutral = BooleanField('量化-股票中性')
    q_Stock_high_frequency = BooleanField('量化-股票高频')
    q_Trend = BooleanField('量化-期货趋势')
    q_Arbitrage = BooleanField('量化-期货套利')
    q_High_frequency = BooleanField('量化-期货高频')

    nq_Stock_long = BooleanField('人工-股票多头')
    nq_Market_neutral = BooleanField('人工-股票中性')
    nq_Stock_high_frequency = BooleanField('人工-股票高频')
    nq_Trend = BooleanField('人工-期货趋势')
    nq_Arbitrage = BooleanField('人工-期货套利')
    nq_High_frequency = BooleanField('人工-期货高频')

    bond_s = BooleanField('债券策略')
    mix = BooleanField('混合策略')

    fund = StringField('可投资金:')
    fof = BooleanField('fof子资金')
    own = BooleanField('公司自有资金')
    regular = BooleanField('普通资金')

    pp_partner_bank = StringField('引入人:')
    pp_partner_broker = StringField('已合作机构:')
    date = DateField('入白名单时间:', validators=[DataRequired()], format='%Y-%m-%d', widget=DatePickerWidget())
    address = StringField('地址(私募):', validators=[DataRequired()])
    visitor = StringField('我司对接人:', validators=[DataRequired()])
    c_name = StringField('联系人(私募):', validators=[DataRequired()])
    c_position = StringField('职务(私募):', validators=[DataRequired()])
    c_cellphone = StringField('联系方式(私募):', validators=[DataRequired()])
    memoF = MultipleFileField('公司介绍:')
    memo = StringField('文件:')
    note = TextAreaField('公司亮点:')
    submit = SubmitField("保存")


class FilterF(FlaskForm):
    S_AllS = BooleanField('全选')
    S_AllF = BooleanField('全选')
    S_fund = StringField('可投资金')
    S_fof = BooleanField('fof子资金')
    S_own = BooleanField('公司自有资金')
    S_regular = BooleanField('普通资金')

    S_pp_inv_strategy = StringField('投资策略')
    S_pp_stock = StringField('股票')
    S_pp_future = StringField('期货')

    S_q_Stock_long = BooleanField('量化-股票多头')
    S_q_Market_neutral = BooleanField('量化-股票中性')
    S_q_Stock_high_frequency = BooleanField('量化-股票高频')
    S_q_Trend = BooleanField('量化-期货趋势')
    S_q_Arbitrage = BooleanField('量化-期货套利')
    S_q_High_frequency = BooleanField('量化-期货高频')

    S_nq_Stock_long = BooleanField('人工-股票多头')
    S_nq_Market_neutral = BooleanField('人工-股票中性')
    S_nq_Stock_high_frequency = BooleanField('人工-股票高频')
    S_nq_Trend = BooleanField('人工-期货趋势')
    S_nq_Arbitrage = BooleanField('人工-期货套利')
    S_nq_High_frequency = BooleanField('人工-期货高频')

    S_bond_s = BooleanField('债券策略')
    S_mix = BooleanField('混合类策略')
    Search = SubmitField('筛选')


class SearchForm(FlaskForm):
    search_PP = StringField('私幕')
    search_management_scale = StringField('管理规模')
    search_Referrer = StringField('引入人')
    search_strategy = StringField('策略')
    search_fund = StringField('可投资金')
    search = SubmitField('搜索')


class csvForm(FlaskForm):
    csv = MultipleFileField('upload csv files')
    upload = SubmitField('submit')

