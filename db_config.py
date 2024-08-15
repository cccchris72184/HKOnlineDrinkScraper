# change your database configuration here
import psycopg2

conn = psycopg2.connect(
        host="localhost",
        dbname="demo_test",
        user="postgres",
        password="",
        port=5432
    )

cur = conn.cursor()