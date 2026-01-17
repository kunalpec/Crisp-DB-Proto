from Database_function.connect_db import get_conn

def get_all_plans():
    """
    Retrieve all plans from the database.
    Returns a list of tuples containing plan details.
    """
    conn = get_conn()
    cur = conn.cursor()
    query = """
    SELECT id, name, description, monthly_token_limit, price_monthly,
           max_agents, human_handover, knowledge_base, is_active
    FROM plans;
    """
    cur.execute(query)
    plans = cur.fetchall()
    cur.close()
    conn.close()
    return plans


def create_plan(name, description, monthly_token_limit, price_monthly,
                max_agents=1, human_handover=False, knowledge_base=True):
    """
    Create a new plan.
    Returns the new plan id on success, None on failure (e.g., duplicate name).
    """
    conn = get_conn()
    cur = conn.cursor()
    try:
        query = """
        INSERT INTO plans (name, description, monthly_token_limit, price_monthly,
                           max_agents, human_handover, knowledge_base)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id;
        """
        cur.execute(query, (name, description, monthly_token_limit, price_monthly,
                            max_agents, human_handover, knowledge_base))
        plan_id = cur.fetchone()[0]
        conn.commit()
        return plan_id
    except Exception as e:
        conn.rollback()
        print(f"Error creating plan: {e}")
        return None
    finally:
        cur.close()
        conn.close()


def get_plan_details(plan_id):
    """
    Retrieve details of a specific plan by id.
    Returns a tuple with plan details or None if not found.
    """
    conn = get_conn()
    cur = conn.cursor()
    query = """
    SELECT id, name, description, monthly_token_limit, price_monthly,
           max_agents, human_handover, knowledge_base, is_active, created_at
    FROM plans WHERE id = %s;
    """
    cur.execute(query, (plan_id,))
    plan = cur.fetchone()
    cur.close()
    conn.close()
    return plan


def update_plan(plan_id, **kwargs):
    """
    Update a plan's details. Accepts keyword arguments for fields to update.
    Valid fields: name, description, monthly_token_limit, price_monthly,
                  max_agents, human_handover, knowledge_base, is_active.
    Returns True on success, False on failure.
    """
    allowed_fields = {'name', 'description', 'monthly_token_limit', 'price_monthly',
                      'max_agents', 'human_handover', 'knowledge_base', 'is_active'}
    updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
    if not updates:
        return False

    conn = get_conn()
    cur = conn.cursor()
    try:
        set_clause = ', '.join(f"{k} = %s" for k in updates.keys())
        values = list(updates.values()) + [plan_id]
        query = f"UPDATE plans SET {set_clause} WHERE id = %s;"
        cur.execute(query, values)
        conn.commit()
        return cur.rowcount > 0
    except Exception as e:
        conn.rollback()
        print(f"Error updating plan: {e}")
        return False
    finally:
        cur.close()
        conn.close()


def delete_plan(plan_id):
    """
    Delete a plan by id, only if no company is using it.
    Returns True on success, False if in use or not found.
    """
    conn = get_conn()
    cur = conn.cursor()
    try:
        # Check if any company uses this plan
        check_query = "SELECT COUNT(*) FROM companies WHERE plan_id = %s;"
        cur.execute(check_query, (plan_id,))
        count = cur.fetchone()[0]
        if count > 0:
            return False  # Cannot delete, plan in use

        # Delete the plan
        delete_query = "DELETE FROM plans WHERE id = %s;"
        cur.execute(delete_query, (plan_id,))
        conn.commit()
        return cur.rowcount > 0
    except Exception as e:
        conn.rollback()
        print(f"Error deleting plan: {e}")
        return False
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    # create_plan("paid", "description", 100000, 100,
    #             max_agents=5, human_handover=True, knowledge_base=True)
    # print(get_all_plans())
    # print(get_plan_details('e8abb25e-098a-46b1-97ed-ecd46e687c47'))
    # update_plan('e8abb25e-098a-46b1-97ed-ecd46e687c47', name="paid", price_monthly=1000)
    # print(get_plan_details('29d05dd2-a58d-4f5d-9cdd-8fc676978c68'))
    # print(delete_plan('95615068-9349-4bb0-b922-b3475c27dbfe'))
    print(get_all_plans())

    # Database_function.Super_admin.plan