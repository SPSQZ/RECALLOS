from sqlalchemy import text
from database import engine

with engine.begin() as connection:
    columns = connection.execute(
        text("PRAGMA table_info(messages)")
    ).fetchall()

    column_names = [column[1] for column in columns]

    if not columns:
        print("The messages table does not exist.")
    elif "created_at" not in column_names:
        connection.execute(
            text("""
                ALTER TABLE messages
                ADD COLUMN created_at DATETIME
            """)
        )
        print("Added the created_at column.")
    else:
        print("The created_at column already exists.")