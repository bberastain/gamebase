from app import db, login
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from hashlib import md5


favorites = db.Table('favorites',
                db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
                db.Column('game_id', db.Integer, db.ForeignKey('game.id'))
                )


class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True, unique=True)
    subscribers = db.relationship(
            'User', secondary=favorites,
            backref=db.backref('subscriptions', lazy='dynamic'))

    def __repr__(self):
        return '<Game: {}>'.format(self.name)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    about_me = db.Column(db.String(140))

    def __repr__(self):
        return '<User: {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
            digest, size)

    def favorite(self, game):
        if not self.is_favorite(game):
            self.subscriptions.append(game)

    def unfavorite(self, game):
        if self.is_favorite(game):
            self.subscriptions.remove(game)

    def is_favorite(self, game):
        return self.subscriptions.filter(
            favorites.c.game_id == game.id).count() > 0

    def favorite_games(self):
        return Game.query.join(
            favorites, (favorites.c.game_id == Game.id)).filter(
                favorites.c.user_id == self.id).all()


@login.user_loader
def load_user(id):
    return User.query.get(int(id))
