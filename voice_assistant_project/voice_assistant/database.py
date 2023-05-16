import sqlite3
import datetime

def create_connection(db_file):
    #create a connection to the SQLite database
    conn = None
    try:
        conn = sqlite3.connect(db_file, check_same_thread=False)
        print(f'Successfully connected to SQLite version {sqlite3.version}')
    except sqlite3.Error as e:
        print(e)
    return conn

def create_table(conn):
    #create a table to store conversation history
    try:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS conversation_history
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    speaker TEXT NOT NULL,
                    text TEXT NOT NULL);''')
        conn.commit()
        print('successfully created conversation history table.')
    except sqlite3.Error as e:
        print(e)

def initialize_database():
    conn = create_connection()
    create_table(conn)
    return conn

def insert_message(conn, timestamp, speaker, text):
    #insert a message into the conversation history table
    try:
        c = conn.cursor()
        c.execute("INSERT INTO conversation_history (timestamp, speaker, text) VALUES (?, ?, ?)", (timestamp, speaker, text))
        conn.commit()
    except sqlite3.Error as e:
        print(e)

def retrieve_database_history(conn, minutes=5, recall=False, reset_timestamp=None):
    current_time = datetime.datetime.now()
    time_threshold = current_time - datetime.timedelta(minutes=minutes)

    # Check if a reset is requested
    if reset_timestamp is not None:
        # If a reset timestamp is provided, only retrieve messages that are newer than the reset timestamp
        time_threshold = max(time_threshold, reset_timestamp)

    try:
        c = conn.cursor()
        if recall:
            c.execute("SELECT * FROM conversation_history")
        else:
            c.execute("SELECT * FROM conversation_history WHERE timestamp >= ?", (time_threshold.strftime("%Y-%m-%d %H:%M:%S.%f"),))

        rows = c.fetchall()
        return [(datetime.datetime.strptime(row[1], "%Y-%m-%d %H:%M:%S.%f"), row[2], row[3]) for row in rows] if rows else []

    except sqlite3.Error as e:
        print(e)
        return []

