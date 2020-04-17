"""
Library for interacting with the DB
and other DB related functions
"""

import sys
import socket
from time import sleep
import tormysql
import pymysql.cursors

# Constants
# Change these to the details you chose
SQL_USER = "user"
SQL_PASSWD = "admin"
SQL_DB = "db"
SQL_HOST = "db"


# Creating the DB connection pool
pool = tormysql.ConnectionPool(
    max_connections=20,
    idle_seconds=7200,
    wait_connection_timeout=3,
    host=SQL_HOST,
    user=SQL_USER,
    passwd=SQL_PASSWD,
    db=SQL_DB,
    charset="utf8",
    # To get SQL results as dicts
    cursorclass=pymysql.cursors.DictCursor,
)


async def execute(query, params):
    """
    Execute an sql command with the params given

    Args:
        query: the SQL query to execute
        params: params for the SQL query
    Returns:
        Result of the SQL query
    """
    result = None
    print(f"Executing {query % params}")
    async with await pool.Connection() as conn:
        try:
            async with conn.cursor() as cursor:
                await (cursor.execute(query, params))
                result = cursor.fetchall()
        except Exception as error:
            print(error)
            await conn.rollback()
        else:
            await conn.commit()
    print(f"Result -> {result}")
    return result


async def close_db():
    """
    Closes the DB connection pool

    Args:
        None
    Returns:
        None
    """
    await pool.close()


async def insert(table, params):
    """
    Inserts values into the DB

    Args:
        table: the SQL table to insert to
        params: the insert parameters
    Returns:
        result of the query
    """
    placeholds = "%s, " * (len(params) - 1)
    query = f"insert into {table} values({placeholds}%s);"
    result = await (execute(query, params))
    return result


async def select(table, attrs, conds="", params=()):
    """
    Selects values from a table in the DB

    Args:
        table: the SQL table to query
        params: the query parameters
        conds: any extra conditionals for the query
    Returns:
        None
    """
    query = f"select {attrs} from {table} {conds};"
    result = await (execute(query, params))
    return result


async def gen_new_id():
    """
    Generates a new ID and returns it

    Args:
        none
    Returns:
        the new id
    """
    result = await execute("insert into ids values (default);", ())
    result = await select("ids", "id", "order by id desc limit 1")
    new_id = result[0]["id"]
    query = "delete from ids order by id asc limit 1;"
    await execute(query, ())
    return new_id


def format_time(time):
    """
    Formats time string to {:%d-%m-%y %H:%M:%S}
    which is MySQL/MariaDB compatible

    Args:
        time: a time string
    Returns:
        The formatted time string
    """

    return "{:%d-%m-%y %H:%M:%S}".format(time)


def sync_execute(command):
    """
    Execute an sql command with the params given
    not async, only used for startup

    Args:
        command: the SQL command to execute
    Returns:
        None
    """
    connection = pymysql.connect(
        host=SQL_HOST, user=SQL_USER, password=SQL_PASSWD, db=SQL_DB,
    )
    try:
        with connection.cursor() as cursor:
            cursor.execute(command, ())

        connection.commit()
    finally:
        connection.close()


def wait_for_db():
    """
    Waits for the db to be ready to accept connections

    Args:
        none
    Returns:
        None, exists with code 1 it
        reached max attempts
    """
    attempts = 0
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    while attempts < 10:
        # Attempting to connect
        result = sock.connect_ex(("db", 3306))
        if result == 0:  # Connection successful!
            break
        print("DB not ready for connections yet, sleeping 5s")
        sleep(5)
        attempts += 1

    # Exiting with code 1 if timeouts exceeded
    if attempts == 10:
        print("Failed to connect to DB")
        sys.exit(1)


def initialize():
    """
    Initializes the DB,
    creating the necessary tables
    and the img directory
    if they do not exist

    Args:
        none
    Returns:
        none
    """

    wait_for_db()

    command = """
    create table if not exists ids(
        id bigint unsigned not null auto_increment,
        primary key (id)
    )engine=innodb
    default charset=utf8
    default collate=utf8_unicode_ci;
    """
    sync_execute(command)

    command = """
    create table if not exists posts(
        title varchar(50) not null default '',
        content varchar(800) not null default '',
        board tinyint unsigned not null,
        ext varchar(5) not null default '',
        post_id int unsigned not null,
        created_at datetime not null,
        bumped_at datetime not null,
        bump_count tinyint not null default 0,
        primary key (post_id),
        key title (title),
        key board (board)
    )engine=innodb
    default charset=utf8
    default collate=utf8_unicode_ci;
    """

    sync_execute(command)
    command = """
    create table if not exists comments(
        content varchar(800) not null default '',
        board tinyint unsigned not null,
        parent int unsigned not null,
        ext varchar(5) not null default '',
        com_id int unsigned not null auto_increment,
        created_at datetime not null,
        primary key (com_id),
        key parent (parent)
    )engine=innodb
    default charset=utf8
    default collate=utf8_unicode_ci;
    """
    sync_execute(command)
