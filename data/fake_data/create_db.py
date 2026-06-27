import random
import uuid
from datetime import datetime

from faker import Faker
from sqlalchemy import DECIMAL, TIMESTAMP, Column, String, Text, create_engine
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv
import os

# ----------------------------
# Load environment variables
# ----------------------------
load_dotenv()

DATABASE_URL = (
    f"postgresql://{os.getenv('POSTGRES_USER', 'postgres')}:"
    f"{os.getenv('POSTGRES_PASSWORD', 'postgres')}@"
    f"{os.getenv('POSTGRES_HOST', 'localhost')}:"
    f"{os.getenv('POSTGRES_PORT', '5432')}/"
    f"{os.getenv('POSTGRES_DB', 'postal_service')}"
)

# ----------------------------
# Database connection
# ----------------------------
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()
Base = declarative_base()


# ----------------------------
# Models
# ----------------------------

class PackageTracking(Base):
    __tablename__ = "package_tracking"
    __table_args__ = {"extend_existing": True}

    tracking_code = Column(String(50), primary_key=True)
    status = Column(String(50), nullable=False)
    last_update = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)  # ✅ fixed
    location = Column(Text, nullable=False)
    weight_kg = Column(DECIMAL(10, 2))
    shipping_type = Column(String(50), nullable=False)


class User(Base):
    __tablename__ = "users"
    __table_args__ = {"extend_existing": True}

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    phone_number = Column(String(20), nullable=True)
    address = Column(Text, nullable=False)
    city = Column(String(50), nullable=False)
    postal_code = Column(String(20), nullable=False)
    country = Column(String(50), nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)  # ✅ fixed


class UserLLMInteraction(Base):
    __tablename__ = "user_llm_interactions"
    __table_args__ = {"extend_existing": True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    interaction_time = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)  # ✅ fixed


class Order(Base):
    __tablename__ = "orders"
    __table_args__ = {"extend_existing": True}

    order_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sender_name = Column(String(100), nullable=False)
    sender_address = Column(Text, nullable=False)
    sender_city = Column(String(50), nullable=False)
    sender_country = Column(String(50), nullable=False)
    sender_phone = Column(String(20), nullable=False)
    recipient_name = Column(String(100), nullable=False)
    recipient_address = Column(Text, nullable=False)
    recipient_city = Column(String(50), nullable=False)
    recipient_country = Column(String(50), nullable=False)
    recipient_phone = Column(String(20), nullable=False)
    package_weight_kg = Column(DECIMAL(10, 2), nullable=False)
    package_description = Column(Text, nullable=False)
    shipping_type = Column(String(50), nullable=False)
    special_instructions = Column(Text, nullable=True)
    order_status = Column(String(50), default="Pending", nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)  # ✅ fixed


# ----------------------------
# Create all tables at once
# ----------------------------
Base.metadata.create_all(engine)
print("✅ All tables created successfully!")


# ----------------------------
# Seed data
# ----------------------------
faker = Faker()
statuses = ["Processing", "Shipped", "Out for Delivery", "Delivered", "Delayed"]
shipping_types = ["Standard", "Express"]

# --- PackageTracking ---
packages = []
for _ in range(50):
    packages.append(PackageTracking(
        tracking_code=f"PKG{faker.random_int(min=100000, max=999999)}",
        status=random.choice(statuses),
        last_update=faker.date_time_this_year(),
        location=faker.city(),
        weight_kg=round(random.uniform(0.5, 10.0), 2),
        shipping_type=random.choice(shipping_types),
    ))

session.bulk_save_objects(packages)  # ✅ fixed — was adding to empty list before
session.commit()
print("✅ Inserted 50 package records!")

# --- Users ---
users = []
for _ in range(50):
    users.append(User(
        user_id=uuid.uuid4(),
        name=faker.name(),
        email=faker.email(),
        phone_number=faker.phone_number()[:20],
        address=faker.address(),
        city=faker.city(),
        postal_code=faker.postcode(),
        country=faker.country(),
        created_at=faker.date_time_this_decade(),
    ))

session.bulk_save_objects(users)  # ✅ fixed — was adding to empty list before
session.commit()
print("✅ Inserted 50 user records!")

print("\n🎉 Database seeding completed successfully!")