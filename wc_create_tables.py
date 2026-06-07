import psycopg2
from wc_sql_queries import create_table_queries, drop_table_queries


def create_database():
    """Connect to default DB, create worldcupdb, return cursor and connection."""
    conn = psycopg2.connect("host=127.0.0.1 dbname=studentdb user=student password=student")
    conn.set_session(autocommit=True)
    cur = conn.cursor()

    cur.execute("DROP DATABASE IF EXISTS worldcupdb")
    cur.execute("CREATE DATABASE worldcupdb WITH ENCODING 'utf8' TEMPLATE template0")
    conn.close()

    conn = psycopg2.connect("host=127.0.0.1 dbname=worldcupdb user=student password=student")
    cur = conn.cursor()
    return cur, conn


def drop_tables(cur, conn):
    """Drop each table (in foreign-key-safe order) using drop_table_queries."""
    for query in drop_table_queries:
        cur.execute(query)
        conn.commit()


def create_tables(cur, conn):
    """Create each table using create_table_queries."""
    for query in create_table_queries:
        cur.execute(query)
        conn.commit()


def main():
    cur, conn = create_database()
    print("Connected to worldcupdb.")
    drop_tables(cur, conn)
    create_tables(cur, conn)
    print("Tables created successfully.")
    conn.close()


if __name__ == "__main__":
    main()
