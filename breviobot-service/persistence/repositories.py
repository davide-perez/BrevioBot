from .database import UserDB
import bcrypt

class UserRepository:
    def __init__(self, db):
        self.db = db

    def get(self, **kwargs) -> 'UserDB | None':
        return self.db.query(UserDB).filter_by(**kwargs).first()

    def create(self, user, is_verified=False, verification_token=None) -> 'UserDB':
        hashed_password = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt())
        db_user = UserDB(
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            password=hashed_password.decode('utf-8'),
            is_verified=is_verified,
            verification_token=verification_token
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user

    def authenticate(self, username: str, password: str) -> 'UserDB | None':
        user = self.get(username=username)
        if not user:
            return None
        if bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
            return user
        return None

    def verify_user(self, user):
        user.is_verified = True
        user.verification_token = None
        self.db.add(user)
        self.db.commit()