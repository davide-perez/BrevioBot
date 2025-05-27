from .database import UserDB
from .db_session import SessionLocal
import bcrypt

class UserRepository:
    def __init__(self, db_session_factory=SessionLocal) -> None:
        self.db_session_factory = db_session_factory

    def create(self, user, is_verified=False, verification_token=None) -> 'UserDB':
        db = self.db_session_factory()
        try:
            hashed_password = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt())
            db_user = UserDB(
                username=user.username,
                email=user.email,
                full_name=user.full_name,
                is_active=user.is_active,
                is_admin=user.is_admin,
                password=hashed_password.decode('utf-8'),
                is_verified=is_verified,
                verification_token=verification_token
            )
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            return db_user
        finally:
            db.close()

    def get_by_field(self, field_name: str, value) -> 'UserDB | None':
        db = self.db_session_factory()
        try:
            field = getattr(UserDB, field_name, None)
            if field is None:
                raise ValueError(f"UserDB has no field '{field_name}'")
            return db.query(UserDB).filter(field == value).first()
        finally:
            db.close()

    def get_by_id(self, user_id: int) -> 'UserDB | None':
        return self.get_by_field("id", user_id)

    def get_by_username(self, username: str) -> 'UserDB | None':
        return self.get_by_field("username", username)

    def get_by_email(self, email: str) -> 'UserDB | None':
        return self.get_by_field("email", email)

    def verify_password(self, username: str, password: str) -> 'UserDB | None':
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