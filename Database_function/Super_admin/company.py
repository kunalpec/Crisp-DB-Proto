from Database_function.connect_db import get_conn
import secrets
import bcrypt
from uuid import UUID
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta


# =========================================================
# INTERNAL: CALCULATE END DATE
# =========================================================
def _calculate_end_date(start_date, duration_value, duration_unit):
    if duration_unit == "month":
        return start_date + relativedelta(months=duration_value)
    elif duration_unit == "year":
        return start_date + relativedelta(years=duration_value)
    else:
        raise ValueError("duration_unit must be 'month' or 'year'")

# =========================================================
# CREATE COMPANY (SUPER ADMIN ONLY)
# =========================================================
def create_company(name, domain, plan_id, username, email, password):
    """
    Atomically creates:
    - company
    - company admin
    - company plan
    - API key
    """
    conn = get_conn()
    cur = conn.cursor()

    try:
        # 1️⃣ Create company
        cur.execute(
            """
            INSERT INTO companies (name, domain, plan_id)
            VALUES (%s, %s, %s)
            RETURNING id, status;
            """,
            (name, domain, plan_id)
        )
        # cur.execute(
        #     """
        #     INSERT INTO companies (name, domain)
        #     VALUES (%s, %s)
        #     RETURNING id, status;
        #     """,
        #     (name, domain)
        # )
        company_id, status = cur.fetchone()
        # 2️⃣ Fetch plan details (ONLY active plans)
        cur.execute(
            """
            SELECT monthly_token_limit, duration_value, duration_unit
            FROM plans
            WHERE id = %s AND is_active = true;
            """,
            (plan_id,)
        )
        plan = cur.fetchone()
        if not plan:
            raise ValueError("Invalid or inactive plan")

        token_limit, duration_value, duration_unit = plan

        # 3️⃣ Calculate dates (UTC SAFE)
        start_date = datetime.now(timezone.utc)
        end_date = _calculate_end_date(start_date, duration_value, duration_unit)

        # 4️⃣ Assign plan
        cur.execute(
            """
            INSERT INTO company_plans (
                company_id,
                plan_id,
                start_date,
                end_date,
                token_limit
            )
            VALUES (%s, %s, %s, %s, %s);
            """,
            (company_id, plan_id, start_date, end_date, token_limit)
        )

        # 5️⃣ Create admin user
        hashed_password = bcrypt.hashpw(
            password.encode("utf-8"),
            bcrypt.gensalt()
        ).decode("utf-8")

        cur.execute(
            """
            INSERT INTO company_users (
                company_id, username, email, password_hash, role
            )
            VALUES (%s, %s, %s, %s, 'admin');
            """,
            (company_id, username, email, hashed_password)
        )

        # 6️⃣ Create API key
        api_key = "skv-to-" + secrets.token_hex(32)
        cur.execute(
            """
            INSERT INTO company_api_keys (company_id, api_key)
            VALUES (%s, %s);
            """,
            (company_id, api_key)
        )

        # ✅ SINGLE COMMIT
        conn.commit()

        return {
            "company_id": company_id,
            "status": status,
            "api_key": api_key,
            "plan_expires_at": end_date
        }

    except Exception as e:
        conn.rollback()
        raise RuntimeError(f"Create company failed: {e}")

    finally:
        cur.close()
        conn.close()

# =========================================================
# VIEW ALL COMPANIES
# =========================================================
def view_all_company():
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT
                c.id,
                c.name,
                c.domain,
                c.status,
                cp.plan_id,
                cp.status AS plan_status,
                cp.end_date,
                c.created_at
            FROM companies c
            LEFT JOIN company_plans cp
                ON c.id = cp.company_id
               AND cp.status = 'active'
            ORDER BY c.created_at DESC;
            """
        )
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()

# =========================================================
# UPDATE COMPANY INFO
# =========================================================
def update_company_info(company_id, **kwargs):
    allowed_fields = {"name", "domain", "status"}
    updates = {k: v for k, v in kwargs.items() if k in allowed_fields}

    if not updates:
        raise ValueError("No valid fields to update")

    conn = get_conn()
    cur = conn.cursor()
    try:
        set_clause = ", ".join(f"{k} = %s" for k in updates)
        values = list(updates.values()) + [company_id]

        cur.execute(
            f"""
            UPDATE companies
            SET {set_clause}
            WHERE id = %s
            RETURNING id, name, domain, status;
            """,
            values
        )
        conn.commit()
        return cur.fetchone()
    except Exception as e:
        conn.rollback()
        raise RuntimeError(f"Update failed: {e}")
    finally:
        cur.close()
        conn.close()

# =========================================================
# ACTIVATE / DEACTIVATE / DELETE
# =========================================================
def _set_company_status(company_id, status):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            UPDATE companies
            SET status = %s
            WHERE id = %s
            RETURNING id, name, status;
            """,
            (status, company_id)
        )
        conn.commit()
        return cur.fetchone()
    finally:
        cur.close()
        conn.close()

def deactivate_company(company_id):
    return _set_company_status(company_id, "inactive")

def activate_company(company_id):
    return _set_company_status(company_id, "active")

def delete_company(company_id):
    return _set_company_status(company_id, "blocked")


