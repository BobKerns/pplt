'''
Routines to extract data from Quicken files.
'''

from pathlib import Path
import sqlite3 as sql

DB = Path('/tmp/quicken_data/family-2023.quicken/data')

SQL_ACCOUNTS = '''
SELECT zaccount.z_pk, zaccount.zname as name, ztypename as type, zonlinebankingledgerbalanceamount as balance from zaccount;
'''

with sql.connect(DB) as conn:
    cursor = conn.cursor()
    cursor.execute(SQL_ACCOUNTS)
    for row in cursor.fetchall():
        print(row)
