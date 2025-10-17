import aiosqlite

DB_NAME = "data.db"

# 🔹 Bazani yaratish (agar mavjud bo'lmasa)
async def db_init():
    async with aiosqlite.connect(DB_NAME) as db:
        # Ish qidiruvchilar uchun jadval
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

        # Ish beruvchilar uchun jadval
        await db.execute("""
        CREATE TABLE IF NOT EXISTS employers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            full_name TEXT,
            category TEXT,
            region TEXT,
            district TEXT,
            headcount TEXT,
            salary TEXT,
            contact TEXT,
            extra TEXT,
            created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        await db.commit()
        print("📁 Database initialized successfully.")


# 🔹 O‘xshash e’lonlarni topish (kategoriya va hudud bo‘yicha)
async def get_similar_posts(category: str, region: str):
    async with aiosqlite.connect(DB_NAME) as db:
        # Har ikki jadvaldan o‘xshash postlarni olish
        query_seekers = """
            SELECT full_name, category, region, district, salary, contact
            FROM seekers
            WHERE category = ? AND region = ?
            ORDER BY created DESC
            LIMIT 5
        """
        query_employers = """
            SELECT full_name, category, region, district, salary, contact
            FROM employers
            WHERE category = ? AND region = ?
            ORDER BY created DESC
            LIMIT 5
        """

        seekers_cursor = await db.execute(query_seekers, (category, region))
        seekers = await seekers_cursor.fetchall()

        employers_cursor = await db.execute(query_employers, (category, region))
        employers = await employers_cursor.fetchall()

        rows = seekers + employers

        # Natijani tartibli lug‘at shaklida qaytarish
        result = [
            dict(zip(["full_name", "category", "region", "district", "salary", "contact"], r))
            for r in rows
        ]
        return result
