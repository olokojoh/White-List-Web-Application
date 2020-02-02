from app import app, db, admin
from flask import render_template, request, redirect, url_for, flash, send_from_directory, jsonify
from app.models import Private_placement, Strategy, Visit, Fund, Inv_scope, User, operationRecord
from app.forms import PPform, FilterF, SearchForm, LoginForm, RegistrationForm, EditProfileForm, csvForm
from sqlalchemy import and_, or_
from flask_paginate import get_page_parameter
from config import Config
import os
from werkzeug.urls import url_parse
from flask_login import current_user, login_user, logout_user, login_required
from datetime import datetime
from flask_admin.contrib.sqla import ModelView
from flask_admin import expose, BaseView
from werkzeug.security import generate_password_hash
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.types import NVARCHAR, Float, Integer, Date
from pyecharts.charts import Line
from eplot import eplot
from flask import Flask
from jinja2 import Markup, Environment, FileSystemLoader
from pyecharts import options as opts
from pyecharts.charts import Bar


@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Private_placement': Private_placement, 'Strategy': Strategy, 'Visit': Visit, 'Fund': Fund, 'Inv_scope': Inv_scope, 'operationRecord': operationRecord}


@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('用户名或密码错误')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        print(form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)


@app.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        print('-------------------------------')
        User.query.filter_by(id=current_user.id).update({'username': form.username.data})
        User.query.filter_by(id=current_user.id).update({'password_hash': generate_password_hash(form.password.data)})
        db.session.commit()
        flash('修改成功')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template('user.html', user=user)


@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.now()
        db.session.commit()


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    Sform = SearchForm()
    Fform = FilterF()
    form = PPform()
    current_user.detail = False
    form.pp_qualification.choices = [('1', '仅备案'), ('2', '仅会员'), ('3', '投顾资质')]

    per_page = Config.data_per_page
    page = request.args.get(get_page_parameter(), type=int, default=1)
    pagination = db.session.query(Private_placement, Inv_scope, Strategy, Fund, Visit)\
        .filter(and_(
            Private_placement.id == Inv_scope.pp_id,
            Private_placement.id == Strategy.pp_id,
            Private_placement.id == Fund.pp_id,
            Private_placement.id == Visit.pp_id)).paginate(page=page, per_page=per_page, error_out=False)
    pp = pagination.items
    num = len(pp)

    # for i in pp:
    #     fw = ''
    #     cl = ''
    #     zj = ''

    #     if i[1].stock == '股票':
    #         fw = fw + i[1].stock + ' '
    #     if i[1].futures == '期货':
    #         fw = fw + i[1].futures + ' '
    #     if i[1].bond == '债券':
    #         fw = fw + i[1].bond
    #     i[1].result = fw

    #     if i[2].q_Stock_long == '量化-股票多头' or i[2].q_Market_neutral == '量化-股票中性' or i[2].q_Stock_high_frequency == '量化-股票高频' or i[2].nq_Stock_long == '人工-股票多头' or i[2].nq_Market_neutral == '人工-股票中性' or i[2].nq_Stock_high_frequency == '人工-股票高频':
    #         cl = cl + '股票策略 '
    #     if i[2].q_Trend == '量化-期货趋势' or i[2].q_Arbitrage == '量化-期货套利' or i[2].q_High_frequency == '量化-期货高频' or i[2].nq_Trend == '人工-期货趋势' or i[2].nq_Arbitrage == '人工-期货套利' or i[2].nq_High_frequency == '人工-期货高频':
    #         cl = cl + '管理期货 '
    #     if i[2].bond_s == '债券策略':
    #         cl = cl + '债券策略 '
    #     if i[2].mix == '混合策略':
    #         cl = cl + '混合策略'
    #     i[2].result = cl

    #     if i[3].fof == 'fof子基金':
    #         zj = zj + 'fof子基金      '
    #     if i[3].own == '公司自有资金':
    #         zj = zj + '公司自有资金   '
    #     if i[3].regular == '普通资金':
    #         zj = zj + '普通资金'
    #     i[3].result = zj

    context = {
        'pagination': pagination,
        'u': pp,
        'num': num
    }

    return render_template('index.html', **context, form=form, Fform=Fform, Sform=Sform)


