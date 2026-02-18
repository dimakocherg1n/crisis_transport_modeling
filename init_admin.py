# init_admin.py
import sys

sys.path.append('.')

from app.database import SessionLocal, engine, Base
from app.models.database_models import User
from app.core.config import settings


def init_first_admin():
    """Инициализация первого администратора"""
    print("👑 Инициализация первого администратора...")

    # Создаем таблицы, если их нет
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        # Проверяем, есть ли уже администраторы
        admin_count = db.query(User).filter(User.role == "admin").count()

        if admin_count > 0:
            print("✅ Администраторы уже существуют")
            admins = db.query(User).filter(User.role == "admin").all()
            for admin in admins:
                print(f"   👤 {admin.email} ({admin.role})")
            return

        # Создаем первого администратора из настроек
        if settings.FIRST_SUPERUSER_EMAIL and settings.FIRST_SUPERUSER_PASSWORD:
            admin = User(
                email=settings.FIRST_SUPERUSER_EMAIL,
                username="admin",
                full_name="Системный администратор",
                hashed_password=get_password_hash(settings.FIRST_SUPERUSER_PASSWORD),
                role="admin",
                is_active=True
            )

            db.add(admin)
            db.commit()
            db.refresh(admin)

            print(f"✅ Создан первый администратор:")
            print(f"   📧 Email: {admin.email}")
            print(f"   👤 Username: {admin.username}")
            print(f"   🔑 Пароль: {settings.FIRST_SUPERUSER_PASSWORD}")
            print("\n⚠️  ВНИМАНИЕ: Смените пароль после первого входа!")

        else:
            print("❌ Не указаны учетные данные администратора в настройках")

    except Exception as e:
        db.rollback()
        print(f"❌ Ошибка при создании администратора: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    init_first_admin()