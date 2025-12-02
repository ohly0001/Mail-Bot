import atexit
import mysql.connector
from mysql.connector import Error

class db_controller:
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
            self.mycursor.execute("SELECT whitelist_uid, whitelisted_name, whitelisted_address, whitelisted_on FROM address_whitelist;")
            results = self.mycursor.fetchall()
            print(f"{self.mycursor.rowcount} whitelist entries(s) selected")
            return results
        except Error as err:
            print(f"Failed to fetch whitelist: {err}")
            exit(1)

    def insert_email(self, email: dict, references: list[str] = None, recipients: list[dict] = None):
        try:
            self.mycursor.execute(
                "INSERT INTO emails (email_uid, email_parent_id, email_id, subject_line, sender_name, from_address, body_text, sent_on, token_count) VALUES (%(email_uid)s, %(email_parent_id)s, %(email_id)s, %(subject_line)s, %(sender_name)s, %(from_address)s, %(body_text)s, %(sent_on)s, %(token_count)s);", 
                email
            )
            
            # only add last reference if parent id already in references
            if references:
                self.mycursor.execute("SELECT * FROM email_references WHERE email_parent_id = %s LIMIT 1;", (references[0],))
                if self.mycursor.rowcount == 0:
                    if email['email_parent_id'] not in references:
                        references.append(email["email_parent_id"])
                    self.mycursor.executemany(
                        "INSERT INTO email_references (email_parent_id, email_child_id) VALUES (%s, %s)", 
                        [(references[0], references[i]) for i in range(1, len(references))]
                    )
                else:
                    self.mycursor.execute(
                        "INSERT INTO email_references (email_parent_id, email_child_id) VALUES (%s, %s)", 
                        (references[0], email['email_parent_id'])
                    )
                    
            if recipients:
                self.mycursor.executemany(
                    "INSERT INTO email_recipients (email_id, recipient_address, isCC) VALUES (%s, %s, %s)", 
                    [(email['email_id'], r['address'], r['isCC']) for r in recipients]
                )
            
            self.mydb.commit()
            print("Email inserted")
        except Error as err:
            self.mydb.rollback()
            print(f"Failed to insert email: {err}")

    def insert_emails(self, emails: list[dict], references: list[list[str]], recipients: list[list[str]]):
        pass

    def select_email_thread(self, reference_root_id: str):
        """Fetches the root email and all emails in a thread given the thread reference root"""
        try:
            self.mycursor.execute(
                "SELECT * FROM emails WHERE email_id = %s UNION ALL SELECT e.* FROM emails e INNER JOIN email_references r ON e.email_id = r.email_child_id WHERE r.email_parent_id = %s ORDER BY sent_on ASC;", 
                (reference_root_id, reference_root_id)
            )
            results = self.mycursor.fetchall()
            print(f"{len(results)} email(s) selected in thread")
            return results
        except Error as err:
            print(f"Failed to fetch thread: {err}")
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