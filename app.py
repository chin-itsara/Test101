from __future__ import annotations

import argparse
import sqlite3
from dataclasses import dataclass
from pathlib import Path

DEFAULT_DB = Path(__file__).resolve().parent / "factory_erp.db"


@dataclass
class ERPSystem:
    db_path: str = str(DEFAULT_DB)

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS employees (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    employee_code TEXT UNIQUE NOT NULL,
                    full_name TEXT NOT NULL,
                    department TEXT NOT NULL,
                    position TEXT NOT NULL,
                    phone TEXT,
                    start_date TEXT
                );

                CREATE TABLE IF NOT EXISTS customers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_name TEXT NOT NULL,
                    company_name TEXT,
                    phone TEXT,
                    email TEXT,
                    address TEXT
                );

                CREATE TABLE IF NOT EXISTS quotations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    quote_no TEXT UNIQUE NOT NULL,
                    customer_id INTEGER NOT NULL,
                    project_name TEXT NOT NULL,
                    product_type TEXT NOT NULL,
                    total_amount REAL NOT NULL,
                    status TEXT NOT NULL DEFAULT 'Draft',
                    issue_date TEXT,
                    FOREIGN KEY (customer_id) REFERENCES customers (id)
                );

                CREATE TABLE IF NOT EXISTS work_orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    wo_no TEXT UNIQUE NOT NULL,
                    quotation_id INTEGER NOT NULL,
                    planner_employee_id INTEGER,
                    status TEXT NOT NULL DEFAULT 'Planned',
                    production_start TEXT,
                    production_end TEXT,
                    notes TEXT,
                    FOREIGN KEY (quotation_id) REFERENCES quotations (id),
                    FOREIGN KEY (planner_employee_id) REFERENCES employees (id)
                );

                CREATE TABLE IF NOT EXISTS installations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    install_no TEXT UNIQUE NOT NULL,
                    work_order_id INTEGER NOT NULL,
                    install_date TEXT,
                    team_lead_employee_id INTEGER,
                    site_address TEXT,
                    status TEXT NOT NULL DEFAULT 'Scheduled',
                    FOREIGN KEY (work_order_id) REFERENCES work_orders (id),
                    FOREIGN KEY (team_lead_employee_id) REFERENCES employees (id)
                );

                CREATE TABLE IF NOT EXISTS deliveries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    delivery_no TEXT UNIQUE NOT NULL,
                    installation_id INTEGER NOT NULL,
                    delivered_date TEXT,
                    receiver_name TEXT,
                    status TEXT NOT NULL DEFAULT 'Pending',
                    remark TEXT,
                    FOREIGN KEY (installation_id) REFERENCES installations (id)
                );
                """
            )

    def create_employee(self, employee_code: str, full_name: str, department: str, position: str, phone: str = "", start_date: str = "") -> int:
        with self.connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO employees (employee_code, full_name, department, position, phone, start_date)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (employee_code, full_name, department, position, phone, start_date),
            )
            return cur.lastrowid

    def create_customer(self, customer_name: str, company_name: str = "", phone: str = "", email: str = "", address: str = "") -> int:
        with self.connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO customers (customer_name, company_name, phone, email, address)
                VALUES (?, ?, ?, ?, ?)
                """,
                (customer_name, company_name, phone, email, address),
            )
            return cur.lastrowid

    def create_quotation(self, quote_no: str, customer_id: int, project_name: str, product_type: str, total_amount: float, status: str = "Draft", issue_date: str = "") -> int:
        with self.connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO quotations (quote_no, customer_id, project_name, product_type, total_amount, status, issue_date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (quote_no, customer_id, project_name, product_type, total_amount, status, issue_date),
            )
            return cur.lastrowid

    def create_work_order(self, wo_no: str, quotation_id: int, planner_employee_id: int | None = None, status: str = "Planned", production_start: str = "", production_end: str = "", notes: str = "") -> int:
        with self.connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO work_orders (wo_no, quotation_id, planner_employee_id, status, production_start, production_end, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (wo_no, quotation_id, planner_employee_id, status, production_start, production_end, notes),
            )
            return cur.lastrowid

    def create_installation(self, install_no: str, work_order_id: int, install_date: str = "", team_lead_employee_id: int | None = None, site_address: str = "", status: str = "Scheduled") -> int:
        with self.connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO installations (install_no, work_order_id, install_date, team_lead_employee_id, site_address, status)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (install_no, work_order_id, install_date, team_lead_employee_id, site_address, status),
            )
            return cur.lastrowid

    def create_delivery(self, delivery_no: str, installation_id: int, delivered_date: str = "", receiver_name: str = "", status: str = "Pending", remark: str = "") -> int:
        with self.connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO deliveries (delivery_no, installation_id, delivered_date, receiver_name, status, remark)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (delivery_no, installation_id, delivered_date, receiver_name, status, remark),
            )
            return cur.lastrowid

    def get_flow_report(self) -> list[sqlite3.Row]:
        with self.connect() as conn:
            return conn.execute(
                """
                SELECT q.quote_no, c.customer_name, w.wo_no, i.install_no, d.delivery_no, d.status AS delivery_status
                FROM quotations q
                JOIN customers c ON c.id = q.customer_id
                LEFT JOIN work_orders w ON w.quotation_id = q.id
                LEFT JOIN installations i ON i.work_order_id = w.id
                LEFT JOIN deliveries d ON d.installation_id = i.id
                ORDER BY q.id
                """
            ).fetchall()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Factory ERP CLI")
    parser.add_argument("--db", default=str(DEFAULT_DB), help="SQLite database path")
    parser.add_argument("--init", action="store_true", help="Initialize database tables")
    parser.add_argument("--demo", action="store_true", help="Insert one complete demo flow")
    parser.add_argument("--report", action="store_true", help="Print quote-to-delivery flow")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    erp = ERPSystem(db_path=args.db)

    if args.init:
        erp.init_db()
        print("Database initialized")

    if args.demo:
        erp.init_db()
        emp_id = erp.create_employee("E001", "Somchai Prasert", "Production", "Planner", "0812345678", "2024-01-01")
        customer_id = erp.create_customer("Niran House", "Niran Co.", "021111111", "client@example.com", "Bangkok")
        quote_id = erp.create_quotation("Q-001", customer_id, "Project A", "Sliding Door", 150000, "Approved", "2024-02-01")
        wo_id = erp.create_work_order("WO-001", quote_id, emp_id, "In Production", "2024-02-02", "2024-02-10", "High priority")
        install_id = erp.create_installation("IN-001", wo_id, "2024-02-15", emp_id, "Chiang Mai", "Scheduled")
        erp.create_delivery("DL-001", install_id, "2024-02-20", "Owner", "Delivered", "Completed")
        print("Demo data inserted")

    if args.report:
        rows = erp.get_flow_report()
        print("quote_no | customer_name | wo_no | install_no | delivery_no | delivery_status")
        for row in rows:
            print(
                f"{row['quote_no']} | {row['customer_name']} | {row['wo_no'] or '-'} | "
                f"{row['install_no'] or '-'} | {row['delivery_no'] or '-'} | {row['delivery_status'] or '-'}"
            )


if __name__ == "__main__":
    main()
