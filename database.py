import os
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    BigInteger,
    String,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    MetaData,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# Создаём метаданные с указанием схемы
metadata = MetaData(schema=os.getenv("DB_SCHEMA", "public"))

# Базовая модель для всех таблиц
Base = declarative_base(metadata=metadata)


# Таблица пользователей (только для администраторов)
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(String, unique=True, nullable=False)
    username = Column(String, nullable=True)
    is_admin = Column(Boolean, default=False)  # Флаг администратора


# Таблица элементов меню
class MenuItem(Base):
    __tablename__ = "menu_items"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)  # Название продукта
    price = Column(Float, nullable=False)  # Текущая цена
    is_available = Column(Boolean, default=True)  # Доступен ли для заказа


# Таблица заказов
class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(String, nullable=False)
    status = Column(String, default="Принят")
    created_at = Column(DateTime, default=datetime.utcnow)
    desired_time = Column(String)
    items = relationship("OrderItem", back_populates="order")


# Таблица товаров в заказе
class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True)
    order_id = Column(
        Integer, ForeignKey("orders.id"), nullable=False
    )  # Связь с заказом
    menu_item_id = Column(
        Integer, ForeignKey("menu_items.id"), nullable=False
    )  # Связь с товаром
    quantity = Column(Integer, default=1)  # Количество товара
    price_at_time = Column(Float, nullable=False)  # Цена товара на момент заказа
    order = relationship("Order", back_populates="items")  # Связь с заказом
    menu_item = relationship("MenuItem")  # Связь с элементом меню


