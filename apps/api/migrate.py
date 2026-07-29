import sys
import os
from sqlalchemy import text
from core.database import engine

def run():
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE usercontext ADD COLUMN contact JSONB DEFAULT '{}'::jsonb"))
            conn.commit()
            print("Successfully added contact column")
        except Exception as e:
            print(f"Error (maybe already exists): {e}")

if __name__ == "__main__":
    run()
