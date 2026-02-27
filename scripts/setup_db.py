import os
import logging
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("setup_db")

load_dotenv()

def setup_database():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        logger.error("DATABASE_URL not found in environment.")
        exit(1)

    logger.info("Connecting to database for setup...")
    engine = create_engine(database_url)
    
    # 1. Drop existing tables and types
    # Skip complex cleanup for in-memory SQLite (tests)
    if engine.url.drivername == "sqlite":
        logger.info("Skipping cleanup for SQLite.")
    else:
        logger.info("Dropping existing tables and types (CASCADE)...")
        drop_sql = """
        DROP TABLE IF EXISTS tasks CASCADE;
        DROP TABLE IF EXISTS users CASCADE;
        DROP TYPE IF EXISTS task_status CASCADE;
        """
        
        with engine.connect() as conn:
            with conn.begin():
                try:
                    conn.execute(text(drop_sql))
                    logger.info("Cleanup complete.")
                except Exception as e:
                    logger.error(f"Error during cleanup: {e}")
                    exit(1)

    # 2. Run schema.sql
    schema_path = os.path.join("db", "schema.sql")
    logger.info(f"Applying schema from {schema_path}...")
    with open(schema_path, "r") as f:
        schema_sql = f.read()
    
    with engine.connect() as conn:
        with conn.begin():
            try:
                # Execute the entire file content as one block
                conn.execute(text(schema_sql))
                logger.info("Schema applied successfully.")
            except Exception as e:
                logger.error(f"Error applying schema: {e}")
                exit(1)

    # 3. Run seed.sql
    seed_path = os.path.join("db", "seed.sql")
    logger.info(f"Seeding data from {seed_path}...")
    with open(seed_path, "r") as f:
        seed_sql = f.read()
    
    with engine.connect() as conn:
        with conn.begin():
            try:
                conn.execute(text(seed_sql))
                logger.info("Database seeded successfully!")
            except Exception as e:
                logger.error(f"Error seeding database: {e}")
                exit(1)

if __name__ == "__main__":
    setup_database()
