from mysql.connector import connect, Error
from mailbot_logging import Logger

class DB:
    def __init__(self, mysql_conn_params):
        self.logger = Logger(self)
        
        self.mysql_conn_params = mysql_conn_params
        self.mydb = None
        self.mycursor = None
    
    def connect_mysql(self):
        try:
            if not self.mydb:
                self.mydb = connect(**self.mysql_conn_params)

            elif not self.mydb.is_connected():
                try:
                    self.mydb.reconnect(attempts=3, delay=5)
                except Error: # Attempt hard reconnect
                    self.mydb = connect(**self.mysql_conn_params)
            
                if self.mydb.in_transaction():
                    self.mydb.rollback()
            
                if self.mycursor:
                    self.mycursor.close()
            
            self.mycursor = self.mydb.cursor(
                prepared=True,
                dictionary=True,
                read_timeout=5, 
                write_timeout=5)
             
        except Error as err:
            self.logger.error("Failed to connect/reconnect to MySQL", err)
            exit(2)
    
    def select_registered_users(self) -> list[]:
        self.connect_mysql()
         
        try:
            self.mycursor.execute("SELECT user_id, email_address, alias_name, registered_on FROM registered_users;")
            rows = self.mycursor.fetchall()
            self.mydb.commit()
            self.logger.info(f"Selected {self.mycursor.rowcount} registered users")
            return rows
        
        except Error as err:
            self.mydb.rollback()
            self.logger.error("Failed to select registered users", err)
            return []
        
    def update_thread_bot_reply_mode(self, thread_id: int, bot_reply_mode: str):
        self.connect_mysql()
        
        try:
            self.mycursor.execute("UPDATE email_thread SET bot_reply_mode = %s WHERE thread_id = %s;", 
                                  (bot_reply_mode, thread_id))
            self.mydb.commit()
            self.logger.info(f"Updated {self.mycursor.rowcount} thread")
            return self.mycursor.rowcount > 0
        
        except Error as err:
            self.mydb.rollback()
            self.logger.error("Failed to update thread", err)
            return False
        
    def update_thread_bot_filter_mode(self, thread_id: int, bot_filter_mode: str):
        self.connect_mysql()
        
        try:
            self.mycursor.execute("UPDATE email_thread SET bot_filter_mode = %s WHERE thread_id = %s;", 
                                  (bot_filter_mode, thread_id))
            self.mydb.commit()
            self.logger.info(f"Updated {self.mycursor.rowcount} thread")
            return self.mycursor.rowcount > 0
        
        except Error as err:
            self.mydb.rollback()
            self.logger.error("Failed to update thread", err)
            return False
        
    def delete_registered_user(self, user_id=None, email_address=None, alias=None) -> False:
        self.connect_mysql()
        
        try:
            if user_id is not None:
                self.mycursor.execute("DELETE FROM registered_users WHERE user_id = %s;", (user_id,))
            elif email_address is not None:
                self.mycursor.execute("DELETE FROM registered_users WHERE email_addres = %s;", (email_address,))
            elif alias is not None:
                self.mycursor.execute("DELETE FROM registered_users WHERE alias = %s;", (alias,))
            
            self.mydb.commit()
            self.logger.info(f"Deleted {self.mycursor.rowcount} registered users")
            return self.mycursor.rowcount > 0
        
        except Error as err:
            self.mydb.rollback()
            self.logger.error("Failed to delete registered user", err)
            return False
        
    def close(self):
        try:
            if self.mycursor:
                self.mycursor.close()
                
        except Error as err:
            self.logger.error("Failed to close cursor", err)
            
        try:
            if self.mydb and self.mydb.is_connected():
                self.mydb.rollback()
                self.mydb.close()
            self.logger.info("Disconnected from MySQL")
                
        except Error as err:
            self.logger.error("Failed to close DB connection", err)