from sqlalchemy import Column, String, ForeignKey, create_engine, Float, PrimaryKeyConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from fastapi import HTTPException

# Database Setup
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    username = Column(String, primary_key=True)
    password = Column(String, nullable=False)
    role = Column(String, nullable=False)

class OrdersToken(Base):
    __tablename__ = "orders_tokens"
    order_id = Column(String, nullable=False)
    username = Column(String, ForeignKey("users.username"), nullable=False)
    symbol = Column(String, nullable=False)
    duration = Column(Float, nullable=False)
    interval = Column(Float, nullable=False)
    order_status = Column(String, nullable=False)
    __table_args__ = (
    PrimaryKeyConstraint('order_id', 'username'),
    )

class TWAPOrder(Base):
    __tablename__ = "twap_orders"
    order_id = Column(String, ForeignKey("orders_tokens.order_id"), nullable=False)
    username = Column(String, ForeignKey("users.username"), nullable=False)
    symbol = Column(String, nullable=False)
    side = Column(String, nullable=False)
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    timestamp = Column(String, nullable=False)
    __table_args__ = (
        PrimaryKeyConstraint('order_id', 'username', 'timestamp'),
    )
DATABASE_URL = "sqlite:///Server/Utilities/users.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(engine)

# Ensure admin user exists
def ensure_admin_user():
    session = SessionLocal()
    try:
        admin_user = session.query(User).filter(User.username == "admin").first()
        if not admin_user:
            admin_user = User(username="admin", password="admin123", role="admin")
            session.add(admin_user)
            session.commit()
    finally:
        session.close()

ensure_admin_user()

class DBM:
    def __init__(self):
        self.SessionLocal = SessionLocal
        self.ensure_admin_user()

    def ensure_admin_user(self):
        session = self.SessionLocal()
        try:
            admin_user = session.query(User).filter(User.username == "admin").first()
            if not admin_user:
                admin_user = User(username="admin", password="admin123", role="admin")
                session.add(admin_user)
                session.commit()
        finally:
            session.close()

    ### User Management ###

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
        """Supprime un utilisateur et toutes ses données associées."""
        session = self.SessionLocal()
        try:
            # Delete TWAP orders first due to foreign key constraints
            session.query(TWAPOrder).filter(TWAPOrder.username == username).delete()
            # Delete orders tokens
            session.query(OrdersToken).filter(OrdersToken.username == username).delete()
            # Delete user
            user = session.query(User).filter(User.username == username).first()
            if user:
                session.delete(user)
            session.commit()
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=500, detail=f"Error deleting user: {e}")
        finally:
            session.close()

    ### Order Management ###

    def add_order_token(self, order_id: str, username: str, symbol: str, side: str, quantity: float, price: float):
        """Ajoute un nouvel ordre."""
        session = self.SessionLocal()
        try:
            new_exec = TWAPOrder(
                order_id=order_id,
                username=username,
                symbol=symbol,
                side=side,
                quantity=quantity,
                price=price,
                timestamp=datetime.utcnow().isoformat()
            )
            session.add(new_exec)
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Error executing TWAP slice: {e}")
        finally:
            session.close()

    def get_orders(self, username: str = None, order_id: str = None, order_status: str = None):
        """Retourne les ordres filtrés par order_id et/ou order_status."""
        session = self.SessionLocal()
        try:
            query = session.query(OrdersToken)
            if username:
                query = query.filter(OrdersToken.username == username)
            if order_id:
                query = query.filter(OrdersToken.order_id == order_id)
            if order_status:
                query = query.filter(OrdersToken.order_status == order_status)
            orders = query.all()
            results = []
            for o in orders:
                results.append({
                    "order_id": o.order_id,
                    "username": o.username,
                    "symbol": o.symbol,
                    "duration": o.duration,
                    "interval": o.interval,
                    "order_status": o.order_status
                })
            return results
        finally:
            session.close()

    def create_order_token(self, order_req, username: str):
        session = self.SessionLocal()
        try:
            # Vérifie l'unicité de l'order_id
            existing = session.query(OrdersToken).filter(OrdersToken.order_id == order_req.order_id, OrdersToken.username == username).first()
            if existing:
                raise HTTPException(status_code=400, detail="Order ID already exists")
            new_order = OrdersToken(
                order_id=order_req.order_id,
                username=username,
                symbol=order_req.symbol,
                duration=order_req.duration,
                interval=order_req.interval,
                order_status="open"
            )
            session.add(new_order)
            session.commit()
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=500, detail=f"Error creating order: {e}")
        finally:
            session.close()

    def close_order(self, order_id: str):
        """Met à jour le statut de l'ordre en 'closed'."""
        session = self.SessionLocal()
        try:
            order = session.query(OrdersToken).filter(OrdersToken.order_id == order_id).first()
            if order:
                order.order_status = "closed"
                session.commit()
        except Exception as e:
            session.rollback()
            print(f"Error closing order: {e}")
        finally:
            session.close()

    def get_order_details(self, username: str, order_id: str):
        session = self.SessionLocal()
        try:
            order = session.query(OrdersToken).filter(OrdersToken.order_id == order_id, OrdersToken.username == username).first()
            if not order:
                raise HTTPException(status_code=404, detail="Order not found")
            executions = session.query(TWAPOrder).filter(TWAPOrder.order_id == order_id, TWAPOrder.username == username).all()
            exec_details = []
            for exec in executions:
                exec_details.append({
                    "price": exec.price,
                    "quantity": exec.quantity,
                    "timestamp": exec.timestamp
                })
            return {
                "order": {
                    "order_id": order.order_id,
                    "username": order.username,
                    "symbol": order.symbol,
                    "duration": order.duration,
                    "interval": order.interval,
                    "order_status": order.order_status
                },
                "executions": exec_details
            }
        finally:
            session.close()

    def update_order_status(self, order_id: str, new_status: str):
        """Met à jour le statut de l'ordre."""
        session = self.SessionLocal()
        try:
            order = session.query(OrdersToken).filter(OrdersToken.order_id == order_id).first()
            if order:
                order.order_status = new_status
                session.commit()
        except Exception as e:
            session.rollback()
            print(f"Error updating order status: {e}")
        finally:
            session.close()


dbm = DBM()