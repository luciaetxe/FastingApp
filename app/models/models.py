from app import db
from datetime import datetime

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    history = db.relationship("FastHistory", backref="user", lazy=True)

    @property
    def completed_fasts_streak(self):
        if not self.history:
            return 0
        fasts = sorted(self.history, key=lambda f: f.date, reverse=True)
        streak = 1
        today = datetime.now().date()
        last_fast_date = fasts[0].date.date()

        if (today - last_fast_date).days > 2:
            return 0
        
        for i in range(1, len(fasts)):
            current_date = fasts[i].date.date()
            previous_date = fasts[i-1].date.date()
            if (previous_date - current_date).days <=2:
                streak += 1
            else:
                break
        return streak
    
class Fast(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=True)
    hours_planned = db.Column(db.Integer, nullable=False)
    planned_end_time = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(50), nullable=True)

class FastHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    duration_hours = db.Column(db.Integer, nullable=False)
    hours_planned = db.Column(db.Integer, nullable=False)