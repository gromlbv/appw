from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

from sqlalchemy.orm import Mapped, relationship


db = SQLAlchemy()

def migrate(app, db):
    Migrate(app, db)

def create_app(app):
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
    app.config ["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    migrate(app, db)
    return app

def create_tables():
    db.create_all()



class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(24))
    password = db.Column(db.String(32))

    is_premium = db.Column(db.Boolean, default=False)
    is_approved = db.Column(db.Boolean, default=False)
            
    def anonim(self):
        return {
            "username": self.username,
            "is_premium": self.is_premium,
            "is_approved": self.is_approved
        }

# class Messages(db.Model):
#     id = db.Column(db.Integer, primary_key=True)


# Игры

class GameInfo(db.Model):
    __tablename__ = 'games_info'
    id = db.Column(db.Integer, primary_key=True)

    game_id = db.Column(db.Integer, db.ForeignKey('games.id'))
    game = relationship("Game", uselist=False, back_populates="info")

    description = db.Column(db.Text)
    price = db.Column(db.Integer)
    release_date = db.Column(db.Date)
    language = db.Column(db.Text)
    published_by = db.Column(db.String(20), db.ForeignKey('users.id'))
    published_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)

    app_type = db.Column(db.String(100))
    category = db.Column(db.String(100))


class GameDownload(db.Model):
    __tablename__ = 'downloads'
    id = db.Column(db.Integer, primary_key=True)
    
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'))
    game = relationship("Game", back_populates="downloads")

    title = db.Column(db.String(50))
    description = db.Column(db.String(100))

    file_link = db.Column(db.String(255))
    file_size = db.Column(db.Integer)
    order = db.Column(db.Integer, default=0)
    is_important = db.Column(db.Boolean, default=False)


class Game(db.Model):
    __tablename__ = 'games'
    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.Text, nullable=False)
    preview = db.Column(db.Text)
    link = db.Column(db.String(32), nullable=False, unique=True)
    comments_allowed = db.Column(db.Boolean, default=False)

    is_unity_build = db.Column(db.Boolean, default=False)
    is_archived = db.Column(db.Boolean, default=False, index=True)

    info = relationship("GameInfo", uselist=False, back_populates="game")
    downloads = relationship("GameDownload", back_populates="game", order_by="GameDownload.order")
    stats = relationship("GameStats", uselist=False, back_populates="game")


class GameStats(db.Model):
    __tablename__ = 'game_stats'
    id = db.Column(db.Integer, primary_key=True)
    
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'), unique=True)
    game = relationship("Game", back_populates="stats")
    
    serious_fun = db.Column(db.Integer, default=50)
    utility_gamified = db.Column(db.Integer, default=50)

    story = db.Column(db.Integer, default=50)
    gameplay = db.Column(db.Integer, default=50)
    solo = db.Column(db.Integer, default=50)
    coop = db.Column(db.Integer, default=50)


# class GameComment(db.Model):
#     __tablename__ = 'game_comments'
#     id = db.Column(db.Integer, primary_key=True)

#     user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
#     game_id = db.Column(db.Integer, db.ForeignKey('games.id'), nullable=False)
#     user = relationship("User", back_populates="game_comments")
#     game = relationship("Game", back_populates="game_comments")
#     reply = relationship("GameComment", back_populates="comment")

#     text = db.Column(db.Text)
#     is_positive = db.Column(db.Boolean)
#     date = db.Column(db.DateTime, default=db.func.current_timestamp())


# class CommentReply(db.Model):
#     __tablename__ = 'comment_replies'
#     id = db.Column(db.Integer, primary_key=True)
    
#     user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
#     comment_id = db.Column(db.Integer, db.ForeignKey('game_comments.id'), nullable=False)

#     user = relationship("User", back_populates="comment_replies")
#     comment = relationship("GameComment", back_populates="replies")

#     text = db.Column(db.Text)
#     date = db.Column(db.DateTime, default=db.func.current_timestamp())



class SharedFile(db.Model):
    __tablename__ = 'shared_files'
    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.Text)
    preview = db.Column(db.Text)
    file_link = db.Column(db.Text)
    uploaded_by = db.Column(db.String(20), db.ForeignKey('users.id'))
    is_active = db.Column(db.Boolean, default=True)

    # Премиум фичи
    expires = db.Column(db.Integer)
    auto_download = db.Column(db.Integer)
    link = db.Column(db.String(32))


# users = User.query.all()
# users = User.query.with_entities(User.username, User.password).all()
# users = [user.to_dict() for user in User.query.all()]
# users = User.query.filter(User.username == 'admin').all()

from datetime import datetime

class Collection(db.Model):
    __tablename__ = 'collections'
    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(500))
    link = db.Column(db.String(200), unique=True, index=True)
    is_archived = db.Column(db.Boolean, default=False, index=True)

    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    owner = db.relationship('User', backref='owned_collections')
    
    games = db.relationship('CollectionGame', backref=db.backref('parent_collection'), lazy='dynamic',overlaps="game_associations,collection")
    members = db.relationship('CollectionUser', backref=db.backref('collection'), lazy='dynamic', primaryjoin='Collection.id == CollectionUser.collection_id'
)

class CollectionGame(db.Model):
    __tablename__ = 'collection_games'
    
    collection_id = db.Column(db.Integer, db.ForeignKey('collections.id'), primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'), primary_key=True)
    
    order = db.Column(db.Integer, default=0)
    added_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    added_at = db.Column(db.DateTime, default=datetime.now) 
    is_featured = db.Column(db.Boolean, default=False)
    
    collection = db.relationship('Collection', backref='game_associations', overlaps="games,parent_collection")
    game = db.relationship('Game', backref='collection_associations')
    added_user = db.relationship('User')


class CollectionUser(db.Model):
    __tablename__ = 'collection_users'
    collection_id = db.Column(db.Integer, db.ForeignKey('collections.id'), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    
    can_edit = db.Column(db.Boolean, default=False)
    can_view = db.Column(db.Boolean, default=False)
    
    invited_at = db.Column(db.DateTime, default=datetime.now)
    invited_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    user = db.relationship('User', foreign_keys=[user_id], backref='collection_permissions')
    inviter = db.relationship('User', foreign_keys=[invited_by])