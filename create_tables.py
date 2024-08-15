import psycopg2
from db_config import conn, cur

# create all tables
tables = dict()

tables['dates'] = """
    CREATE TABLE IF NOT EXISTS dates ( 
        scrap_date TIMESTAMP,
        PRIMARY KEY (scrap_date)
    )
"""

tables['product_well'] = """
    CREATE TABLE IF NOT EXISTS products_well (
            brand_name VARCHAR(50),
            product_name VARCHAR(50),
            packing VARCHAR(50),
            country VARCHAR(50),
            PRIMARY KEY(product_name)
    )
"""

tables['fact_well'] = """
    CREATE TABLE IF NOT EXISTS fact_well (
            product_name VARCHAR(50),
            current_price DOUBLE PRECISION,
            unit_price DOUBLE PRECISION,
            stock_status BOOLEAN,
            discount_1 VARCHAR(100),
            discount_2 VARCHAR(100),
            discount_3 VARCHAR(100),
            scrap_date TIMESTAMP,
            PRIMARY KEY(product_name, scrap_date),
            FOREIGN KEY (product_name) REFERENCES products_well (product_name),
            FOREIGN KEY (scrap_date) REFERENCES dates (scrap_date)
    )
"""

tables['product_pns'] = """
    CREATE TABLE IF NOT EXISTS product_pns (
        brand_name VARCHAR(100),
        product_name VARCHAR(100),
        category VARCHAR(100),
        packing VARCHAR(50),
        country VARCHAR(100),
        PRIMARY KEY(product_name)
    )
"""

tables['fact_pns'] = """
    CREATE TABLE IF NOT EXISTS fact_pns (
        brand_name VARCHAR(100),
        product_name VARCHAR(100),
        quantity DOUBLE PRECISION,
        rating DOUBLE PRECISION,
        no_of_reviews INT,
        current_price DOUBLE PRECISION,
        unit_price DOUBLE PRECISION,
        stock_status BOOLEAN,
        promotion1 VARCHAR(100),
        promotion2 VARCHAR(100),
        promotion3 VARCHAR(100),
        packing VARCHAR(50),
        scrap_date TIMESTAMP,
        PRIMARY KEY(product_name, scrap_date),
        FOREIGN KEY (product_name) REFERENCES product_pns (product_name),
        FOREIGN KEY (scrap_date) REFERENCES dates (scrap_date)
    )
"""

tables['products_HKTV'] = """
    CREATE TABLE IF NOT EXISTS products_HKTV (
        product_id VARCHAR PRIMARY KEY,
        product_name VARCHAR,
        brand_name VARCHAR,
        packing VARCHAR,
        country VARCHAR,
        category VARCHAR
    )
"""

tables['store_HKTV'] = """
    CREATE TABLE IF NOT EXISTS store_HKTV (
        store_id VARCHAR PRIMARY KEY,
        store_name VARCHAR(255),
        store_rating FLOAT
    )
"""

tables['fact_HKTV'] = """
    CREATE TABLE IF NOT EXISTS fact_HKTV (
        product_id VARCHAR,
        unit_price FLOAT,
        current_price FLOAT,
        promotion_text TEXT,
        rating FLOAT,
        no_of_reviews INT,
        quantity INT,
        scrap_date TIMESTAMP,
        PRIMARY KEY(product_id, scrap_date),
        FOREIGN KEY(product_id) REFERENCES products_HKTV (product_id),
        FOREIGN KEY(scrap_date) REFERENCES dates (scrap_date)
    )
"""

tables['product_store_HKTV'] = """
    CREATE TABLE IF NOT EXISTS product_store_HKTV (
        product_id VARCHAR,
        store_id VARCHAR,
        PRIMARY KEY (product_id, store_id),
        FOREIGN KEY (product_id) REFERENCES products_HKTV (product_id),
        FOREIGN KEY (store_id) REFERENCES store_HKTV (store_id)
    )
"""

try:
    for table in tables.keys():
        print(f"Creating table {table}")
        cur.execute(tables[table])
    conn.commit()
except (Exception, psycopg2.DatabaseError) as error:
    conn.rollback()
    print(error)




cur.close()
conn.close()


