from app import create_app, db
from sqlalchemy import text
from dotenv import load_dotenv

# Force load .env so Flask sees the cloud URL
load_dotenv()

app = create_app()

with app.app_context():
    # 1. Check the connection
    db_url = app.config['SQLALCHEMY_DATABASE_URI']
    print(f"🧐 Flask is connected to: {db_url}")
    
    # Safety Check: Warn if it looks like a local default instead of Render
    if 'localhost' in db_url and 'render' not in db_url:
        print("⚠️  WARNING: You seem to be connected to localhost.")
    
    # 2. Force Drop All Tables
    print("💥 Wiping database using Flask context...")
    db.drop_all()
    
    # 3. Manually kill the migration history table (The root cause of conflicts)
    try:
        with db.engine.connect() as conn:
            conn.execute(text("DROP TABLE IF EXISTS alembic_version CASCADE;"))
            conn.commit()
            print("   ✅ Dropped: alembic_version")
    except Exception as e:
        print(f"   Note: alembic_version might already be gone ({e})")
    
    print("✅ Database is 100% EMPTY. You can now run 'flask db upgrade'.")