# Класс для работы с базой данных
class Database:
    def __init__(self):
        # Чтение параметров подключения из .env
        self.db_url = os.getenv("DATABASE_URL", None)  # URL базы данных

        if not self.db_url:
            db_user = os.getenv("DB_USER")
            db_password = os.getenv("DB_PASSWORD")
            db_host = os.getenv("DB_HOST")
            db_port = os.getenv("DB_PORT")
            db_name = os.getenv("DB_NAME")
            # Формируем строку подключения для PostgreSQL
            self.db_url = (
                f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
            )

        self.engine = create_engine(self.db_url)
        self.Session = sessionmaker(bind=self.engine)
        self.create_tables()

    def create_tables(self):
        """Создание таблиц в базе данных"""
        Base.metadata.create_all(self.engine)

    def get_menu_items(self):
        """Получить все элементы меню"""
        session = self.Session()
        items = session.query(MenuItem).filter_by(is_available=True).all()
        result = []
        for item in items:
            result.append(
                {
                    "id": item.id,
                    "name": item.name,
                    "price": item.price,
                    "is_available": item.is_available,
                }
            )
        session.close()
        return result

    def get_menu_item(self, item_id):
        """Получить элемент меню по ID"""
        session = self.Session()
        item = session.query(MenuItem).filter_by(id=item_id).first()
        if item:
            result = {
                "id": item.id,
                "name": item.name,
                "price": item.price,
                "is_available": item.is_available,
            }
        else:
            result = None
        session.close()
        return result

    def get_user_orders(self, telegram_id):
        """Получить заказы пользователя по Telegram ID"""
        session = self.Session()
        orders = (
            session.query(Order).filter_by(telegram_id=str(telegram_id)).all()
        )  # Преобразуем в строку

        result = []
        for order in orders:
            order_data = {
                "id": order.id,
                "status": order.status,
                "created_at": order.created_at,
                "items": [],
            }
            total = 0
            for item in order.items:
                order_data["items"].append(
                    {
                        "name": item.menu_item.name,
                        "quantity": item.quantity,
                        "price": item.price_at_time,
                        "subtotal": item.price_at_time * item.quantity,
                    }
                )
                total += item.price_at_time * item.quantity
            order_data["total"] = total
            result.append(order_data)

        session.close()
        return result

    def is_admin(self, telegram_id):
        """Проверить, является ли пользователь администратором"""
        session = self.Session()
        user = (
            session.query(User)
            .filter_by(telegram_id=str(telegram_id), is_admin=True)
            .first()
        )  # Преобразуем в строку
        session.close()
        return user is not None

    def create_order(self, telegram_id, items):
        """Создать заказ"""
        session = self.Session()
        try:
            order = Order(
                telegram_id=str(telegram_id), status="Принят"
            )  # Преобразуем в строку
            session.add(order)
            session.flush()  # Генерация ID для заказа

            for item in items:
                menu_item = (
                    session.query(MenuItem).filter_by(id=item["menu_item_id"]).first()
                )
                if menu_item and menu_item.is_available:
                    order_item = OrderItem(
                        order_id=order.id,
                        menu_item_id=item["menu_item_id"],
                        quantity=item["quantity"],
                        price_at_time=menu_item.price,  # Берем актуальную цену из меню
                    )
                    session.add(order_item)
                else:
                    session.rollback()
                    return None  # Если товар не найден или недоступен

            session.commit()
            return order.id
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def update_order_status(self, order_id, new_status):
        """Обновить статус заказа"""
        session = self.Session()
        order = session.query(Order).filter_by(id=order_id).first()
        if order:
            order.status = new_status
            session.commit()
        session.close()

    def create_user_if_not_exists(self, telegram_id: int, username: str = None) -> None:
        """Создать пользователя, если он не существует"""
        session = self.Session()
        user = session.query(User).filter_by(telegram_id=str(telegram_id)).first()
        if not user:
            user = User(telegram_id=str(telegram_id), username=username, is_admin=False)
            session.add(user)
            session.commit()
        elif username and user.username != username:
            # Обновляем username если он изменился
            user.username = username
            session.commit()
        session.close()

    def add_menu_item(self, name: str, price: float) -> int:
        """Добавить новый товар в меню"""
        session = self.Session()
        try:
            item = MenuItem(name=name, price=price, is_available=True)
            session.add(item)
            session.commit()
            return item.id
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def update_menu_item(self, item_id: int, **kwargs) -> bool:
        """Обновить информацию о товаре"""
        session = self.Session()
        item = session.query(MenuItem).filter_by(id=item_id).first()
        if item:
            for key, value in kwargs.items():
                if hasattr(item, key):
                    setattr(item, key, value)
            session.commit()
            session.close()
            return True
        session.close()
        return False

    def get_all_orders(self, status=None):
        """Получить все заказы (для админов)"""
        session = self.Session()
        query = session.query(Order)
        if status:
            query = query.filter_by(status=status)
        orders = query.all()

        result = []
        for order in orders:
            # Получаем username пользователя
            user = session.query(User).filter_by(telegram_id=order.telegram_id).first()
            username = user.username if user and user.username else "Нет username"

            order_data = {
                "id": order.id,
                "telegram_id": order.telegram_id,
                "status": order.status,
                "created_at": order.created_at,
                "desired_time": order.desired_time,
                "username": username,
                "items": [],
            }
            total = 0
            for item in order.items:
                order_data["items"].append(
                    {
                        "name": item.menu_item.name,
                        "quantity": item.quantity,
                        "price": item.price_at_time,
                        "subtotal": item.price_at_time * item.quantity,
                    }
                )
                total += item.price_at_time * item.quantity
            order_data["total"] = total
            result.append(order_data)

        session.close()
        return result

    def get_order_details(self, order_id: int):
        """Получить детальную информацию о заказе"""
        session = self.Session()
        order = session.query(Order).filter_by(id=order_id).first()
        if not order:
            session.close()
            return None

        result = {
            "id": order.id,
            "telegram_id": order.telegram_id,
            "status": order.status,
            "created_at": order.created_at,
            "items": [],
        }

        total = 0
        for item in order.items:
            result["items"].append(
                {
                    "name": item.menu_item.name,
                    "quantity": item.quantity,
                    "price": item.price_at_time,
                    "subtotal": item.price_at_time * item.quantity,
                }
            )
            total += item.price_at_time * item.quantity
        result["total"] = total

        session.close()
        return result

    def get_user_by_telegram_id(self, telegram_id: int):
        """Получить пользователя по Telegram ID"""
        session = self.Session()
        user = (
            session.query(User).filter_by(telegram_id=str(telegram_id)).first()
        )  # Преобразуем в строку
        session.close()
        return user

    def process_order(
        self, telegram_id: int, cart_items: list, desired_time: str = None
    ) -> int:
        """Создать заказ из выбранных товаров"""
        session = self.Session()
        try:
            order = Order(
                telegram_id=str(telegram_id),
                status="Принят",
                created_at=datetime.utcnow(),
                desired_time=desired_time,
            )
            session.add(order)
            session.flush()  # Получаем ID заказа

            # Добавляем товары в заказ
            for item in cart_items:
                menu_item = (
                    session.query(MenuItem).filter_by(id=item["item_id"]).first()
                )
                if menu_item and menu_item.is_available:
                    order_item = OrderItem(
                        order_id=order.id,
                        menu_item_id=menu_item.id,
                        quantity=item["quantity"],
                        price_at_time=menu_item.price,
                    )
                    session.add(order_item)

            session.commit()
            return order.id
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def notify_order_status(self, order_id: int) -> dict:
        """Получить информацию для уведомления о статусе заказа"""
        session = self.Session()
        order = session.query(Order).filter_by(id=order_id).first()
        if not order:
            session.close()
            return None

        # Получаем username пользователя
        user = session.query(User).filter_by(telegram_id=order.telegram_id).first()
        username = user.username if user and user.username else "Нет username"

        result = {
            "telegram_id": order.telegram_id,
            "order_id": order.id,
            "status": order.status,
            "desired_time": order.desired_time,
            "username": username,
            "items": [],
        }

        total = 0
        for item in order.items:
            result["items"].append(
                {
                    "name": item.menu_item.name,
                    "quantity": item.quantity,
                    "price": item.price_at_time,
                }
            )
            total += item.price_at_time * item.quantity
        result["total"] = total

        session.close()
        return result

    def get_all_admins(self):
        """Получить список всех администраторов"""
        session = self.Session()
        admins = session.query(User).filter_by(is_admin=True).all()
        result = [admin.telegram_id for admin in admins]
        session.close()
        return result

    def get_orders_stats(self, period=None):
        """Получить статистику заказов за период"""
        session = self.Session()
        query = session.query(Order)

        if period:
            now = datetime.utcnow()
            if period == "day":
                start_date = now - timedelta(days=1)
            elif period == "week":
                start_date = now - timedelta(weeks=1)
            elif period == "month":
                start_date = now - timedelta(days=30)
            query = query.filter(Order.created_at >= start_date)

        orders = query.all()

        stats = {
            "total_orders": len(orders),
            "total_revenue": 0,
            "pending_orders": 0,
            "completed_orders": 0,
            "orders": [],
        }

        for order in orders:
            order_total = sum(
                item.price_at_time * item.quantity for item in order.items
            )
            stats["total_revenue"] += order_total

            if order.status == "Принят":
                stats["pending_orders"] += 1
            elif order.status == "Готов":
                stats["completed_orders"] += 1

            if len(stats["orders"]) < 5:  # Сохраняем только последние 5 заказов
                stats["orders"].append(
                    {
                        "id": order.id,
                        "status": order.status,
                        "total": order_total,
                        "created_at": order.created_at,
                    }
                )

        session.close()
        return stats

    def add_admin(self, admin_telegram_id: int, new_admin_telegram_id: int) -> bool:
        """Добавить нового администратора"""
        session = self.Session()
        try:
            # Проверяем, что добавляющий является админом
            admin = (
                session.query(User)
                .filter_by(
                    telegram_id=str(admin_telegram_id),  # Преобразуем в строку
                    is_admin=True,
                )
                .first()
            )
            if not admin:
                return False

            # Создаем или обновляем пользователя
            user = (
                session.query(User)
                .filter_by(
                    telegram_id=str(new_admin_telegram_id)  # Преобразуем в строку
                )
                .first()
            )
            if not user:
                user = User(
                    telegram_id=str(new_admin_telegram_id),  # Преобразуем в строку
                    is_admin=True,
                )
                session.add(user)
            else:
                user.is_admin = True

            session.commit()
            return True
        except Exception as e:
            session.rollback()
            print(f"Error adding admin: {e}")
            return False
        finally:
            session.close()

    def remove_admin(self, admin_telegram_id: int, target_telegram_id: int) -> bool:
        """Удалить администратора"""
        session = self.Session()
        try:
            # Проверяем, что удаляющий является админом
            admin = (
                session.query(User)
                .filter_by(
                    telegram_id=str(admin_telegram_id),  # Преобразуем в строку
                    is_admin=True,
                )
                .first()
            )
            if not admin:
                return False

            # Находим и обновляем целевого пользователя
            user = (
                session.query(User)
                .filter_by(telegram_id=str(target_telegram_id))  # Преобразуем в строку
                .first()
            )
            if user:
                user.is_admin = False
                session.commit()
                return True
            return False
        finally:
            session.close()

    def delete_menu_item(self, item_id: int) -> bool:
        """Удалить товар из меню"""
        session = self.Session()
        try:
            item = session.query(MenuItem).filter_by(id=item_id).first()
            if item:
                item.is_available = False  # Мягкое удаление
                session.commit()
                return True
            return False
        finally:
            session.close()
