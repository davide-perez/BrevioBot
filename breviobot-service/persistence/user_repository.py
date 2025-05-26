from .database import UserDB
from .db_session import SessionLocal
import bcrypt

class UserRepository:
    def __init__(self, db_session_factory=SessionLocal):
        self.db_session_factory = db_session_factory

    def create(self, user):
        db = self.db_session_factory()
        try:
            hashed_password = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt())
            db_user = UserDB(
                username=user.username,
                email=user.email,
                full_name=user.full_name,
                is_active=user.is_active,
                is_admin=user.is_admin,
                password=hashed_password.decode('utf-8')
            )
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            return db_user
        finally:
            db.close()

    def get_by_field(self, field_name, value):
        db = self.db_session_factory()
        try:
            field = getattr(UserDB, field_name, None)
            if field is None:
                raise ValueError(f"UserDB has no field '{field_name}'")
            return db.query(UserDB).filter(field == value).first()
        finally:
            db.close()

    def get_by_id(self, user_id):
        return self.get_by_field("id", user_id)

    def get_by_username(self, username):
        return self.get_by_field("username", username)

    def get_by_email(self, email):
        return self.get_by_field("email", email)

    def verify_password(self, username, password):
        db = self.db_session_factory()
        try:
            user = self.get_by_username(username)
            if not user:
                return None
            import bcrypt
            if bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
                return user
            return None
        finally:
            db.close()