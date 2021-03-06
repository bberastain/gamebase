from app import app, db
from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_user, logout_user, login_required
from app.forms import GameForm, LoginForm, RegistrationForm, EditProfileForm, \
    SearchForm, CategoryForm
from app.models import Game, User, Category1, Category2
from werkzeug.urls import url_parse


def init_cats():
    form = SearchForm()
    cat1 = Category1.query.order_by(Category1.id).all()
    cat2 = Category2.query.order_by(Category2.id).all()
    form.category1.choices = [(0, 'N/A')] + \
                             [(x + 1, y.label) for x, y in enumerate(cat1)]
    form.category2.choices = [(0, 'N/A')] + \
                             [(x + 1, y.label) for x, y in enumerate(cat2)]
    return form


@app.route('/category', methods=['GET', 'POST'])
def category():
    form1 = CategoryForm(prefix='form1')
    form2 = CategoryForm(prefix='form2')
    if form1.validate_on_submit():
        category = Category1(label=form1.category.data)
        db.session.add(category)
        db.session.commit()
        flash('New category added')
        return redirect(url_for('index'))
    if form2.validate_on_submit():
        category = Category2(label=form2.category.data)
        db.session.add(category)
        db.session.commit()
        flash('New category added')
        return redirect(url_for('index'))
    return render_template('category.html', form1=form1, form2=form2)


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index():
    form = init_cats()
    recent = Game.query.order_by(Game.id.desc()).all()
    if form.validate_on_submit():
        if form.category1.data == 0 and form.category2.data == 0:
            flash('Please select at least one category')
            return redirect(url_for('index'))
        elif form.category1.data == 0:
            games = Game.query.filter_by(
                    category2_id=form.category2.data).all()
        elif form.category2.data == 0:
            games = Game.query.filter_by(
                    category1_id=form.category1.data).all()
        else:
            games = Game.query.filter_by(
                    category1_id=form.category1.data,
                    category2_id=form.category2.data).all()
        form = init_cats()
        return render_template('index.html', games=games, form=form)
    return render_template('index.html', form=form, recent=recent)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/addgame', methods=['GET', 'POST'])
def addgame():
    form = GameForm()
    cat1 = Category1.query.order_by(Category1.id).all()
    cat2 = Category2.query.order_by(Category2.id).all()
    form.category1.choices = [(0, 'N/A')] + \
                             [(x + 1, y.label) for x, y in enumerate(cat1)]
    form.category2.choices = [(0, 'N/A')] + \
                             [(x + 1, y.label) for x, y in enumerate(cat2)]
    if form.validate_on_submit():
        if form.category1.data == 0 and form.category2.data == 0:
            game = Game(name=form.name.data)
        elif form.category1.data == 0:
            game = Game(name=form.name.data, category2_id=form.category2.data)
        elif form.category2.data == 0:
            game = Game(name=form.name.data, category1_id=form.category1.data)
        else:
            game = Game(name=form.name.data, category1_id=form.category1.data,
                        category2_id=form.category2.data)
        db.session.add(game)
        db.session.commit()
        flash('Thank you for adding a new game!')
        return redirect(url_for('index'))
    return render_template('addgame.html', form=form)


@app.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template('user.html', user=user)


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile',
                           form=form)


@app.route('/favorite/<game>')
@login_required
def favorite(game):
    game = Game.query.filter_by(id=game).first()
    if game is None:
        flash('Game {} not found.'.format(game))
        return redirect(url_for('index'))
    if current_user.is_favorite(game):
        flash('{} is already in your favorites'.format(game.name))
        return redirect(url_for('index'))
    current_user.favorite(game)
    db.session.commit()
    flash('You added {} to your favorites'.format(game.name))
    return redirect(url_for('index'))


@app.route('/unfavorite/<game>')
@login_required
def unfavorite(game):
    game = Game.query.filter_by(id=game).first()
    if game is None:
        flash('Game {} not found.'.format(game))
        return redirect(url_for('index'))
    if not current_user.is_favorite(game):
        flash('{} is not in your favorites'.format(game.name))
        return redirect(url_for('index'))
    current_user.unfavorite(game)
    db.session.commit()
    flash('You removed {} from your favorites'.format(game.name))
    return redirect(url_for('index'))
