"""Opt-in real PostgreSQL locking test; SQLite cannot validate row locks."""

import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models import Community, Item, RentalRequest, User
from app.schemas.rental import RentalCreate
from app.services.rental import (
    RentalError,
    create_rental,
    today_utc,
    transition_rental,
)


@pytest.mark.skipif(
    not os.getenv("TEST_POSTGRES_URL"), reason="TEST_POSTGRES_URL is not configured"
)
def test_simultaneous_accepts_only_reserve_once() -> None:
    # Only a fresh, test-owned schema is created and removed, never existing tables.
    schema = "rental_test_" + uuid.uuid4().hex
    url = os.environ["TEST_POSTGRES_URL"]
    admin = create_engine(url)
    with admin.begin() as connection:
        connection.exec_driver_sql(f'CREATE SCHEMA "{schema}"')
    engine = create_engine(
        url, connect_args={"options": f"-csearch_path={schema} -clock_timeout=10000"}
    )
    try:
        Base.metadata.create_all(engine)
        with Session(engine, expire_on_commit=False) as db:
            community = Community(
                name="Lock test", type="college", city="Delhi", invite_code="LOCKTEST"
            )
            db.add(community)
            db.flush()
            users = [
                User(
                    full_name=str(i),
                    email=f"{i}@test.example",
                    password_hash="unused",
                    community_id=community.id,
                )
                for i in range(3)
            ]
            db.add_all(users)
            db.flush()
            item = Item(
                owner_id=users[0].id,
                community_id=community.id,
                title="Drill",
                description="Test",
                category="Tools",
                rental_price_per_day=10,
                security_deposit=20,
                replacement_value=100,
                availability=True,
            )
            db.add(item)
            db.commit()
            data = RentalCreate(
                item_id=item.id,
                start_date=today_utc() + timedelta(days=1),
                end_date=today_utc() + timedelta(days=3),
            )
            ids = [create_rental(db, user, community.id, data).id for user in users[1:]]
            owner_id, community_id = users[0].id, community.id
        barrier = Barrier(2)

        def accept(rental_id: uuid.UUID) -> int:
            with Session(engine) as db:
                owner = db.get(User, owner_id)
                assert owner is not None
                barrier.wait(timeout=10)
                try:
                    transition_rental(db, owner, community_id, rental_id, "accept")
                    return 200
                except RentalError as exc:
                    db.rollback()
                    return exc.status_code

        with ThreadPoolExecutor(max_workers=2) as pool:
            assert sorted(pool.map(accept, ids)) == [200, 409]
        with Session(engine) as db:
            assert sorted(db.scalars(select(RentalRequest.status)).all()) == [
                "ACCEPTED",
                "PENDING",
            ]
    finally:
        engine.dispose()
        with admin.begin() as connection:
            connection.exec_driver_sql(f'DROP SCHEMA "{schema}" CASCADE')
        admin.dispose()
