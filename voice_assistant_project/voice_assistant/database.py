import sqlite3
import datetime

def create_connection(db_file):
    #create a connection to the SQLite database
    conn = None
    try:
        conn = sqlite3.connect('db_file', check_same_thread=False)
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

    
def retrieve_database_history(conn, minutes=5, recall=False):
    current_time = datetime.datetime.now()
    time_threshold = current_time - datetime.timedelta(minutes=minutes)

    try:
        c = conn.cursor()
        if recall:
            # Return ALL conversation history if recall is True
            print("full conversation history trigger")
            c.execute("SELECT * FROM conversation_history")
        else:
            # Return default of 5 minutes history
            print("5min convo history")
            c.execute("SELECT * FROM conversation_history WHERE timestamp >= ?", (time_threshold.strftime("%Y-%m-%d %H:%M:%S.%f"),))

        rows = c.fetchall()
        return [(datetime.datetime.strptime(row[1], "%Y-%m-%d %H:%M:%S.%f"), row[2], row[3]) for row in rows] if rows else []  # Return an empty list if rows are empty

    except sqlite3.Error as e:
        print(e)
        return []

def retrieve_memory_history(conversation_history, minutes=5):
    current_time = datetime.datetime.now()
    time_threshold = current_time - datetime.timedelta(minutes=minutes)
    memory_history = [item for item in conversation_history if item[0] >= time_threshold]
    return memory_history

def reset_chat():
    print("Resetting memory")
    global memory_history
    memory_history = []