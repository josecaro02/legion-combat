from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""
    pass


# Initialize SQLAlchemy with the custom base
db = SQLAlchemy(model_class=Base)
