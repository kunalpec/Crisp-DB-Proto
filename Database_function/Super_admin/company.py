# some other file at project root
from Database_function.connect_db import get_conn
import secrets
from uuid import UUID
import bcrypt
# Create the Company
def create_company(name, domain, plan_id,username,email,password):
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
        create_company_user(result[0],username,email,password,"admin")
        conn.commit()
        create_company_api_key(result[0])
        conn.commit()
        return result

    except Exception as e:
        conn.rollback()
        raise e

    finally:
        conn.close()
        cur.close()


# view All companies
def view_all_company():
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT
                id,
                name,
                domain,
                status,
                total_tokens_used,
                plan_id,
                created_at
            FROM companies
            ORDER BY created_at DESC;
            """
        )
        return cur.fetchall()

    except Exception as e:
        conn.rollback()
        raise e

    finally:
        cur.close()
        conn.close()

# update companies detail
def update_company_info(company_id, **kwargs):
    if not kwargs:
        raise ValueError("No fields provided to update")

    conn = get_conn()
    cur = conn.cursor()

    try:
        # Build dynamic SET clause
        fields = []
        values = []

        for key, value in kwargs.items():
            fields.append(f"{key} = %s")
            values.append(value)

        values.append(company_id)

        query = f"""
            UPDATE companies
            SET {', '.join(fields)}
            WHERE id = %s
            RETURNING id, name, domain, status, plan_id;
        """

        cur.execute(query, tuple(values))
        result = cur.fetchone()
        conn.commit()
        return result

    except Exception as e:
        conn.rollback()
        raise e

    finally:
        cur.close()
        conn.close()

# deactivate company
def deactive_company(company_id):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            UPDATE companies
            SET status = 'inactive'
            WHERE id = %s
            RETURNING id, name, status;
            """,
            (company_id,)
        )

        result = cur.fetchone()
        conn.commit()
        return result

    except Exception as e:
        conn.rollback()
        raise e

    finally:
        cur.close()
        conn.close()

# delete company  
def delete_company(company_id):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            DELETE FROM companies
            WHERE id = %s
            RETURNING id, name;
            """,
            (company_id,)
        )

        deleted = cur.fetchone()
        conn.commit()

        if deleted:
            return {"message": "company has been deleted"}
        else:
            return {"message": "not deleted"}
        
    except Exception as e:
        conn.rollback()
        raise e

    finally:
        cur.close()
        conn.close()

# make api_key
def create_company_api_key(company_id):
    api_key = "skv-to-"+secrets.token_hex(32)

    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO company_api_keys (company_id, api_key)
            VALUES (%s, %s)
            RETURNING api_key;
            """,
            (company_id, api_key)
        )

        result = cur.fetchone()
        conn.commit()
        return result[0]

    except Exception as e:
        conn.rollback()
        raise e

    finally:
        cur.close()
        conn.close()

# create company user
def create_company_user(company_id: UUID,username:str, email: str, password: str, role: str):
    # hash password
    hashed_password = bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")

    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO company_users (
                company_id,
                email,
                password_hash,
                role,
                username
            )
            VALUES (%s, %s, %s, %s,%s)
            RETURNING id, email, role,username;
            """,
            (company_id, email, hashed_password, role, username)
        )

        result = cur.fetchone()
        conn.commit()
        return result

    except Exception as e:
        conn.rollback()
        raise e

    finally:
        cur.close()
        conn.close()
    
if __name__=="__main__":
    # create_company('abc','IT','f272b9a1-8064-42a3-a0c9-d49e27452368','ABC','testemail@gmail.com','testpassword')
    # print(update_company_info("fe39e6b7-0e76-4dc7-ac26-2fd3e6944e22",status='inactive'))
    # print(delete_company("fe39e6b7-0e76-4dc7-ac26-2fd3e6944e22"))
    # print()
    # print(view_all_company())
    # delete_company('35fa6e25-3caa-4f98-acf1-5035e8d61321')
    # Database_function.Super_admin.company

    create_company('Microsoft','IT','f272b9a1-8064-42a3-a0c9-d49e27452368','Ashutosh','microsoft123@gmail.com','Ashu123')

    
