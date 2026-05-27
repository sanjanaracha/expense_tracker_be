from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import mysql.connector
from fastapi.responses import StreamingResponse
import pandas as pd
import io

app = FastAPI()

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root",
    database="expense_tracker"
)

cursor = db.cursor(dictionary=True)

class Expense(BaseModel):
    title: str
    amount: float
    category: str

@app.get("/")
def home():
    return {"message": "Expense Tracker Backend Running"}

@app.post("/expenses")
def add_expense(expense: Expense):
    query = """
    INSERT INTO expenses (title, amount, category)
    VALUES (%s, %s, %s)
    """
    cursor.execute(query, (expense.title, expense.amount, expense.category))
    db.commit()
    return {"message": "Expense added successfully"}

@app.get("/expenses")
def get_expenses():
    cursor.execute("SELECT * FROM expenses")
    return cursor.fetchall()

@app.get("/expenses/{expense_id}")
def get_single_expense(expense_id: int):
    cursor.execute("SELECT * FROM expenses WHERE expense_id=%s", (expense_id,))
    data = cursor.fetchone()

    if not data:
        raise HTTPException(status_code=404, detail="Expense not found")

    return data

@app.put("/expenses/{expense_id}")
def update_expense(expense_id: int, expense: Expense):
    query = """
    UPDATE expenses
    SET title=%s, amount=%s, category=%s
    WHERE expense_id=%s
    """
    cursor.execute(query, (expense.title, expense.amount, expense.category, expense_id))
    db.commit()

    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Expense not found")

    return {"message": "Expense updated successfully"}

@app.delete("/expenses/{expense_id}")
def delete_expense(expense_id: int):
    cursor.execute("DELETE FROM expenses WHERE expense_id=%s", (expense_id,))
    db.commit()

    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Expense not found")

    return {"message": "Expense deleted successfully"}

@app.get("/search")
def search_expense(category: str):
    cursor.execute("SELECT * FROM expenses WHERE category=%s", (category,))
    return cursor.fetchall()

@app.get("/sort")
def sort_expenses(sort_by: str):
    valid_sorts = {
        "date_desc": "created_at DESC",
        "date_asc": "created_at ASC",
        "price_desc": "amount DESC",
        "price_asc": "amount ASC"
    }

    if sort_by not in valid_sorts:
        raise HTTPException(status_code=400, detail="Invalid sort option")

    query = f"SELECT * FROM expenses ORDER BY {valid_sorts[sort_by]}"
    cursor.execute(query)
    return cursor.fetchall()

@app.get("/monthly-summary")
def monthly_summary():
    query = """
    SELECT MONTH(created_at) as month,
           SUM(amount) as total
    FROM expenses
    GROUP BY MONTH(created_at)
    """
    cursor.execute(query)
    return cursor.fetchall()

@app.get("/category-summary")
def category_summary():
    query = """
    SELECT category,
           SUM(amount) as total
    FROM expenses
    GROUP BY category
    """
    cursor.execute(query)
    return cursor.fetchall()

@app.get("/export")
def export_csv():
    cursor.execute("SELECT * FROM expenses")
    data = cursor.fetchall()

    df = pd.DataFrame(data)

    stream = io.StringIO()
    df.to_csv(stream, index=False)

    response = StreamingResponse(
        iter([stream.getvalue()]),
        media_type="text/csv"
    )

    response.headers["Content-Disposition"] = "attachment; filename=expenses.csv"
    return response