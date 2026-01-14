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


if __name__=="__main__":
    # print(create_company("Google","google.com","15f389ae-373d-4799-b246-a89e6c8cbae5"))
    # print(update_company_info("fe39e6b7-0e76-4dc7-ac26-2fd3e6944e22",status='inactive'))
    # print(delete_company("fe39e6b7-0e76-4dc7-ac26-2fd3e6944e22"))
    # Database_function.Super_admin.company
    print()