import sqlite3

from app import ERPSystem


def test_end_to_end_flow(tmp_path):
    db_path = tmp_path / "erp.db"
    erp = ERPSystem(str(db_path))
    erp.init_db()

    emp_id = erp.create_employee("E001", "Somchai Prasert", "Production", "Planner")
    customer_id = erp.create_customer("Niran House", "Niran Co.")
    quote_id = erp.create_quotation("Q-001", customer_id, "Project A", "Sliding", 150000, "Approved")
    wo_id = erp.create_work_order("WO-001", quote_id, emp_id, "In Production")
    install_id = erp.create_installation("IN-001", wo_id, team_lead_employee_id=emp_id)
    erp.create_delivery("DL-001", install_id, status="Delivered")

    report = erp.get_flow_report()
    assert len(report) == 1
    assert report[0]["quote_no"] == "Q-001"
    assert report[0]["delivery_no"] == "DL-001"


def test_schema_created(tmp_path):
    db_path = tmp_path / "schema.db"
    erp = ERPSystem(str(db_path))
    erp.init_db()

    with sqlite3.connect(db_path) as conn:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            ).fetchall()
        }
    assert {
        "employees",
        "customers",
        "quotations",
        "work_orders",
        "installations",
        "deliveries",
    }.issubset(tables)
