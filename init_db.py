"""
Database initialization script for Freight Broker API
Populates SQLite database with load data from CSV
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db import engine, create_tables
from app.models import Load
from app.database import loads
from sqlalchemy.orm import sessionmaker

def populate_database():
    """Populate database with load data from CSV"""
    
    # Create tables
    create_tables()
    print("✅ Database tables created")
    
    # Create session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Clear existing data
        db.query(Load).delete()
        
        # Add loads from CSV data
        for load_data in loads:
            db_load = Load(
                load_id=load_data["load_id"],
                origin=load_data["origin"],
                destination=load_data["destination"],
                pickup_datetime=load_data["pickup_datetime"],
                delivery_datetime=load_data["delivery_datetime"],
                equipment_type=load_data["equipment_type"],
                loadboard_rate=load_data["loadboard_rate"],
                notes=load_data.get("notes"),
                weight=load_data.get("weight"),
                commodity_type=load_data.get("commodity_type"),
                miles=load_data.get("miles"),
                dimensions=load_data.get("dimensions"),
                num_of_pieces=load_data.get("num_of_pieces")
            )
            db.add(db_load)
        
        db.commit()
        print(f"✅ Successfully populated database with {len(loads)} loads")
        
        # Verify data
        count = db.query(Load).count()
        print(f"📊 Total loads in database: {count}")
        
    except Exception as e:
        print(f"❌ Error populating database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    populate_database()
