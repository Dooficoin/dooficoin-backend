from database import db
from datetime import datetime

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    amount = db.Column(db.String(100), nullable=False)
    currency = db.Column(db.String(10), nullable=False)
    transaction_type = db.Column(db.String(50), nullable=False) # e.g., 'transfer', 'purchase', 'mining_reward'
    item_id = db.Column(db.Integer, db.ForeignKey("items.id"), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "sender_id": self.sender_id,
            "receiver_id": self.receiver_id,
            "amount": self.amount,
            "currency": self.currency,
            "transaction_type": self.transaction_type,
            "item_id": self.item_id,
            "timestamp": self.timestamp.isoformat()
        }