@app.route('/detail/<ppid>', methods=['GET', 'POST'])
@login_required
def detail(ppid):
    form = PPform()
    csvform = csvForm()
    current_user.detail = True
    i = db.session.query(Private_placement, Inv_scope, Strategy, Fund, Visit)\
        .filter(and_(
            Private_placement.id == ppid,
            Private_placement.id == Inv_scope.pp_id,
            Private_placement.id == Strategy.pp_id,
            Private_placement.id == Fund.pp_id,
            Private_placement.id == Visit.pp_id)).first()
            
    fw = ''
    cl = ''
    zj = ''

    if i[1].stock == '股票':
        fw = fw + '股票\r\n'
    if i[1].futures == '期货':
        fw = fw + '期货\r\n'
    if i[1].bond == '债券':  
        fw = fw + '债券'
    i[1].result = fw

    if i[2].q_Stock_long == '量化-股票多头' or i[2].q_Market_neutral == '量化-股票中性' or i[2].q_Stock_high_frequency == '量化-股票高频' or i[2].nq_Stock_long == '人工-股票多头' or i[2].nq_Market_neutral == '人工-股票中性' or i[2].nq_Stock_high_frequency == '人工-股票高频':
        cl = cl + '股票策略\r\n'
    if i[2].q_Trend == '量化-期货趋势' or i[2].q_Arbitrage == '量化-期货套利' or i[2].q_High_frequency == '量化-期货高频' or i[2].nq_Trend == '人工-期货趋势' or i[2].nq_Arbitrage == '人工-期货套利' or i[2].nq_High_frequency == '人工-期货高频':
        cl = cl + '管理期货\r\n'
    if i[2].bond_s == '债券策略':
        cl = cl + '债券策略\r\n'
    if i[2].mix == '混合策略':
        cl = cl + '混合策略'
    i[2].result = cl

    if i[3].fof == 'fof子基金':
        zj = zj + 'fof子基金 '
    if i[3].own == '公司自有资金':
        zj = zj + '公司自有资金 '
    if i[3].regular == '普通资金':
        zj = zj + '普通资金'
    i[3].result = zj

    return render_template('detail.html', i=i, form=form, csvform=csvform)


@app.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    # 从前端获取新数据
    Sform = SearchForm()
    Fform = FilterF()
    form = PPform()
    form.pp_qualification.choices = [('1', '仅备案'), ('2', '仅会员'), ('3', '投顾资质')]
    
    if form.validate_on_submit():
        pp_name = request.form.get('pp_name')
        searchpp = Private_placement.query.filter(Private_placement.pp_name == 'pp_name').all()
        if searchpp != []:
            flash('私募已存在')
            return render_template('index.html', form=form, Fform=Fform, Sform=Sform)
        management_scale = float(request.form.get('pp_management_scale')) * 100000000
        futures_scale = float(request.form.get('pp_futures_scale')) * 100000000
        qualification = request.form.get('pp_qualification')

        if qualification == 1:
            qualification = '仅备案'
        elif qualification == 2:
            qualification = '仅会员'
        else:
            qualification = '投顾资质'
        stock_check = request.form.get('stock')
        futures_check = request.form.get('futures')
        bond_check = request.form.get('bond')
        pp_established_time = request.form.get('pp_established_time')
        RoW_ratio = request.form.get('RoW_ratio')
        reward_within_3yrs = request.form.get('reward_within_3yrs')

        if stock_check == 'y':
            stock = '股票'
        else:
            stock = ''

        if futures_check == 'y':
            futures = '期货'
        else:
            futures = ''

        if bond_check == 'y':
            bond = '债券'
        else:
            bond = ''

        coop_mod = request.form.get('pp_cooperation_mod')

        q_Stock_long_check = request.form.get('q_Stock_long')
        q_Market_neutral_check = request.form.get('q_Market_neutral')
        q_Stock_high_frequency_check = request.form.get('q_Stock_high_frequency')
        nq_Stock_long_check = request.form.get('nq_Stock_long')
        nq_Market_neutral_check = request.form.get('nq_Market_neutral')
        nq_Stock_high_frequency_check = request.form.get('nq_Stock_high_frequency')
        q_Trend_check = request.form.get('q_Trend')
        q_Arbitrage_check = request.form.get('q_Arbitrage')
        q_High_frequency_check = request.form.get('q_High_frequency')
        nq_Trend_check = request.form.get('nq_Trend')
        nq_Arbitrage_check = request.form.get('nq_Arbitrage')
        nq_High_frequency_check = request.form.get('nq_High_frequency')
        bond_s_check = request.form.get('bond_s')
        mix_check = request.form.get('mix')

        if q_Stock_long_check == 'y':
            q_Stock_long = '量化-股票多头'
        else:
            q_Stock_long = ''

        if q_Market_neutral_check == 'y':
            q_Market_neutral = '量化-股票中性'
        else:
            q_Market_neutral = ''

        if q_Stock_high_frequency_check == 'y':
            q_Stock_high_frequency = '量化-股票高频'
        else:
            q_Stock_high_frequency = ''

        if nq_Stock_long_check == 'y':
            nq_Stock_long = '人工-股票多头'
        else:
            nq_Stock_long = ''

        if nq_Market_neutral_check == 'y':
            nq_Market_neutral = '人工-股票中性'
        else:
            nq_Market_neutral = ''

        if nq_Stock_high_frequency_check == 'y':
            nq_Stock_high_frequency = '人工-股票高频'
        else:
            nq_Stock_high_frequency = ''

        if q_Trend_check == 'y':
            q_Trend = '量化-期货趋势'
        else:
            q_Trend = ''

        if q_Arbitrage_check == 'y':
            q_Arbitrage = '量化-期货套利'
        else:
            q_Arbitrage = ''

        if q_High_frequency_check == 'y':
            q_High_frequency = '量化-期货高频'
        else:
            q_High_frequency = ''

        if nq_Trend_check == 'y':
            nq_Trend = '人工-期货趋势'
        else:
            nq_Trend = ''

        if nq_Arbitrage_check == 'y':
            nq_Arbitrage = '人工-期货套利'
        else:
            nq_Arbitrage = ''

        if nq_High_frequency_check == 'y':
            nq_High_frequency = '人工-期货高频'
        else:
            nq_High_frequency = ''

        if bond_s_check == 'y':
            bond_s = '债券策略'
        else:
            bond_s = ''

        if mix_check == 'y':
            mix = '混合策略'
        else:
            mix = ''

        fof_check = request.form.get('fof')
        own_check = request.form.get('own')
        regular_check = request.form.get('regular')

        if fof_check == 'y':
            fof = 'fof子资金'
        else:
            fof = ''

        if own_check == 'y':
            own = '公司自有资金'
        else:
            own = ''

        if regular_check == 'y':
            regular = '普通资金'
        else:
            regular = ''

        partner_bank = request.form.get('pp_partner_bank')
        partner_broker = request.form.get('pp_partner_broker')
        date = request.form.get('date')
        # date = PPform.date.data.strftime('%Y-%m-%d')
        address = request.form.get('address')
        visitor = request.form.get('visitor')
        contacter = request.form.get('c_name')
        position = request.form.get('c_position')
        cellphone = request.form.get('c_cellphone')
        note = request.form.get('note').replace('\r\n', '_')

        file_dir = os.path.join(Config.basedir, Config.UPLOAD_PATH)  # 拼接成合法文件夹地址
        if not os.path.exists(file_dir):
            os.makedirs(file_dir)

        files = request.files.getlist('memoF')
        filenames = []
        for f in files:
            if f:
                filename = pp_name + '_' + f.filename
                f.save(os.path.join(Config.UPLOAD_PATH, filename))
                filenames.append(filename)

        memo = ''
        for i in filenames:
            memo += i + ' | '

        newPP = Private_placement(
            pp_name=pp_name, pp_management_scale=management_scale, pp_futures_scale=futures_scale,
            pp_qualification=qualification, pp_cooperation_mod=coop_mod,
            pp_partner_bank=partner_bank, pp_partner_broker=partner_broker,
            memo=memo, note=note, pp_established_time=pp_established_time,
            RoW_ratio=RoW_ratio, reward_within_3yrs=reward_within_3yrs)
        db.session.add(newPP)
        db.session.commit()
        NPP = db.session.query(Private_placement).filter(Private_placement.pp_name == pp_name)
        pid = NPP[0].id

        # 将新数据存入数据库
        newInv_scope = Inv_scope(stock=stock, futures=futures, bond=bond, pp_id=pid)
        newVisit = Visit(date=date, address=address, visitor=visitor, c_name=contacter, c_position=position, c_cellphone=cellphone, pp_id=pid)
        newStrategy = Strategy(
            q_Stock_long=q_Stock_long, q_Market_neutral=q_Market_neutral, q_Stock_high_frequency=q_Stock_high_frequency,
            q_Trend=q_Trend, q_Arbitrage=q_Arbitrage, q_High_frequency=q_High_frequency,
            nq_Stock_long=nq_Stock_long, nq_Market_neutral=nq_Market_neutral, nq_Stock_high_frequency=nq_Stock_high_frequency,
            nq_Trend=nq_Trend, nq_Arbitrage=nq_Arbitrage, nq_High_frequency=nq_High_frequency,
            bond_s=bond_s, mix=mix, pp_id=pid)
        newFund = Fund(fof=fof, own=own, regular=regular, pp_id=pid)

        newoperationRecord = operationRecord(user_id=current_user.id, username=current_user.username, operation='添加', pp=pp_name, time=datetime.now())

        db.session.add(newoperationRecord)
        db.session.add(newInv_scope)
        db.session.add(newVisit)
        db.session.add(newStrategy)
        db.session.add(newFund)
        db.session.commit()

        return redirect('index')

    flash('信息类型错误')
    return redirect('index')


