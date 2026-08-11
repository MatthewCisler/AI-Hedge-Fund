"""Initialize the local database schema and demo records."""

from app.db.init_db import create_database_schema, seed_demo_data
from app.db.session import SessionLocal


def main() -> None:
    create_database_schema()
    with SessionLocal() as db:
        seed_demo_data(db)
    print("Database schema is ready and demo data is seeded.")


if __name__ == "__main__":
    main()
