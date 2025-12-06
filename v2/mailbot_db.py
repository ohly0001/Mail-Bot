from mysql.connector import connect, Error
from mailbot_logging import Logger

class DB:
    SELECT_REG_USERS = "SELECT user_id, email_address, alias_name, registered_on FROM registered_users;"
    
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
    
    def select_registered_users(self):
        self.connect_mysql()
        
        try:
            self.mycursor.execute(self.SELECT_REG_USERS)
            rows = self.mycursor.fetchall()
            self.logger.info(f"Selected {self.mycursor.rowcount} registered users")
            return rows
        
        except Error as err:
            self.logger.error("Failed to select registered users", err)
            return []
        
    def close(self):
        try:
            if self.mycursor:
                self.mycursor.close()
                
        except Error as err:
            self.logger.error("Failed to close cursor", err)
            
        try:
            if self.mydb and self.mydb.is_connected():
                self.mydb.close()
            self.logger.info("Disconnected from MySQL")
                
        except Error as err:
            self.logger.error("Failed to close DB connection", err)