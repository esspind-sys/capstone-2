import sqlite3

conn = sqlite3.connect("./data/database.sqlite")
cur = conn.cursor()

cur.executescript("""
DROP TABLE IF EXISTS sales;
DROP TABLE IF EXISTS customers;
DROP TABLE IF EXISTS employees;

CREATE TABLE sales (
    id INTEGER PRIMARY KEY,
    region TEXT,
    product TEXT,
    revenue REAL,
    date TEXT,
    units_sold INTEGER
);

CREATE TABLE customers (
    id INTEGER PRIMARY KEY,
    name TEXT,
    industry TEXT,
    churn_date TEXT,
    satisfaction_score REAL
);

CREATE TABLE employees (
    id INTEGER PRIMARY KEY,
    department TEXT,
    satisfaction_score REAL,
    tenure_years REAL
);
""")

sales = [
    ("North", "Widget A", 12000.0, "2025-01-15", 240),
    ("North", "Widget B", 8500.0, "2025-02-10", 170),
    ("South", "Widget A", 15300.0, "2025-01-20", 306),
    ("South", "Widget C", 9800.0, "2025-03-05", 196),
    ("East",  "Widget B", 7200.0, "2025-02-28", 144),
    ("East",  "Widget A", 11100.0, "2025-03-18", 222),
    ("West",  "Widget C", 13400.0, "2025-01-30", 268),
    ("West",  "Widget B", 6900.0, "2025-03-22", 138),
    ("North", "Widget C", 10200.0, "2025-04-12", 204),
    ("South", "Widget B", 14700.0, "2025-04-25", 294),
]
cur.executemany(
    "INSERT INTO sales (region, product, revenue, date, units_sold) VALUES (?, ?, ?, ?, ?)",
    sales,
)

customers = [
    ("Acme Corp",      "Manufacturing", None,         4.5),
    ("Globex",         "Finance",       "2025-02-01", 2.8),
    ("Initech",        "Technology",    None,         4.1),
    ("Umbrella Inc",   "Healthcare",    "2025-03-15", 3.2),
    ("Stark Industries","Technology",   None,         4.8),
    ("Wayne Enterprises","Finance",     None,         4.3),
    ("Soylent Co",     "Manufacturing", "2025-01-10", 2.5),
    ("Hooli",          "Technology",    None,         3.9),
]
cur.executemany(
    "INSERT INTO customers (name, industry, churn_date, satisfaction_score) VALUES (?, ?, ?, ?)",
    customers,
)

employees = [
    ("Engineering", 4.2, 3.5),
    ("Engineering", 3.8, 1.2),
    ("Sales",       4.5, 5.0),
    ("Sales",       3.1, 0.8),
    ("Support",     4.0, 2.3),
    ("Support",     4.6, 4.1),
    ("Marketing",   3.5, 1.9),
    ("Marketing",   4.1, 3.0),
]
cur.executemany(
    "INSERT INTO employees (department, satisfaction_score, tenure_years) VALUES (?, ?, ?)",
    employees,
)

conn.commit()
conn.close()
print("Database seeded: data/database.sqlite")
print(f"  sales rows:     {len(sales)}")
print(f"  customers rows: {len(customers)}")
print(f"  employees rows: {len(employees)}")