@app.route('/delete', methods=['GET', 'POST'])
@login_required
def delete():
    if request.method == 'POST':
        checkedRows = request.form.getlist('checkbox2')
        for i in checkedRows:
            pp = Private_placement.query.filter_by(id=i).all()
            inv_scope = Inv_scope.query.filter_by(pp_id=i).all()
            strategy = Strategy.query.filter_by(pp_id=i).all()
            fund = Fund.query.filter_by(pp_id=i).all()
            visit = Visit.query.filter_by(pp_id=i).all()
            fn = pp[0].memo.split(" | ")
            newoperationRecord = operationRecord(user_id=current_user.id, username=current_user.username, operation='删除', pp=pp[0].pp_name, time=datetime.now())
            db.session.add(newoperationRecord)

            for o in fn:
                f = os.path.join(Config.UPLOAD_PATH, o)
                if os.path.isfile(f):
                    os.remove(f)
            for o in pp:
                db.session.delete(o)
                db.session.commit()
            for o in inv_scope:
                db.session.delete(o)
                db.session.commit()
            for o in strategy:
                db.session.delete(o)
                db.session.commit()
            for o in fund:
                db.session.delete(o)
                db.session.commit()
            for o in visit:
                db.session.delete(o)
                db.session.commit()

        db.session.commit()

        return redirect('index')
    return redirect('index')


