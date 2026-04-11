# app/commands.py
import click
from flask.cli import with_appcontext

from app.extensions import db
from app.models.user import User, UserRole
from app.utils.password_utils import hash_password

import os

email = os.environ.get("OWNER_EMAIL", "owner@gym.com")
password = os.environ.get("OWNER_PASSWORD", "securepassword")


@click.command("create-owner")
@with_appcontext
def create_owner():
    existing = db.session.query(User).filter_by(email=email).first()

    if existing:
        print("Owner ya existe")
        return

    owner = User(
        email=email,
        password_hash=hash_password(password),
        first_name='Owner',
        last_name='Gym',
        role=UserRole.OWNER
    )

    db.session.add(owner)
    db.session.commit()
    print("Owner creado")
