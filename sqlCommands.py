import mysql.connector
from werkzeug.security import check_password_hash


class MySql:
    def __init__(self):
        """
        Initialize the MySql class and create a connection to the MySQL database.
        """
        self.connection = self.createConnection()
        self.create_tables()
        self.create_triggers()

    @staticmethod
    def createConnection():
        """
        Create a connection to the MySQL database.
        """
        try:
            # Attempt to connect to the database
            cnx = mysql.connector.connect(user='root', password='root', host='127.0.0.1')
            myCursor = cnx.cursor()

            # Create the database if it does not exist
            try:
                myCursor.execute('CREATE DATABASE IF NOT EXISTS projectDB')
            except mysql.connector.errors.DatabaseError:
                pass
            finally:
                # Connect to the database
                cnx = mysql.connector.connect(user='root', password='root', host='127.0.0.1', database='projectDB')
            return cnx
        except mysql.connector.Error as err:
            print("Error creating MySQL connection: {}".format(err))
            return None

    def get_all_games(self):
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = """
                SELECT g.*, gi.games_count
                FROM games g
                JOIN game_inventory gi ON g.game_id = gi.game_id
            """
            cursor.execute(query)
            result = cursor.fetchall()
            cursor.close()
            return result
        except mysql.connector.Error as e:
            print("Error executing query: {}".format(e))
            return None

    def execute_sql_file(self, filename):
        """
        Execute SQL commands from a file.
        """
        try:
            with open(filename, 'r') as file:
                commands = file.read().split(';')
                cursor = self.connection.cursor()

                for command in commands:
                    command = command.strip()
                    if command:
                        try:
                            # Check if table already exists
                            if command.startswith("CREATE TABLE"):
                                table_name = command.split("CREATE TABLE")[1].split("(")[0].strip()
                                cursor.execute("SHOW TABLES LIKE %s", (table_name,))
                                if cursor.fetchone():
                                    print("Table '{}' already exists. Skipping creation.".format(table_name))
                                    continue

                            cursor.execute(command)
                            self.connection.commit()
                        except mysql.connector.Error as err:
                            print("Error executing command: {}".format(err))
                            self.connection.rollback()
        except IOError as e:
            print("Error reading SQL file: {}".format(e))
        finally:
            cursor.close()

    def create_triggers(self):
        """
        Create triggers in the database.
        """
        try:
            cursor = self.connection.cursor()
            # Trigger to update game inventory after order is placed
            cursor.execute("""
                CREATE TRIGGER update_inventory_after_order
                AFTER INSERT ON order_items
                FOR EACH ROW
                BEGIN
                    UPDATE game_inventory
                    SET games_count = games_count - 1
                    WHERE game_id = NEW.game_id;
                END
            """)

            # Trigger to check inventory before placing order
            cursor.execute("""
                CREATE TRIGGER check_inventory_before_order
                BEFORE INSERT ON order_items
                FOR EACH ROW
                BEGIN
                    DECLARE available_count INT;
                    SELECT games_count INTO available_count
                    FROM game_inventory
                    WHERE game_id = NEW.game_id;

                    IF available_count <= 0 THEN
                        SIGNAL SQLSTATE '45000'
                        SET MESSAGE_TEXT = 'Game is out of stock';
                    END IF;
                END
            """)

            self.connection.commit()
            cursor.close()
        except mysql.connector.Error as e:
            print("Error creating triggers:", e)
            self.connection.rollback()

    def create_tables(self):
        """
        Create tables by executing SQL commands from a file.
        """
        self.execute_sql_file('tables.sql')

    def get_games_by_platform(self, platform=None):
        """
        Retrieve games based on the specified platform, including games_count.
        """
        try:
            cursor = self.connection.cursor(dictionary=True)
            if platform:
                query = """
                    SELECT g.*, gi.games_count
                    FROM games g
                    LEFT JOIN game_inventory gi ON g.game_id = gi.game_id
                    WHERE platform = %s
                """
                cursor.execute(query, (platform,))
            else:
                query = """
                    SELECT g.*, gi.games_count
                    FROM games g
                    LEFT JOIN game_inventory gi ON g.game_id = gi.game_id
                """
                cursor.execute(query)
            result = cursor.fetchall()
            cursor.close()
            return result
        except mysql.connector.Error as e:
            print("Error executing query: {}".format(e))
            return None

    def get_game_by_id(self, game_id):
        """
        Retrieve a game by its ID, including games_count.
        """
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = """
                SELECT g.*, gi.games_count
                FROM games g
                LEFT JOIN game_inventory gi ON g.game_id = gi.game_id
                WHERE g.game_id = %s
            """
            cursor.execute(query, (game_id,))
            result = cursor.fetchone()
            cursor.close()
            return result
        except mysql.connector.Error as e:
            print("Error executing query: {}".format(e))
            return None

    def get_user_by_id(self, user_id):
        """
        Retrieve a user by their ID.
        """
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = "SELECT * FROM users WHERE user_id = %s"
            cursor.execute(query, (user_id,))
            result = cursor.fetchone()
            cursor.close()
            return result
        except mysql.connector.Error as e:
            print("Error executing query: {}".format(e))
            return None

    def authenticate_user(self, username, password):
        """
        Authenticate a user based on their username and password.
        """
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = "SELECT * FROM users WHERE username = %s"
            cursor.execute(query, (username,))
            user = cursor.fetchone()
            cursor.close()
            if user and check_password_hash(user['password_hash'], password):
                return user
        except mysql.connector.Error as e:
            print("Error authenticating user: {}".format(e))
        return None

    def get_user_by_username(self, username):
        """
        Retrieve a user by their username.
        """
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = 'SELECT * FROM users WHERE username = %s'
            cursor.execute(query, (username,))
            user = cursor.fetchone()
            cursor.close()
            if user:
                return user
            return False

        except mysql.connector.Error as e:
            print("Error executing query: {}".format(e))
            return None

    def create_user(self, user):
        """
        Create a new user.
        """
        try:
            cursor = self.connection.cursor()
            query = 'INSERT INTO users (username, password_hash, phone, address, email) VALUES(%s, %s, %s, %s, %s)'
            cursor.execute(query, (user[0], user[1], user[2], user[3], user[4],))
            self.connection.commit()

            # Check if user was successfully created
            query = 'SELECT * FROM users WHERE username = %s'
            cursor.execute(query, (user[0],))
            created_user = cursor.fetchone()
            cursor.close()

            if created_user:
                return True
            return False

        except mysql.connector.Error as e:
            print("Error executing query: {}".format(e))
            return False

    def add_game_to_bought(self, game_id, user_id):
        """
        Add a game to the user's bought games.
        """
        try:
            cursor = self.connection.cursor()
            query = 'INSERT INTO user_orders (date_order, user_id) VALUES (CURDATE(), %s)'
            cursor.execute(query, (user_id,))
            order_id = cursor.lastrowid

            query = 'INSERT INTO order_items (order_id, game_id) VALUES (%s, %s)'
            cursor.execute(query, (order_id, game_id))

            self.connection.commit()
            cursor.close()
            return order_id
        except mysql.connector.Error as e:
            print("Error adding game to bought: {}".format(e))
            self.connection.rollback()
            return False

    def get_owned_games(self, user_id):
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = """
                SELECT g.*
                FROM games g
                JOIN (
                    SELECT oi.game_id
                    FROM order_items oi
                    JOIN user_orders uo ON oi.order_id = uo.order_id
                    WHERE uo.user_id = %s
                ) AS user_games ON g.game_id = user_games.game_id
            """

            # Execute the query with user_id as a parameter
            cursor.execute(query, (user_id,))

            # Fetch all rows
            owned_games = cursor.fetchall()

            # Close the cursor and connection
            cursor.close()
            return owned_games
        except mysql.connector.Error as e:
            print(f"Error fetching owned games: {e}")
            return None

    def get_order_details(self, order_id):
        """
        Retrieve details about a specific order including the game and user details.
        """
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = """
                SELECT uo.order_id, uo.date_order, u.user_id, u.username, u.phone, u.address, u.email,
                       g.*, oi.order_id AS oi_order_id
                FROM user_orders uo
                JOIN order_items oi ON uo.order_id = oi.order_id
                JOIN games g ON oi.game_id = g.game_id
                JOIN users u ON uo.user_id = u.user_id
                WHERE uo.order_id = %s
            """
            cursor.execute(query, (order_id,))
            order_details = cursor.fetchall()
            cursor.close()
            return order_details
        except mysql.connector.Error as e:
            print("Error fetching order details:", e)
            return None

    def delete_game(self, game_id):
        try:
            cursor = self.connection.cursor()

            # Retrieve order_ids associated with the game_id
            cursor.execute("SELECT order_id FROM order_items WHERE game_id = %s", (game_id,))
            order_ids = cursor.fetchall()

            # Delete game references from order_items table
            cursor.execute("DELETE FROM order_items WHERE game_id = %s", (game_id,))

            # Delete corresponding order_ids from user_orders table
            for order_id in order_ids:
                cursor.execute("DELETE FROM user_orders WHERE order_id = %s", (order_id[0],))

            # Delete game from game_inventory table
            cursor.execute("DELETE FROM game_inventory WHERE game_id = %s", (game_id,))

            # Finally, delete game from games table
            cursor.execute("DELETE FROM games WHERE game_id = %s", (game_id,))

            # Commit changes
            self.connection.commit()
            cursor.close()
            return True
        except mysql.connector.Error as e:
            print("Error deleting game:", e)
            self.connection.rollback()
            return False

    def add_game_to_list(self, game):
        try:
            cursor = self.connection.cursor()
            query = """INSERT INTO 
            games (game_name, details, developer, publisher, platform, price) 
            VALUES (%s, %s, %s, %s, %s, %s)"""
            cursor.execute(query, (game[0], game[1], game[2], game[3], game[4], game[5],))
            game_id = cursor.lastrowid
            # Insert game count into game_inventory table
            query = """
                        INSERT INTO game_inventory (game_id, games_count)
                        VALUES (%s, %s)
                    """
            cursor.execute(query, (game_id, game[6]))
            self.connection.commit()
            cursor.close()
            return True
        except mysql.connector.Error as e:
            print("Error adding game: ", e)
            self.connection.rollback()
            return False
