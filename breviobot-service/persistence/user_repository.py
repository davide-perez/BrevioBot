from .database import UserDB
from .db_session import SessionLocal

class UserRepository:
    def __init__(self, db_session_factory=SessionLocal):
        self.db_session_factory = db_session_factory

    def create(self, user):
        db = self.db_session_factory()
        try:
            db_user = UserDB(
                username=user.username,
                email=user.email,
                full_name=user.full_name,
                is_active=user.is_active,
                is_admin=user.is_admin,
                hashed_password=user.hashed_password
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