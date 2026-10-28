"""Model de Category."""
from database import db
from utils.helpers import COLOR_LENGTH, DEFAULT_COLOR, utcnow


class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(300), nullable=True)
    color = db.Column(db.String(COLOR_LENGTH), default=DEFAULT_COLOR)
    created_at = db.Column(db.DateTime, default=utcnow)

    @staticmethod
    def is_valid_color(color):
        return bool(color) and len(color) == COLOR_LENGTH and color.startswith('#')

