"""DPDP Act data deletion utility.

Purges every clinical artefact SAHAYAK stores: visit payloads, encrypted
transcripts, field history, follow-ups and session rows. Optionally removes
the synthetic beneficiary list and the database file itself.

Usage:
    python scripts/purge_data.py               # interactive confirmation
    python scripts/purge_data.py --yes         # non-interactive
    python scripts/purge_data.py --yes --keep-beneficiaries
    python scripts/purge_data.py --yes --delete-file
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import storage  # noqa: E402


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Purge SAHAYAK clinical data")
    parser.add_argument("--yes", action="store_true", help="skip the confirmation prompt")
    parser.add_argument("--keep-beneficiaries", action="store_true",
                        help="keep the beneficiary registry, purge everything else")
    parser.add_argument("--delete-file", action="store_true",
                        help="also delete the SQLite database file after purging")
    args = parser.parse_args(argv)

    db = storage.db_path()
    print("SAHAYAK data purge")
    print(f"  database : {db}")
    print(f"  key file : {storage._key_file()}")  # noqa: SLF001 - shown to the operator
    print("  scope    : visits, transcripts, field history, follow-ups, sessions"
          + ("" if args.keep_beneficiaries else ", beneficiaries"))

    if not args.yes:
        answer = input("Type 'purge' to continue: ").strip().lower()
        if answer != "purge":
            print("Aborted. Nothing was deleted.")
            return 1

    storage.init_db()
    counts = storage.purge_all(
        keep_beneficiaries=args.keep_beneficiaries,
        remove_db_file=args.delete_file,
    )

    print("\nDeleted rows:")
    for table, count in counts.items():
        if table == "db_file_removed":
            continue
        print(f"  {table:16} {count}")
    if counts.get("db_file_removed"):
        print(f"  database file    removed ({db})")

    remaining = storage.dashboard()
    print("\nRemaining:")
    print(f"  visits        {remaining['total_visits']}")
    print(f"  beneficiaries {remaining['beneficiaries']}")
    print(f"  follow-ups    {len(storage.list_follow_ups(status=None, limit=500))}")
    print("\nPurge complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