# =========================================================
# CHANGE COMPANY PLANS
# =========================================================
def change_company_plan(company_id, new_plan_id):
    """
    Upgrade / downgrade company plan.
    Automatically expires current plan and assigns new one.
    """
    conn = get_conn()
    cur = conn.cursor()

    try:
        # 1️⃣ Get active plan
        cur.execute(
            """
            SELECT id
            FROM company_plans
            WHERE company_id = %s AND status = 'active';
            """,
            (company_id,)
        )
        active_plan = cur.fetchone()
        if not active_plan:
            raise ValueError("Company has no active plan")

        active_company_plan_id = active_plan[0]

        # 2️⃣ Expire current plan
        cur.execute(
            """
            UPDATE company_plans
            SET status = 'expired',
                end_date = now()
            WHERE id = %s;
            """,
            (active_company_plan_id,)
        )

        # 3️⃣ Fetch new plan details
        cur.execute(
            """
            SELECT token_limit, duration_value, duration_unit
            FROM plans
            WHERE id = %s AND is_active = true;
            """,
            (new_plan_id,)
        )
        plan = cur.fetchone()
        if not plan:
            raise ValueError("Invalid or inactive new plan")

        token_limit, duration_value, duration_unit = plan

        start_date = datetime.now(timezone.utc)
        end_date = _calculate_end_date(start_date, duration_value, duration_unit)

        # 4️⃣ Assign new plan
        cur.execute(
            """
            INSERT INTO company_plans (
                company_id,
                plan_id,
                start_date,
                end_date,
                token_limit
            )
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id;
            """,
            (company_id, new_plan_id, start_date, end_date, token_limit)
        )

        new_company_plan_id = cur.fetchone()[0]

        conn.commit()

        return {
            "old_company_plan_id": active_company_plan_id,
            "new_company_plan_id": new_company_plan_id,
            "start_date": start_date,
            "end_date": end_date
        }

    except Exception as e:
        conn.rollback()
        raise RuntimeError(f"Change plan failed: {e}")

    finally:
        cur.close()
        conn.close()

# =========================================================
# RENEW COMPANY PLANS
# =========================================================
def renew_company_plan(company_id, plan_id):
    """
    Renew a plan for a company AFTER expiry.
    Company must NOT have an active plan.
    """
    conn = get_conn()
    cur = conn.cursor()

    try:
        # 1️⃣ Ensure NO active plan exists
        cur.execute(
            """
            SELECT 1
            FROM company_plans
            WHERE company_id = %s AND status = 'active';
            """,
            (company_id,)
        )
        if cur.fetchone():
            raise ValueError(
                "Company already has an active plan. Use change_company_plan()."
            )

        # 2️⃣ Fetch plan details
        cur.execute(
            """
            SELECT token_limit, duration_value, duration_unit
            FROM plans
            WHERE id = %s AND is_active = true;
            """,
            (plan_id,)
        )
        plan = cur.fetchone()
        if not plan:
            raise ValueError("Invalid or inactive plan")

        token_limit, duration_value, duration_unit = plan

        # 3️⃣ Calculate new dates (UTC safe)
        start_date = datetime.now(timezone.utc)
        end_date = _calculate_end_date(start_date, duration_value, duration_unit)

        # 4️⃣ Insert NEW subscription row
        cur.execute(
            """
            INSERT INTO company_plans (
                company_id,
                plan_id,
                start_date,
                end_date,
                token_limit,
                tokens_used,
                status
            )
            VALUES (%s, %s, %s, %s, %s, 0, 'active')
            RETURNING id;
            """,
            (company_id, plan_id, start_date, end_date, token_limit)
        )

        company_plan_id = cur.fetchone()[0]
        conn.commit()

        return {
            "company_plan_id": company_plan_id,
            "start_date": start_date,
            "end_date": end_date,
            "message": "Plan renewed successfully"
        }

    except Exception as e:
        conn.rollback()
        raise RuntimeError(f"Renew plan failed: {e}")

    finally:
        cur.close()
        conn.close()


if __name__=="__main__":
    # print(create_company("Google","google.com","15f389ae-373d-4799-b246-a89e6c8cbae5"))
    # print(update_company_info("fe39e6b7-0e76-4dc7-ac26-2fd3e6944e22",status='inactive'))
    # print(delete_company("fe39e6b7-0e76-4dc7-ac26-2fd3e6944e22"))
    create_company(
        name="CampusBot",
        domain="campusbot.in",
        plan_id="39685b88-4aae-437f-9b15-1f85450d1e88",
        username="admin",
        email="admin@campusbot.in",
        password="campus123"
    )
    create_company(
        name="ShopAssist AI",
        domain="shopassist.ai",
        plan_id="81a66470-02be-472a-8b50-286606b0f65e",
        username="founder",
        email="founder@shopassist.ai",
        password="shop123"
    )
    create_company(
        name="HealthCare Support AI",
        domain="healthsupport.com",
        plan_id="601d80d5-5090-45df-b26a-e13dcd3942f4",
        username="superadmin",
        email="admin@healthsupport.com",
        password="health123"
    )
    create_company(
        name="Gov eSeva AI",
        domain="eseva.gov.in",
        plan_id="ededb913-59af-4c7d-88f2-c01a160c286e",
        username="root",
        email="root@eseva.gov.in",
        password="govsecure"
    )
    print('created companies')
    # Database_function.Super_admin.company