from database import db
from datetime import datetime

class RevokedToken(db.Model):
    __tablename__ = 'revoked_tokens'
    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(120), unique=True, nullable=False)
    revoked_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<RevokedToken {self.jti}>'

    def to_dict(self):
        return {
            'id': self.id,
            'jti': self.jti,
            'revoked_at': self.revoked_at.isoformat()
        }


