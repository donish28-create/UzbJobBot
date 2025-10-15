import aiosqlite

DB_NAME = "data.db"

async def db_init():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS seekers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            full_name TEXT,
            category TEXT,
            region TEXT,
            district TEXT,
            experience TEXT,
            salary TEXT,
            contact TEXT,
            extra TEXT,
            created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS employers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            category TEXT,
            region TEXT,
            district TEXT,
            salary TEXT,
            contact TEXT,
            extra TEXT,
            created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        await db.commit()
        print("📁 Database initialized successfully.")

