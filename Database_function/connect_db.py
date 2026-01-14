import psycopg
import os
from dotenv import load_dotenv

# make the connection to .env
load_dotenv()

# Connect to ChatBotdb
def get_conn():
    """
    Return a PostgreSQL connection to ChatBotdb
    """
    conn = psycopg.connect(
        host=os.getenv("POSTSQL_HOST"),        
        dbname="Chatbot_saas",
        user=os.getenv("POSTSQL_USER"),        
        password=os.getenv("POSTSQL_PASSWORD"),
        port=os.getenv("POSTSQL_PORT") 
    )
    return conn


# Test query
if __name__=="__main__":
  cur = get_conn().cursor()
  cur.execute("SELECT 1;")
  print(cur.fetchone())  # Output: (1,)
