import json
import sqlite3 as sqlite
from pathlib import Path


class Data:

    def __init__(self):
        self.con = sqlite.connect('database.db')
        self.cur = self.con.cursor()
        self.cur.execute("CREATE TABLE IF NOT EXISTS file(id, ts)")

    def delete_file(self, identity, timestamp):
        timestamp = int(timestamp, 16)
        Path(f'data/{identity}/{timestamp}.json').unlink(missing_ok=True)
        self.cur.execute(f"""DELETE FROM file
                         WHERE ts == {timestamp} AND id == {identity}""")
        self.con.commit()

    def history(self, identity):
        self.cur.execute(f"""SELECT ts FROM file WHERE id == {identity}
                         ORDER BY ts DESC""")
        return self.cur.fetchall()

    def insert_file(self, identity, timestamp, embed):
        Path(f'data/{identity}').mkdir(parents=True, exist_ok=True)
        with open(f'data/{identity}/{timestamp}.json', 'w') as save:
            json.dump(embed, save, indent=4)
        self.cur.execute("INSERT INTO file VALUES(?, ?)", (identity, timestamp))
        self.con.commit()
