import psycopg2


class Postgres:
    def __init__(self):
        try:
            self.connection = psycopg2.connect("postgresql://admin:apj0702@localhost:5431/schedulerbot")
            self.cursor = self.connection.cursor()
        except Exception as e:
            print(f'Failed to establish connection: {e}')

    def get_all_records(self):
        try:
            self.cursor.execute("SELECT * FROM jobs")
            records = self.cursor.fetchall()
            return records
        except (Exception, psycopg2.Error) as error:
            print("Error while fetching data from PostgreSQL:", error)

    def insert(self, data):
        try:
            postgres_insert_query = """ INSERT INTO jobs(user_id, job_id, channels, message, start_date, 
                hour, minute, frequency, no_of_times) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
            self.cursor.execute(postgres_insert_query, data)
            self.connection.commit()
        except (Exception, psycopg2.Error) as error:
            print("Error while inserting to PostgreSQL:", error)

    def delete_all_records(self):
        try:
            self.cursor.execute('TRUNCATE jobs')
        except (Exception, psycopg2.Error) as error:
            print("Error while deleting records to PostgreSQL:", error)

    def get_job(self, job_id):
        try:
            query = """SELECT * FROM jobs where job_id=%s"""
            self.cursor.execute(query, (job_id,))
            records = self.cursor.fetchall()
            return records[0]
        except (Exception, psycopg2.Error) as error:
            print("Error while fetching job from PostgreSQL:", error)

    def delete_job(self, job_id):
        try:
            query = """DELETE FROM jobs where job_id=%s"""
            self.cursor.execute(query, (job_id,))
        except (Exception, psycopg2.Error) as error:
            print("Error while deleting data from PostgreSQL:", error)

    def get_user_jobs(self, user_id, scheduled_job_ids):
        try:
            if len(scheduled_job_ids) == 0:
                return ()
            query = """SELECT * FROM jobs where user_id=%s AND job_id IN %s"""
            self.cursor.execute(query, (user_id, scheduled_job_ids))
            records = self.cursor.fetchall()
            return records
        except (Exception, psycopg2.Error) as error:
            print("Error while fetching user jobs from PostgreSQL:", error)


db = Postgres()
