import os
import sqlite3
from pathlib import Path
from dotenv import load_dotenv

env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)


class Postgres:
    def __init__(self):
        try:
            # self.connection = psycopg2.connect(
            #     f"postgresql://{os.environ['POSTGRES_USER']}:{os.environ['POSTGRES_PASSWORD']}@{os.environ['POSTGRES_HOST']}:{os.environ['POSTGRES_PORT']}/{os.environ['POSTGRES_DB']}"
            # )
            self.connection = sqlite3.connect("./data/joblist.sqlite", check_same_thread=False)
            self.cursor = self.connection.cursor()
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS jobs(
                    user_id TEXT NOT NULL,
                    job_id TEXT NOT NULL,
                    channels TEXT,
                    message TEXT,
                    start_date TEXT,
                    hour INTEGER,
                    minute INTEGER,
                    frequency TEXT,
                    no_of_times INTEGER,
                    end_date TEXT,
                    PRIMARY KEY(user_id, job_id)
                )
            """)
        except Exception as e:
            print(f'Failed to establish connection: {e}')

    def get_all_records(self):
        try:
            self.cursor.execute("SELECT * FROM jobs")
            records = self.cursor.fetchall()
            return records
        except Exception as e:
            print("Error while fetching data from SQLite:", e)

    def insert(self, data):
        try:
            postgres_insert_query = """ INSERT INTO jobs(user_id, job_id, channels, message, start_date, 
                hour, minute, frequency, no_of_times, end_date) VALUES (?,?,?,?,?,?,?,?,?,?)"""
            self.cursor.execute(postgres_insert_query, data)
            self.connection.commit()
        except Exception as e:
            print("Error while inserting to SQLite:", e)

    def delete_all_records(self):
        try:
            self.cursor.execute('TRUNCATE jobs')
        except Exception as e:
            print("Error while deleting records to SQLite:", e)

    def get_job(self, job_id):
        try:
            query = """SELECT * FROM jobs where job_id=?"""
            self.cursor.execute(query, (job_id,))
            records = self.cursor.fetchall()
            return records[0]
        except Exception as e:
            print("Error while fetching job from SQLite:", e)

    def delete_job(self, job_id):
        try:
            query = """DELETE FROM jobs where job_id=?"""
            self.cursor.execute(query, (job_id,))
            self.connection.commit()
        except Exception as e:
            print("Error while deleting data from SQLite:", e)

    def get_user_jobs(self, user_id, scheduled_job_ids):
        try:
            if len(scheduled_job_ids) == 0:
                return ()
            query = "SELECT * FROM jobs where user_id=? AND job_id IN {}".format(scheduled_job_ids)
            if len(scheduled_job_ids) == 1:
                query = query[:-2] + ")"
            self.cursor.execute(query, (user_id,))
            records = self.cursor.fetchall()
            return records
        except Exception as e:
            print("Error while fetching user jobs from SQLite:", e)


db = Postgres()