@app.route('/edit', methods=['GET', 'POST'])
@login_required
def edit():
    # Sform = SearchForm()
    # Fform = FilterF()
    form = PPform()
    form.pp_qualification.choices = [('1', '仅备案'), ('2', '仅会员'), ('3', '投顾资质')]
    if form.validate_on_submit():
        pp_id_1 = request.form.get('pp_id')
        pp_name = request.form.get('pp_name')
        RoW_ratio = request.form.get('RoW_ratio')
        reward_within_3yrs = request.form.get('reward_within_3yrs')
        pp_established_time = request.form.get('pp_established_time')
        management_scale = float(request.form.get('pp_management_scale')) * 100000000
        futures_scale = float(request.form.get('pp_futures_scale')) * 100000000
        qualification = request.form.get('pp_qualification')
        
        if qualification == '1':
            qualification = '仅备案'
        elif qualification == '2':
            qualification = '仅会员'
        else:
            qualification = '投顾资质'

        note = request.form.get('note').replace('\r\n', '_')

        stock_check = request.form.get('stock')
        futures_check = request.form.get('futures')
        bond_check = request.form.get('bond')

        if stock_check == 'y':
            stock = '股票'
        else:
            stock = ''

        if futures_check == 'y':
            futures = '期货'
        else:
            futures = ''

        if bond_check == 'y':
            bond = '债券'
        else:
            bond = ''

        coop_mod = request.form.get('pp_cooperation_mod')

        q_Stock_long_check = request.form.get('q_Stock_long')
        q_Market_neutral_check = request.form.get('q_Market_neutral')
        q_Stock_high_frequency_check = request.form.get('q_Stock_high_frequency')
        nq_Stock_long_check = request.form.get('nq_Stock_long')
        nq_Market_neutral_check = request.form.get('nq_Market_neutral')
        nq_Stock_high_frequency_check = request.form.get('nq_Stock_high_frequency')
        q_Trend_check = request.form.get('q_Trend')
        q_Arbitrage_check = request.form.get('q_Arbitrage')
        q_High_frequency_check = request.form.get('q_High_frequency')
        nq_Trend_check = request.form.get('nq_Trend')
        nq_Arbitrage_check = request.form.get('nq_Arbitrage')
        nq_High_frequency_check = request.form.get('nq_High_frequency')
        bond_s_check = request.form.get('bond_s')
        mix_check = request.form.get('mix')

        if q_Stock_long_check == 'y':
            q_Stock_long = '量化-股票多头'
        else:
            q_Stock_long = ''

        if q_Market_neutral_check == 'y':
            q_Market_neutral = '量化-股票中性'
        else:
            q_Market_neutral = ''

        if q_Stock_high_frequency_check == 'y':
            q_Stock_high_frequency = '量化-股票高频'
        else:
            q_Stock_high_frequency = ''

        if nq_Stock_long_check == 'y':
            nq_Stock_long = '人工-股票多头'
        else:
            nq_Stock_long = ''

        if nq_Market_neutral_check == 'y':
            nq_Market_neutral = '人工-股票中性'
        else:
            nq_Market_neutral = ''

        if nq_Stock_high_frequency_check == 'y':
            nq_Stock_high_frequency = '人工-股票高频'
        else:
            nq_Stock_high_frequency = ''

        if q_Trend_check == 'y':
            q_Trend = '量化-期货趋势'
        else:
            q_Trend = ''

        if q_Arbitrage_check == 'y':
            q_Arbitrage = '量化-期货套利'
        else:
            q_Arbitrage = ''

        if q_High_frequency_check == 'y':
            q_High_frequency = '量化-期货高频'
        else:
            q_High_frequency = ''

        if nq_Trend_check == 'y':
            nq_Trend = '人工-期货趋势'
        else:
            nq_Trend = ''

        if nq_Arbitrage_check == 'y':
            nq_Arbitrage = '人工-期货套利'
        else:
            nq_Arbitrage = ''

        if nq_High_frequency_check == 'y':
            nq_High_frequency = '人工-期货高频'
        else:
            nq_High_frequency = ''

        if bond_s_check == 'y':
            bond_s = '债券策略'
        else:
            bond_s = ''

        if mix_check == 'y':
            mix = '混合策略'
        else:
            mix = ''

        fof_check = request.form.get('fof')
        own_check = request.form.get('own')
        regular_check = request.form.get('regular')

        if fof_check == 'y':
            fof = 'fof子资金'
        else:
            fof = ''

        if own_check == 'y':
            own = '公司自有资金'
        else:
            own = ''

        if regular_check == 'y':
            regular = '普通资金'
        else:
            regular = ''

        partner_bank = request.form.get('pp_partner_bank')
        partner_broker = request.form.get('pp_partner_broker')
        date = request.form.get('date')
        address = request.form.get('address')
        visitor = request.form.get('visitor')
        contacter = request.form.get('c_name')
        position = request.form.get('c_position')
        cellphone = request.form.get('c_cellphone')

        oldmemo = Private_placement.query.filter_by(id=pp_id_1).all()[0].memo.split(" | ")
        oldmemo.pop()
        memoL = request.form.get('memo').split(" | ")
        memoL.pop()
        sameF = []
        diffF = []
        for i in oldmemo:
            for j in memoL:
                if i == j:
                    sameF.append(i)

        for b in (oldmemo + memoL):
            if b not in sameF:
                diffF.append(b)

        for a in diffF:
            f = os.path.join(Config.UPLOAD_PATH, a)
            if os.path.isfile(f):
                os.remove(f)

        files = request.files.getlist('memoF')
        filenames = []
        for f in files:
            if f:
                filename = pp_name + '_' + f.filename
                f.save(os.path.join(Config.UPLOAD_PATH, filename))
                filenames.append(filename)

        memo = request.form.get('memo')
        for i in filenames:
            memo += i + ' | '

        # 找到字段并更新数据
        Private_placement.query.filter_by(id=pp_id_1).update({'pp_name': pp_name})
        Private_placement.query.filter_by(id=pp_id_1).update({'pp_management_scale': management_scale})
        Private_placement.query.filter_by(id=pp_id_1).update({'pp_futures_scale': futures_scale})
        Private_placement.query.filter_by(id=pp_id_1).update({'pp_established_time': pp_established_time})
        Private_placement.query.filter_by(id=pp_id_1).update({'RoW_ratio': RoW_ratio})
        Private_placement.query.filter_by(id=pp_id_1).update({'reward_within_3yrs': reward_within_3yrs})
        Private_placement.query.filter_by(id=pp_id_1).update({'pp_qualification': qualification})
        Private_placement.query.filter_by(id=pp_id_1).update({'pp_cooperation_mod': coop_mod})
        Private_placement.query.filter_by(id=pp_id_1).update({'pp_partner_bank': partner_bank})
        Private_placement.query.filter_by(id=pp_id_1).update({'pp_partner_broker': partner_broker})
        Private_placement.query.filter_by(id=pp_id_1).update({'memo': memo})
        Private_placement.query.filter_by(id=pp_id_1).update({'note': note})

        Inv_scope.query.filter_by(pp_id=pp_id_1).update({'stock': stock})
        Inv_scope.query.filter_by(pp_id=pp_id_1).update({'futures': futures})
        Inv_scope.query.filter_by(pp_id=pp_id_1).update({'bond': bond})

        Visit.query.filter_by(pp_id=pp_id_1).update({'date': date})
        Visit.query.filter_by(pp_id=pp_id_1).update({'address': address})
        Visit.query.filter_by(pp_id=pp_id_1).update({'visitor': visitor})
        Visit.query.filter_by(pp_id=pp_id_1).update({'c_name': contacter})
        Visit.query.filter_by(pp_id=pp_id_1).update({'c_position': position})
        Visit.query.filter_by(pp_id=pp_id_1).update({'c_cellphone': cellphone})

        Strategy.query.filter_by(pp_id=pp_id_1).update({'q_Stock_long': q_Stock_long})
        Strategy.query.filter_by(pp_id=pp_id_1).update({'q_Market_neutral': q_Market_neutral})
        Strategy.query.filter_by(pp_id=pp_id_1).update({'q_Stock_high_frequency': q_Stock_high_frequency})
        Strategy.query.filter_by(pp_id=pp_id_1).update({'q_Trend': q_Trend})
        Strategy.query.filter_by(pp_id=pp_id_1).update({'q_Arbitrage': q_Arbitrage})
        Strategy.query.filter_by(pp_id=pp_id_1).update({'q_High_frequency': q_High_frequency})
        Strategy.query.filter_by(pp_id=pp_id_1).update({'nq_Stock_long': nq_Stock_long})
        Strategy.query.filter_by(pp_id=pp_id_1).update({'nq_Market_neutral': nq_Market_neutral})
        Strategy.query.filter_by(pp_id=pp_id_1).update({'nq_Stock_high_frequency': nq_Stock_high_frequency})
        Strategy.query.filter_by(pp_id=pp_id_1).update({'nq_Trend': nq_Trend})
        Strategy.query.filter_by(pp_id=pp_id_1).update({'nq_Arbitrage': nq_Arbitrage})
        Strategy.query.filter_by(pp_id=pp_id_1).update({'nq_High_frequency': nq_High_frequency})
        Strategy.query.filter_by(pp_id=pp_id_1).update({'bond_s': bond_s})
        Strategy.query.filter_by(pp_id=pp_id_1).update({'mix': mix})

        Fund.query.filter_by(pp_id=pp_id_1).update({'fof': fof})
        Fund.query.filter_by(pp_id=pp_id_1).update({'own': own})
        Fund.query.filter_by(pp_id=pp_id_1).update({'regular': regular})

        newoperationRecord = operationRecord(user_id=current_user.id, username=current_user.username, operation='修改', pp=pp_name, time=datetime.now())
        db.session.add(newoperationRecord)
        db.session.commit()
        return redirect('index')
    return render_template('index.html')


