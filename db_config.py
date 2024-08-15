# change your database configuration here
import psycopg2

conn = psycopg2.connect(
        host="",
        dbname="",
        user="",
        password="",
        port=5432
    )

cur = conn.cursor()
