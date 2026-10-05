import sqlite3

DB_NAME = "garage_business_planning.db"

def get_connection():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Categories Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    """)
    
    # Pre-populate default Car Garage categories if empty
    cursor.execute("SELECT COUNT(*) FROM categories")
    if cursor.fetchone()[0] == 0:
        default_categories = [
            "Lifts & Hoists",
            "Diagnostic Tools",
            "Wheel & Tire Service",
            "Air Compressors & Tools",
            "Engine & Transmission Service",
            "Body & Paint Equipment",
            "AC Service Equipment",
            "Hand & Power Tools",
            "Safety & Fluid Handling"
        ]
        for cat in default_categories:
            cursor.execute("INSERT OR IGNORE INTO categories (name) VALUES (?)", (cat,))

    # Suppliers Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS suppliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    """)

    # Equipments Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS equipments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            si_no INTEGER UNIQUE NOT NULL,
            name TEXT NOT NULL,
            requirement_type TEXT NOT NULL,
            category TEXT NOT NULL,
            qty INTEGER DEFAULT 1
        )
    """)

    # Supplier Prices Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS supplier_prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            equipment_id INTEGER NOT NULL,
            supplier_id INTEGER NOT NULL,
            price REAL NOT NULL,
            UNIQUE(equipment_id, supplier_id),
            FOREIGN KEY (equipment_id) REFERENCES equipments(id) ON DELETE CASCADE,
            FOREIGN KEY (supplier_id) REFERENCES suppliers(id) ON DELETE CASCADE
        )
    """)

    # Migration check for qty column
    cursor.execute("PRAGMA table_info(equipments)")
    columns = [col[1] for col in cursor.fetchall()]
    if "qty" not in columns:
        cursor.execute("ALTER TABLE equipments ADD COLUMN qty INTEGER DEFAULT 1")
    
    
    # Add this inside database/schema.py within the init_db() function

    # Parts Catalog Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS parts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        part_number TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        stock_qty INTEGER DEFAULT 0,
        min_stock_level INTEGER DEFAULT 2
        )
    """)

    # Car Compatibility / Fitment Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS part_fitments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        part_id INTEGER NOT NULL,
        car_make TEXT NOT NULL,
        car_model TEXT NOT NULL,
        year_range TEXT NOT NULL,
        FOREIGN KEY (part_id) REFERENCES parts(id) ON DELETE CASCADE
        )
    """)

    # Part Brands & Supplier Pricing Guide Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS part_supplier_sources (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        part_id INTEGER NOT NULL,
        brand_name TEXT NOT NULL,
        supplier_id INTEGER NOT NULL,
        unit_cost REAL NOT NULL,
        lead_time_days INTEGER DEFAULT 1,
        is_preferred INTEGER DEFAULT 0,
        FOREIGN KEY (part_id) REFERENCES parts(id) ON DELETE CASCADE,
        FOREIGN KEY (supplier_id) REFERENCES suppliers(id) ON DELETE CASCADE
    )
    """)


    conn.commit()
    conn.close()