@app.route('/filter', methods=['GET', 'POST'])
@login_required
def filter():
    Sform = SearchForm()
    Fform = FilterF()
    form = PPform()

    per_page = Config.data_per_page
    page = request.args.get(get_page_parameter(), type=int, default=1)

    if Fform.validate_on_submit():
        if request.form.get('S_q_Stock_long') == 'y':
            S_q_Stock_long = 1
        else:
            S_q_Stock_long = 0

        if request.form.get('S_q_Market_neutral') == 'y':
            S_q_Market_neutral = 1
        else:
            S_q_Market_neutral = 0

        if request.form.get('S_q_Stock_high_frequency') == 'y':
            S_q_Stock_high_frequency = 1
        else:
            S_q_Stock_high_frequency = 0

        if request.form.get('S_q_Trend') == 'y':
            S_q_Trend = 1
        else:
            S_q_Trend = 0

        if request.form.get('S_q_Arbitrage') == 'y':
            S_q_Arbitrage = 1
        else:
            S_q_Arbitrage = 0

        if request.form.get('S_q_High_frequency') == 'y':
            S_q_High_frequency = 1
        else:
            S_q_High_frequency = 0

        if request.form.get('S_bond_s') == 'y':
            S_bond_s = 1
        else:
            S_bond_s = 0

        if request.form.get('S_nq_Stock_long') == 'y':
            S_nq_Stock_long = 1
        else:
            S_nq_Stock_long = 0

        if request.form.get('S_nq_Market_neutral') == 'y':
            S_nq_Market_neutral = 1
        else:
            S_nq_Market_neutral = 0

        if request.form.get('S_nq_Stock_high_frequency') == 'y':
            S_nq_Stock_high_frequency = 1
        else:
            S_nq_Stock_high_frequency = 0

        if request.form.get('S_nq_Trend') == 'y':
            S_nq_Trend = 1
        else:
            S_nq_Trend = 0

        if request.form.get('S_nq_Arbitrage') == 'y':
            S_nq_Arbitrage = 1
        else:
            S_nq_Arbitrage = 0

        if request.form.get('S_nq_High_frequency') == 'y':
            S_nq_High_frequency = 1
        else:
            S_nq_High_frequency = 0

        if request.form.get('S_mix') == 'y':
            S_mix = 1
        else:
            S_mix = 0

        if request.form.get('S_fof') == 'y':
            S_fof = 1
        else:
            S_fof = 0

        if request.form.get('S_own') == 'y':
            S_own = 1
        else:
            S_own = 0

        if request.form.get('S_regular') == 'y':
            S_regular = 1
        else:
            S_regular = 0

        S_None = S_q_Stock_long == 0 and S_q_Market_neutral == 0 and S_q_Stock_high_frequency == 0 and S_q_Trend == 0 and S_q_Arbitrage == 0 and S_q_High_frequency == 0 and S_nq_Stock_long == 0 and S_nq_Market_neutral == 0 and S_nq_Stock_high_frequency == 0 and S_nq_Trend == 0 and S_nq_Arbitrage == 0 and S_nq_High_frequency == 0 and S_bond_s == 0 and S_mix == 0
        F_None = S_fof == 0 and S_own == 0 and S_regular == 0

        if S_None and not F_None:
            pagination = db.session.query(Private_placement, Inv_scope, Strategy, Fund, Visit).filter(and_(
                Fund.fof == S_fof, Fund.own == S_own, Fund.regular == S_regular, Strategy.pp_id == Fund.pp_id,
                Private_placement.id == Inv_scope.pp_id,
                Private_placement.id == Strategy.pp_id,
                Private_placement.id == Fund.pp_id,
                Private_placement.id == Visit.pp_id)).paginate(page=page, per_page=per_page, error_out=False)
        elif not S_None and F_None:
            pagination = db.session.query(Private_placement, Inv_scope, Strategy, Fund, Visit).filter(and_(
                Strategy.q_Stock_long == S_q_Stock_long, Strategy.q_Market_neutral == S_q_Market_neutral, Strategy.q_Stock_high_frequency == S_q_Stock_high_frequency,
                Strategy.q_Trend == S_q_Trend, Strategy.q_Arbitrage == S_q_Arbitrage, Strategy.q_High_frequency == S_q_High_frequency,
                Strategy.nq_Stock_long == S_nq_Stock_long, Strategy.nq_Market_neutral == S_nq_Market_neutral, Strategy.nq_Stock_high_frequency == S_nq_Stock_high_frequency,
                Strategy.nq_Trend == S_nq_Trend, Strategy.nq_Arbitrage == S_nq_Arbitrage, Strategy.nq_High_frequency == S_nq_High_frequency,
                Strategy.bond_s == S_bond_s, Strategy.mix == S_mix,
                Private_placement.id == Inv_scope.pp_id,
                Private_placement.id == Strategy.pp_id,
                Private_placement.id == Fund.pp_id,
                Private_placement.id == Visit.pp_id)).paginate(page=page, per_page=per_page, error_out=False)
        elif S_None and F_None:
            pagination = db.session.query(Private_placement, Inv_scope, Strategy, Fund, Visit).filter(and_(
                Private_placement.id == Inv_scope.pp_id,
                Private_placement.id == Strategy.pp_id,
                Private_placement.id == Fund.pp_id,
                Private_placement.id == Visit.pp_id)).paginate(page=page, per_page=per_page, error_out=False)
        else:
            pagination = db.session.query(Private_placement, Inv_scope, Strategy, Fund, Visit).filter(and_(
                Strategy.q_Stock_long == S_q_Stock_long, Strategy.q_Market_neutral == S_q_Market_neutral, Strategy.q_Stock_high_frequency == S_q_Stock_high_frequency,
                Strategy.q_Trend == S_q_Trend, Strategy.q_Arbitrage == S_q_Arbitrage, Strategy.q_High_frequency == S_q_High_frequency,
                Strategy.nq_Stock_long == S_nq_Stock_long, Strategy.nq_Market_neutral == S_nq_Market_neutral, Strategy.nq_Stock_high_frequency == S_nq_Stock_high_frequency,
                Strategy.nq_Trend == S_nq_Trend, Strategy.nq_Arbitrage == S_nq_Arbitrage, Strategy.nq_High_frequency == S_nq_High_frequency,
                Strategy.bond_s == S_bond_s, Strategy.mix == S_mix, Fund.fof == S_fof, Fund.own == S_own, Fund.regular == S_regular, Strategy.pp_id == Fund.pp_id,
                Private_placement.id == Inv_scope.pp_id,
                Private_placement.id == Strategy.pp_id,
                Private_placement.id == Fund.pp_id,
                Private_placement.id == Visit.pp_id)).paginate(page=page, per_page=per_page, error_out=False)

        result = pagination.items
        num = len(result)

        for i in result:
            fw = ''
            cl = ''
            zj = ''

            if i[1].stock == 1:
                fw = fw + '股票 '
            if i[1].futures == 1:
                fw = fw + '期货 '
            if i[1].bond == 1:
                fw = fw + '债券'
            i[1].result = fw

            if i[2].q_Stock_long == 1 or i[2].q_Market_neutral == 1 or i[2].q_Stock_high_frequency == 1 or i[2].nq_Stock_long == 1 or i[2].nq_Market_neutral == 1 or i[2].nq_Stock_high_frequency == 1:
                cl = cl + '股票策略 '
            if i[2].q_Trend == 1 or i[2].q_Arbitrage == 1 or i[2].q_High_frequency == 1 or i[2].nq_Trend == 1 or i[2].nq_Arbitrage == 1 or i[2].nq_High_frequency == 1:
                cl = cl + '管理期货 '
            if i[2].bond_s == 1:
                cl = cl + '债券策略 '
            if i[2].mix == 1:
                cl = cl + '混合策略'
            i[2].result = cl

            if i[3].fof == 1:
                zj = zj + 'fof子基金      '
            if i[3].own == 1:
                zj = zj + '公司自有资金   '
            if i[3].regular == 1:
                zj = zj + '普通资金'
            i[3].result = zj

        context = {
            'pagination': pagination,
            'u': result,
            'num': num
        }

        return render_template('index.html', **context, form=form, Fform=Fform, Sform=Sform)
    return redirect('index')


