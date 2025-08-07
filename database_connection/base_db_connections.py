"""
base functions that all other connection files, including classes.
"""

import sqlite3
from flask import g

DATABASE = "database.db"


def make_dicts(cursor, row) -> dict:
    """row factory for database to turn tuples into dicts"""
    return dict((cursor.description[idx][0], value) for idx, value in enumerate(row))


def get_database():
    """returns a database connection and cursor object of connection"""
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = make_dicts

    cursor = g.db.cursor()
    return g.db, cursor


def query_db(query: str, args=(), fetch: bool = True, one: bool = False):
    """
    Completes a database SQL query on Database.db
    Args:
        query (str): the SQL query that the should be used on database.
        args (tuple): tuple of any arguments the query needs in order as they appear in the query.
        fetch (bool): if true function will return value from query, should be false for something like INSERT.
        one (bool): if true function will only fetch first value of query, does nothing if fetch = false.
    """
    db, cursor = get_database()
    cursor.execute(query, args)

    if fetch:
        if one:
            data = cursor.fetchone()
        else:
            data = cursor.fetchall()

        return data

    cursor.close()
    db.commit()