#!/usr/bin/env python
"""Interactive SQLite database query script for study_agent."""

import argparse
import sqlite3
import sys
from pathlib import Path

# Default database path
DEFAULT_DB_PATH = Path(__file__).parent.parent / "study_agent.db"


def get_connection(db_path: str) -> sqlite3.Connection:
    """Create a database connection."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def list_tables(conn: sqlite3.Connection) -> list[str]:
    """List all tables in the database."""
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
    return [row["name"] for row in cursor.fetchall()]


def list_performance_metrics(conn: sqlite3.Connection, user_id: int) -> list[dict]:
    """List performance metrics for a given user."""
    cursor = conn.execute(
        "SELECT * FROM performance_metrics WHERE user_id = ? ORDER BY recorded_at DESC;",
        (user_id,),
    )
    return [dict(row) for row in cursor.fetchall()]


def describe_table(conn: sqlite3.Connection, table_name: str) -> None:
    """Show table schema."""
    cursor = conn.execute(f"PRAGMA table_info({table_name});")
    columns = cursor.fetchall()

    print(f"\nTable: {table_name}")
    print("-" * 80)
    print(f"{'Column':<25} {'Type':<15} {'Nullable':<10} {'Default':<15} {'PK':<5}")
    print("-" * 80)

    for col in columns:
        nullable = "YES" if not col["notnull"] else "NO"
        default = col["dflt_value"] if col["dflt_value"] else ""
        pk = "YES" if col["pk"] else ""
        print(f"{col['name']:<25} {col['type']:<15} {nullable:<10} {default:<15} {pk:<5}")


def count_rows(conn: sqlite3.Connection, table_name: str) -> int:
    """Count rows in a table."""
    cursor = conn.execute(f"SELECT COUNT(*) as count FROM {table_name};")
    return cursor.fetchone()["count"]


def execute_query(conn: sqlite3.Connection, query: str) -> None:
    """Execute a SQL query and display results."""
    try:
        cursor = conn.execute(query)

        # Check if it's a SELECT query
        if query.strip().upper().startswith("SELECT"):
            rows = cursor.fetchall()

            if not rows:
                print("\nNo results found.")
                return

            # Get column names
            columns = rows[0].keys()

            # Calculate column widths
            widths = {col: len(col) for col in columns}
            for row in rows:
                for col in columns:
                    val = str(row[col]) if row[col] is not None else "NULL"
                    widths[col] = max(widths[col], len(val))

            # Print header
            print()
            header = " | ".join(col.ljust(widths[col]) for col in columns)
            print(header)
            print("-" * len(header))

            # Print rows
            for row in rows:
                values = []
                for col in columns:
                    val = str(row[col]) if row[col] is not None else "NULL"
                    values.append(val.ljust(widths[col]))
                print(" | ".join(values))

            print(f"\n{len(rows)} row(s) returned.")
        else:
            conn.commit()
            print(f"\nQuery executed successfully. {cursor.rowcount} row(s) affected.")

    except sqlite3.Error as e:
        print(f"\nSQL Error: {e}")


def show_summary(conn: sqlite3.Connection) -> None:
    """Show database summary."""
    tables = list_tables(conn)

    print("\n" + "=" * 60)
    print("DATABASE SUMMARY")
    print("=" * 60)

    for table in tables:
        if table.startswith("sqlite_"):
            continue
        count = count_rows(conn, table)
        print(f"  {table:<30} {count:>10} rows")

    print("=" * 60)


def interactive_mode(conn: sqlite3.Connection) -> None:
    """Run interactive query mode."""
    print("\n" + "=" * 60)
    print("STUDY AGENT DATABASE QUERY TOOL")
    print("=" * 60)
    print("\nCommands:")
    print("  .tables          - List all tables")
    print("  .describe <tbl>  - Show table schema")
    print("  .summary         - Show database summary")
    print("  .sample <tbl>    - Show sample data from table")
    print("  .quit / .exit    - Exit the program")
    print("  <SQL>            - Execute SQL query")
    print("\n" + "=" * 60)

    while True:
        try:
            query = input("\nsql> ").strip()

            if not query:
                continue

            if query.lower() in (".quit", ".exit", "quit", "exit"):
                print("Goodbye!")
                break

            if query.lower() == ".tables":
                tables = list_tables(conn)
                print("\nTables:")
                for table in tables:
                    if not table.startswith("sqlite_"):
                        print(f"  - {table}")
                continue

            if query.lower().startswith(".describe"):
                parts = query.split()
                if len(parts) < 2:
                    print("Usage: .describe <table_name>")
                    continue
                table_name = parts[1]
                describe_table(conn, table_name)
                continue

            if query.lower() == ".summary":
                show_summary(conn)
                continue

            if query.lower().startswith(".sample"):
                parts = query.split()
                if len(parts) < 2:
                    print("Usage: .sample <table_name>")
                    continue
                table_name = parts[1]
                execute_query(conn, f"SELECT * FROM {table_name} LIMIT 10;")
                continue

            # Execute as SQL
            execute_query(conn, query)

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except EOFError:
            print("\nGoodbye!")
            break


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Query the study_agent SQLite database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python query_db.py                           # Interactive mode
  python query_db.py --tables                  # List all tables
  python query_db.py --describe users          # Show users table schema
  python query_db.py --summary                 # Show database summary
  python query_db.py -q "SELECT * FROM users"  # Execute a query
        """,
    )

    parser.add_argument(
        "--db",
        "-d",
        type=str,
        default=str(DEFAULT_DB_PATH),
        help=f"Path to SQLite database (default: {DEFAULT_DB_PATH})",
    )
    parser.add_argument(
        "--tables",
        "-t",
        action="store_true",
        help="List all tables",
    )
    parser.add_argument(
        "--describe",
        type=str,
        metavar="TABLE",
        help="Describe a table schema",
    )
    parser.add_argument(
        "--summary",
        "-s",
        action="store_true",
        help="Show database summary",
    )
    parser.add_argument(
        "--query",
        "-q",
        type=str,
        help="Execute a SQL query",
    )
    parser.add_argument(
        "--sample",
        type=str,
        metavar="TABLE",
        help="Show sample data from a table (first 10 rows)",
    )

    args = parser.parse_args()

    # Check if database exists
    db_path = Path(args.db)
    if not db_path.exists():
        print(f"Error: Database not found at {db_path}")
        print("Make sure the database has been initialized.")
        sys.exit(1)

    # Connect to database
    conn = get_connection(str(db_path))

    try:
        # Handle command-line arguments
        if args.tables:
            tables = list_tables(conn)
            print("\nTables:")
            for table in tables:
                if not table.startswith("sqlite_"):
                    print(f"  - {table}")

        elif args.describe:
            describe_table(conn, args.describe)

        elif args.summary:
            show_summary(conn)

        elif args.query:
            execute_query(conn, args.query)

        elif args.sample:
            execute_query(conn, f"SELECT * FROM {args.sample} LIMIT 10;")

        else:
            # Interactive mode
            interactive_mode(conn)

    finally:
        conn.close()


if __name__ == "__main__":
    main()
