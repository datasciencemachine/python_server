import psycopg2
from psycopg2 import pool
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Global connection pool
_connection_pool = None

def initialize_db_pool():
    """
    Initialize a global connection pool.
    This should be called once when the application starts.
    """
    global _connection_pool
    try:
        _connection_pool = psycopg2.pool.SimpleConnectionPool(
            minconn=1,  # Minimum number of connections in the pool
            maxconn=10,  # Maximum number of connections in the pool
            dbname=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5432')
        )
        print("Database connection pool created successfully")
    except Exception as e:
        print(f"Error creating database connection pool: {e}")
        raise

def get_db_connection():
    """
    Get a connection from the connection pool.
    """
    global _connection_pool
    
    # Check if pool is initialized
    if _connection_pool is None:
        initialize_db_pool()
    
    try:
        # Get a connection from the pool
        connection = _connection_pool.getconn()
        return connection
    except Exception as e:
        print(f"Error getting database connection: {e}")
        raise

def release_db_connection(connection):
    """
    Release the connection back to the pool.
    """
    global _connection_pool
    
    if _connection_pool is not None:
        try:
            _connection_pool.putconn(connection)
        except Exception as e:
            print(f"Error releasing database connection: {e}")

def close_db_pool():
    """
    Close all connections in the pool.
    Call this when your application is shutting down.
    """
    global _connection_pool
    
    if _connection_pool is not None:
        try:
            _connection_pool.closeall()
            print("Database connection pool closed")
        except Exception as e:
            print(f"Error closing database connection pool: {e}")

# Example usage
def example_db_operation():
    connection = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Perform your database operations here
        cursor.execute("SELECT NOW()")
        
        # Don't forget to commit if you're making changes
        connection.commit()
        
    except Exception as e:
        print(f"Database operation error: {e}")
        if connection:
            connection.rollback()
    
    finally:
        # Always release the connection back to the pool
        if connection:
            release_db_connection(connection)

# Initialize the pool when your application starts
initialize_db_pool()