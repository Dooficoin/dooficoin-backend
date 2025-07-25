from database import db
from datetime import datetime

class SecurityLog(db.Model):
    """Modelo para armazenar logs de segurança e eventos relacionados."""
    
    __tablename__ = 'security_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    event_type = db.Column(db.String(50), nullable=False)
    severity = db.Column(db.String(20), nullable=False)  # info, warning, error, critical
    ip_address = db.Column(db.String(50))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    details = db.Column(db.Text)
    
    user = db.relationship('User', backref='security_logs')
    
    def __repr__(self):
        return f'<SecurityLog {self.id}: {self.event_type} ({self.severity})>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'event_type': self.event_type,
            'severity': self.severity,
            'ip_address': self.ip_address,
            'user_id': self.user_id,
            'details': self.details
        }

class FraudAlert(db.Model):
    """Modelo para armazenar alertas de fraude detectados."""
    
    __tablename__ = 'fraud_alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    player_id = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=False)
    alert_type = db.Column(db.String(50), nullable=False)
    details = db.Column(db.Text)
    risk_score = db.Column(db.Float, default=0.0)
    reviewed = db.Column(db.Boolean, default=False)
    reviewed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    review_timestamp = db.Column(db.DateTime, nullable=True)
    action_taken = db.Column(db.Text, nullable=True)
    
    player = db.relationship('Player', backref='fraud_alerts')
    reviewer = db.relationship('User', backref='reviewed_alerts')
    
    def __repr__(self):
        return f'<FraudAlert {self.id}: {self.alert_type} for Player {self.player_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'player_id': self.player_id,
            'alert_type': self.alert_type,
            'details': self.details,
            'risk_score': self.risk_score,
            'reviewed': self.reviewed,
            'reviewed_by': self.reviewed_by,
            'review_timestamp': self.review_timestamp.isoformat() if self.review_timestamp else None,
            'action_taken': self.action_taken
        }

class LoginAttempt(db.Model):
    """Modelo para armazenar tentativas de login para análise de segurança."""
    
    __tablename__ = 'login_attempts'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    ip_address = db.Column(db.String(50), nullable=False)
    username = db.Column(db.String(100))
    success = db.Column(db.Boolean, default=False)
    user_agent = db.Column(db.String(255))
    
    def __repr__(self):
        status = "Success" if self.success else "Failed"
        return f'<LoginAttempt {self.id}: {status} from {self.ip_address}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'ip_address': self.ip_address,
            'username': self.username,
            'success': self.success,
            'user_agent': self.user_agent
        }

class BlockedIP(db.Model):
    """Modelo para armazenar IPs bloqueados por atividades suspeitas."""
    
    __tablename__ = 'blocked_ips'
    
    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(50), nullable=False, unique=True)
    blocked_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    blocked_until = db.Column(db.DateTime, nullable=False)
    reason = db.Column(db.String(255))
    
    def __repr__(self):
        return f'<BlockedIP {self.ip_address} until {self.blocked_until}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'ip_address': self.ip_address,
            'blocked_at': self.blocked_at.isoformat(),
            'blocked_until': self.blocked_until.isoformat(),
            'reason': self.reason
        }
    
    @property
    def is_active(self):
        """Verifica se o bloqueio ainda está ativo."""
        return datetime.utcnow() < self.blocked_until