@app.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    Sform = SearchForm()
    Fform = FilterF()
    form = PPform()
    form.pp_qualification.choices = [('1', '仅备案'), ('2', '仅会员'), ('3', '投顾资质')]

    PP = request.form.get('search_PP')
    MS = request.form.get('search_management_scale')
    RF = request.form.get('search_Referrer')
    SG = request.form.get('search_strategy')
    SFund = request.form.get('search_fund')


    per_page = Config.data_per_page
    page = request.args.get(get_page_parameter(), type=int, default=1)

    if Sform.validate_on_submit():
        pagination = db.session.query(Private_placement, Inv_scope, Strategy, Fund, Visit).filter(and_(
            Private_placement.id == Inv_scope.pp_id,
            Private_placement.id == Strategy.pp_id,
            Private_placement.id == Fund.pp_id,
            Private_placement.id == Visit.pp_id,
            Private_placement.pp_name.like('%' + PP + '%'),
            Private_placement.pp_management_scale.like('%' + MS + '%'),
            Private_placement.pp_partner_bank.like('%'+ RF +'%'))).filter(or_(
            Strategy.q_Stock_long.like('%' + SG + '%'),
            Strategy.q_Market_neutral.like('%' + SG + '%'),
            Strategy.q_Stock_high_frequency.like('%' + SG + '%'),
            Strategy.nq_Stock_long.like('%' + SG + '%'),
            Strategy.nq_Market_neutral.like('%' + SG + '%'),
            Strategy.nq_Stock_high_frequency.like('%' + SG + '%'),
            Strategy.q_Trend.like('%' + SG + '%'),
            Strategy.q_Arbitrage.like('%' + SG + '%'),
            Strategy.q_High_frequency.like('%' + SG + '%'),
            Strategy.nq_Trend.like('%' + SG + '%'),
            Strategy.nq_Arbitrage.like('%' + SG + '%'),
            Strategy.nq_High_frequency.like('%' + SG + '%'))).filter(or_(
            Fund.fof.like('%' + SFund + '%'),
            Fund.own.like('%' + SFund + '%'),
            Fund.regular.like('%' + SFund + '%'))).paginate(page=page, per_page=per_page, error_out=False)

        result = pagination.items
        num = len(result)

        for i in result:
            fw = ''
            cl = ''
            zj = ''

            if i[1].stock == '股票':
                fw = fw + '股票\r\n'
            if i[1].futures == '期货':
                fw = fw + '期货\r\n'
            if i[1].bond == '债券':  
                fw = fw + '债券'
            i[1].result = fw

            if i[2].q_Stock_long == '量化-股票多头' or i[2].q_Market_neutral == '量化-股票中性' or i[2].q_Stock_high_frequency == '量化-股票高频' or i[2].nq_Stock_long == '人工-股票多头' or i[2].nq_Market_neutral == '人工-股票中性' or i[2].nq_Stock_high_frequency == '人工-股票高频':
                cl = cl + '股票策略\r\n'
            if i[2].q_Trend == '量化-期货趋势' or i[2].q_Arbitrage == '量化-期货套利' or i[2].q_High_frequency == '量化-期货高频' or i[2].nq_Trend == '人工-期货趋势' or i[2].nq_Arbitrage == '人工-期货套利' or i[2].nq_High_frequency == '人工-期货高频':
                cl = cl + '管理期货\r\n'
            if i[2].bond_s == '债券策略':
                cl = cl + '债券策略\r\n'
            if i[2].mix == '混合策略':
                cl = cl + '混合策略'
            i[2].result = cl

            if i[3].fof == 'fof子基金':
                zj = zj + 'fof子基金 '
            if i[3].own == '公司自有资金':
                zj = zj + '公司自有资金 '
            if i[3].regular == '普通资金':
                zj = zj + '普通资金'
            i[3].result = zj

        context = {
            'pagination': pagination,
            'u': result,
            'num': num
        }

        if PP == '' and SG == '' and MS == '' and RF == '' and SFund == '':
            return redirect('index')
        else:
            return render_template('index.html', **context, form=form, Fform=Fform, Sform=Sform)
    return redirect('index')


