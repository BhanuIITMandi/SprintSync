import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load from .env if present (for local runs)
load_dotenv()

def seed_database():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("Error: DATABASE_URL not found in environment.")
        return

    print(f"Connecting to database...")
    engine = create_engine(database_url)
    
    # Path to seed.sql
    seed_file_path = os.path.join(os.getcwd(), "db", "seed.sql")
    if not os.path.exists(seed_file_path):
        print(f"Error: Seed file not found at {seed_file_path}")
        return

    with open(seed_file_path, "r") as f:
        sql_script = f.read()

    print("Executing seed.sql...")
    # Filter out empty statements and comments if necessary, 
    # but SQLAlchemy text() can often handle multiple blocks depending on driver.
    # We will split by ';' just to be safe for some Postgres drivers.
    statements = sql_script.split(';')
    
    with engine.connect() as connection:
        trans = connection.begin()
        try:
            for statement in statements:
                if statement.strip():
                    connection.execute(text(statement + ';'))
            trans.commit()
            print("Successfully seeded the database!")
        except Exception as e:
            trans.rollback()
            print(f"Error during seeding: {e}")

if __name__ == "__main__":
    seed_database()
