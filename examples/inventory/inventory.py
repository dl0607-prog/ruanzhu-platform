"""演示库存管理系统 V1.0：SQLite 库存及流水管理。"""
import argparse
import json
import sqlite3
from datetime import datetime


def connect(path):
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    db.execute("CREATE TABLE IF NOT EXISTS products (sku TEXT PRIMARY KEY, name TEXT NOT NULL, quantity INTEGER NOT NULL DEFAULT 0 CHECK(quantity>=0))")
    db.execute("CREATE TABLE IF NOT EXISTS movements (id INTEGER PRIMARY KEY, sku TEXT NOT NULL REFERENCES products(sku), delta INTEGER NOT NULL, created_at TEXT NOT NULL)")
    db.commit()
    return db


def add_product(db, sku, name):
    if not sku.strip() or not name.strip():
        raise ValueError("商品编号和名称不能为空")
    with db:
        db.execute("INSERT INTO products(sku,name) VALUES (?,?)", (sku, name))
    return {"message": "商品已添加", "sku": sku, "name": name}


def change_stock(db, sku, amount):
    if amount == 0:
        raise ValueError("变动数量不能为0")
    with db:
        updated = db.execute("UPDATE products SET quantity=quantity+? WHERE sku=? AND quantity+?>=0", (amount, sku, amount))
        if updated.rowcount != 1:
            raise ValueError("商品不存在或库存不足")
        db.execute("INSERT INTO movements(sku,delta,created_at) VALUES (?,?,?)", (sku, amount, datetime.now().isoformat(timespec="seconds")))
        return dict(db.execute("SELECT * FROM products WHERE sku=?", (sku,)).fetchone())


def list_products(db):
    return [dict(row) for row in db.execute("SELECT * FROM products ORDER BY sku")]


def list_movements(db):
    return [dict(row) for row in db.execute("SELECT * FROM movements ORDER BY id")]


def main():
    parser = argparse.ArgumentParser(description="演示库存管理系统 V1.0")
    parser.add_argument("--db", default="inventory.sqlite3")
    sub = parser.add_subparsers(dest="command", required=True)
    add = sub.add_parser("add", help="添加商品")
    add.add_argument("sku")
    add.add_argument("name")
    for command in ("in", "out"):
        change = sub.add_parser(command, help="入库或出库")
        change.add_argument("sku")
        change.add_argument("amount", type=int)
    sub.add_parser("list", help="查看库存")
    sub.add_parser("history", help="查看流水")
    args = parser.parse_args()
    db = connect(args.db)
    try:
        if args.command == "add":
            result = add_product(db, args.sku, args.name)
        elif args.command in ("in", "out"):
            if args.amount <= 0:
                raise ValueError("数量必须为正整数")
            result = change_stock(db, args.sku, args.amount if args.command == "in" else -args.amount)
        elif args.command == "list":
            result = list_products(db)
        else:
            result = list_movements(db)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (ValueError, sqlite3.IntegrityError) as error:
        parser.exit(1, str(error) + "\n")
    finally:
        db.close()


if __name__ == "__main__":
    main()