@app.route('/downloadfile/<fn>', methods=['GET', 'POST'])
@login_required
def downloadfile(fn):
    file_dir = os.path.join(Config.basedir, Config.UPLOAD_PATH)  # 拼接成合法文件夹地址
    return send_from_directory(file_dir, fn, as_attachment=True)


@app.route('/downloadfilexx', methods=['GET', 'POST'])
@login_required
def downloadfilexx():
    file_dir = os.path.join(Config.basedir, Config.UPLOAD_PATH)  # 拼接成合法文件夹地址
    return send_from_directory(file_dir, request.form.get('downloadfile'), as_attachment=True)


@app.route('/read_csv', methods=['GET', 'POST'])
@login_required
def read_csv():
    # file_dir = os.path.join(Config.basedir, Config.UPLOAD_PATH)
    files = request.files.getlist('csv')
    for f in files:
        f.save(os.path.join(Config.UPLOAD_PATH, f.filename))

    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
    con = engine.connect()
    # df = pd.read_excel(io=os.path.join(Config.UPLOAD_PATH, files[0].filename))

    dff = pd.read_excel(io=os.path.join(Config.UPLOAD_PATH, files[0].filename), sheet_name=None)
    # print(type(dff[0]))

    def map_types(df):
        dtypedict = {}
        for i, j in zip(df.columns, df.dtypes):
            if "object" in str(j):
                dtypedict.update({i: NVARCHAR(length=255)})
            if "float" in str(j):
                dtypedict.update({i: Float(precision=2, asdecimal=True)})
            if "int" in str(j):
                dtypedict.update({i: Integer()})
            if "datetime" in str(j):
                dtypedict.update({i: Date()})
        return dtypedict

    for i in dff:
        sheet = dff[i]
        dtypedict = map_types(sheet)
        sheet.to_sql(name=i, con=con, if_exists='replace', index=True, index_label='id', dtype=dtypedict)
        # sheet['时间'] = sheet['时间'].strftime('%Y-%m-%d')
        # xxx =  sheet.values.tolist()
        # time = [x[1] for x in xxx]
        # timelist = []
        # for i in time:
        #     timelist.append(i.to_pydatetime().strftime('%Y-%m-%d'))

        # print(type(timelist[2]))

        # net_worth = [x[2] for x in xxx]
        # print(type(net_worth[0])
        time = []
        for i in sheet['时间']:
            time.append(i.strftime("%Y-%m-%d"))
        # print(sheet['时间'][0].strftime("%Y-%m-%d"))
        line = (
               Line()
               .add_xaxis(time)
               .add_yaxis('累计净值', sheet['累计净值'])
               .set_global_opts(
                   title_opts=opts.TitleOpts(title="净值曲线", subtitle="我是副标题"),
                   toolbox_opts=opts.ToolboxOpts(),
                   bool = True)
                .InitOpts(width = "100%", height = "100%")
        )
        # line.render('chart.html')    


    # def bar_base() -> Bar:
    #     c = (
    #         Bar()
    #         .add_xaxis(["衬衫", "羊毛衫", "雪纺衫", "裤子", "高跟鞋", "袜子"])
    #         .add_yaxis("商家A", [5, 20, 36, 10, 75, 90])
    #         .add_yaxis("商家B", [15, 25, 16, 55, 48, 8])
    #         .set_global_opts(title_opts=opts.TitleOpts(title="Bar-基本示例", subtitle="我是副标题"))
    #     )
    #     return c

    # c = bar_base()
    return render_template('chart.html', chart=Markup(line.render_embed()))
