import sqlite3


def get_db_connection(file_path):
    con = sqlite3.connect(file_path)
    cur = con.cursor()
    return con, cur
