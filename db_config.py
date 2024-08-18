# change your database configuration here
import psycopg2
def create_connection():
    conn = psycopg2.connect(
        host="localhost",
        dbname="hk_drinks",
        user="postgres",
        password="",
        port=5432
    )
    cur = conn.cursor()
    return conn, cur