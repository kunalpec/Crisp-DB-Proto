# some other file at project root
from Database_function.connect_db import get_conn

# Create the Company
def create_company(name, domain, plan_id):
    conn = get_conn()
    cur=conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO companies (name, domain, plan_id)
            VALUES (%s, %s, %s)
            RETURNING id, name, status, plan_id;
            """,
            (name, domain, plan_id)
        )
        result = cur.fetchone()
        conn.commit()
        return result

    except Exception as e:
        conn.rollback()
        raise e

    finally:
        conn.close()
        cur.close()

if __name__=="__main__":
    print(create_company("Amazon","amazon.com",1))
