"""Model de Task — entidade, persistência e invariantes do agregado."""
from database import db
from utils.helpers import (
    DEFAULT_PRIORITY,
    MAX_PRIORITY,
    MAX_TAGS_LENGTH,
    MAX_TITLE_LENGTH,
    MIN_PRIORITY,
    MIN_TITLE_LENGTH,
    STATUS_PENDING,
    TERMINAL_STATUSES,
    VALID_STATUSES,
    utcnow,
)


class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(MAX_TITLE_LENGTH), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default=STATUS_PENDING)
    priority = db.Column(db.Integer, default=DEFAULT_PRIORITY)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)
    due_date = db.Column(db.DateTime, nullable=True)
    tags = db.Column(db.String(MAX_TAGS_LENGTH), nullable=True)

    user = db.relationship('User', backref='tasks')
    category = db.relationship('Category', backref='tasks')

    # ----- invariantes (fonte única da regra) -----

    @staticmethod
    def is_valid_status(status):
        return status in VALID_STATUSES

    @staticmethod
    def is_valid_priority(priority):
        return isinstance(priority, int) and MIN_PRIORITY <= priority <= MAX_PRIORITY

    @staticmethod
    def is_valid_title(title):
        return isinstance(title, str) and MIN_TITLE_LENGTH <= len(title) <= MAX_TITLE_LENGTH

    def is_overdue(self):
        """Regra única de atraso (FINDING-011: antes duplicada em 5 lugares)."""
        if self.due_date is None:
            return False
        if self.status in TERMINAL_STATUSES:
            return False
        return self.due_date < utcnow()

    def days_overdue(self):
        if not self.is_overdue():
            return 0
        return (utcnow() - self.due_date).days

    # ----- tags -----

    @property
    def tag_list(self):
        return self.tags.split(',') if self.tags else []

    def set_tags(self, tags):
        if isinstance(tags, list):
            self.tags = ','.join(str(tag) for tag in tags)
        else:
            self.tags = tags

