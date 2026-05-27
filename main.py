from fastapi import FastAPI, HTTPException
import mysql.connector
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI()

# ======================================================
# CORS POLICY
# ======================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# -------------------- DB Connection --------------------
conn = mysql.connector.connect(
    host=os.getenv("db_host"),
    user=os.getenv("db_user"),
    password=os.getenv("db_password"),
    database=os.getenv("db_name"),
    port=int(os.getenv("db_port"))
)

cursor = conn.cursor(dictionary=True)

# -------------------- Create Table --------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS expenses (
    expense_id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200),
    amount FLOAT,
    category VARCHAR(100),
    payment_method VARCHAR(100),
    expense_date DATE,
    description TEXT
)
""")

conn.commit()


# -------------------- Home --------------------
@app.get("/")
def home():
    return {
        "message": "API Running Successfully"
    }


# -------------------- Add Expense --------------------
@app.post("/add_expense")
def add_expense(payload: dict):

    query = """
    INSERT INTO expenses
    (title, amount, category, payment_method, expense_date, description)
    VALUES (%s, %s, %s, %s, %s, %s)
    """

    values = (
        payload["title"],
        payload["amount"],
        payload["category"],
        payload["payment_method"],
        payload["expense_date"],
        payload["description"]
    )

    cursor.execute(query, values)
    conn.commit()

    return {
        "message": "Expense Added Successfully"
    }


# -------------------- Get All Expenses --------------------
@app.get("/get_expenses")
def get_expenses():

    query = """
    SELECT *
    FROM expenses
    ORDER BY expense_id DESC
    """

    cursor.execute(query)
    data = cursor.fetchall()

    return {
        "expenses": data
    }


# -------------------- Get Single Expense --------------------
@app.get("/get_single_expense/{expense_id}")
def get_single_expense(expense_id: int):

    query = """
    SELECT *
    FROM expenses
    WHERE expense_id = %s
    """

    cursor.execute(query, (expense_id,))
    data = cursor.fetchone()

    if not data:
        raise HTTPException(status_code=404, detail="Expense Not Found")

    return {
        "expense": data
    }


# -------------------- Update Expense --------------------
@app.put("/update_expense/{expense_id}")
def update_expense(expense_id: int, payload: dict):

    check_query = "SELECT * FROM expenses WHERE expense_id=%s"
    cursor.execute(check_query, (expense_id,))
    existing = cursor.fetchone()

    if not existing:
        raise HTTPException(status_code=404, detail="Expense Not Found")

    query = """
    UPDATE expenses
    SET
        title=%s,
        amount=%s,
        category=%s,
        payment_method=%s,
        expense_date=%s,
        description=%s
    WHERE expense_id=%s
    """

    values = (
        payload["title"],
        payload["amount"],
        payload["category"],
        payload["payment_method"],
        payload["expense_date"],
        payload["description"],
        expense_id
    )

    cursor.execute(query, values)
    conn.commit()

    return {
        "message": "Expense Updated Successfully"
    }


# -------------------- Delete Expense --------------------
@app.delete("/delete_expense/{expense_id}")
def delete_expense(expense_id: int):

    check_query = "SELECT * FROM expenses WHERE expense_id=%s"
    cursor.execute(check_query, (expense_id,))
    existing = cursor.fetchone()

    if not existing:
        raise HTTPException(status_code=404, detail="Expense Not Found")

    query = """
    DELETE FROM expenses
    WHERE expense_id=%s
    """

    cursor.execute(query, (expense_id,))
    conn.commit()

    return {
        "message": "Expense Deleted Successfully"
    }


# -------------------- Expense Summary --------------------
@app.get("/expense_summary")
def expense_summary():

    query = """
    SELECT
        category,
        SUM(amount) AS total_amount
    FROM expenses
    GROUP BY category
    """

    cursor.execute(query)
    data = cursor.fetchall()

    return {
        "summary": data
    }