import atexit
import mysql.connector
from mysql.connector import Error

class db_controller:
    INSERT_MAIL = "INSERT INTO emails (email_uid, email_parent_id, email_id, subject_line, sender_name, sender_address, body_text, sent_on) VALUES (%(email_uid)s, %(email_parent_id)s, %(email_id)s, %(subject_line)s, %(sender_name)s, %(sender_address)s, %(body_text)s, %(sent_on)s);"

    SELECT_MAIL_BY_PARENT = "SELECT email_uid, email_id, email_parent_id, subject_line, sender_name, sender_address, body_text, sent_on FROM emails WHERE email_parent_id = %s;"

    SELECT_WHITELIST = "SELECT whitelist_uid, whitelisted_name, whitelisted_address, whitelisted_on FROM address_whitelist;"

    def __init__(self, mysql_conn_params: dict[str, str]):
        try:
            self.mysql_conn_params = mysql_conn_params
            self.mydb = mysql.connector.connect(**mysql_conn_params)
            self.mycursor = self.mydb.cursor(dictionary=True)
            self.mydb.rollback() #clear any lingering queries on start
        except Error as err:
            print(f"Failed to connect to DB: {err}")
            exit(1)

        atexit.register(self.close)

    def select_whitelist(self):
        try:
            self.mycursor.execute(self.SELECT_WHITELIST)
            results = self.mycursor.fetchall()
            print(f"{len(results)} whitelist entries(s) selected")
            return results
        except Error as err:
            print(f"Failed to fetch whitelist: {err}")
            exit(1)

    def insert_email(self, email: dict):
        try:
            self.mycursor.execute(self.INSERT_MAIL, email)
            self.mydb.commit()
            print("Email inserted")
        except Error as err:
            self.mydb.rollback()
            print(f"Failed to insert email: {err}")

    def insert_emails(self, emails: list[dict]):
        try:
            self.mycursor.executemany(self.INSERT_MAIL, emails)
            self.mydb.commit()
            print(f"{self.mycursor.rowcount} email(s) inserted")
        except Error as err:
            self.mydb.rollback()
            print(f"Failed to insert emails: {err}")

    def select_email_thread(self, parent_message_id: str):
        """Fetches all emails in a thread given the parent Message-ID"""
        try:
            results = []
            current_parent = parent_message_id
            while current_parent:
                self.mycursor.execute(self.SELECT_MAIL_BY_PARENT, (current_parent,))
                row = self.mycursor.fetchone()
                if not row:
                    break
                results.append(row)
                current_parent = row['email_parent_id']
            print(f"{len(results)} email(s) selected in thread")
            return results
        except Error as err:
            print(f"Failed to retrieve thread: {err}")
            return []

    def close(self):
        try:
            self.mydb.rollback()
            if self.mycursor:
                self.mycursor.close()
            if self.mydb:
                self.mydb.close()
            print("Disconnected from MySQL DB")
        except Error as err:
            print(f"Failed to close DB: {err}")