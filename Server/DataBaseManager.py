from sqlalchemy import Column, String, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database Setup
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    username = Column(String, primary_key=True)
    password = Column(String, unique=True, nullable=False)
    role = Column(String, nullable=False)

class OrdersToken(Base):
    __tablename__ = "orders_tokens"
    token = Column(String, primary_key=True)
    username = Column(String, ForeignKey("users.username"), nullable=False)
    order_id = Column(String, nullable=False)
    order_status = Column(String, nullable=False)

class TWAPOrder(Base):
    __tablename__ = "twap_orders"
    order_id = Column(String, primary_key=True)
    username = Column(String, ForeignKey("users.username"), nullable=False)
    symbol = Column(String, nullable=False)
    quantity = Column(String, nullable=False)
    price = Column(String, nullable=False)
    timestamp = Column(String, nullable=False)
    
DATABASE_URL = "sqlite:///Server/users.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(engine)

class DBM:
    def __init__(self):
        self.SessionLocal = SessionLocal

    def get_user_by_username(self, username: str):
        """Retourne l'utilisateur si trouvé, sinon None."""
        session = self.SessionLocal()
        try:
            return session.query(User).filter(User.username == username).first()
        finally:
            session.close()
    
    def get_password_by_username(self, username: str):
        """Retourne le mot de passe de l'utilisateur si trouvé, sinon None."""
        user = self.get_user_by_username(username)
        return user.password if user else None
    
    def get_role_by_username(self, username: str):
        """Retourne le rôle de l'utilisateur si trouvé, sinon None."""
        user = self.get_user_by_username(username)
        return user.role if user else None
    
    def create_user(self, username: str, password: str, role: str):
        """Crée un nouvel utilisateur."""
        session = self.SessionLocal()
        try:
            user = User(username=username, password=password, role=role)
            session.add(user)
            session.commit()
        finally:
            session.close()

    def get_all_users(self):
        """Retourne la liste de tous les utilisateurs."""
        session = self.SessionLocal()
        try:
            return session.query(User).all()
        finally:
            session.close()

    def delete_user(self, username: str):
        """Supprime un utilisateur."""
        session = self.SessionLocal()
        try:
            user = session.query(User).filter(User.username == username).first()
            session.delete(user)
            session.commit()
        finally:
            session.close()
    
dbm = DBM()

