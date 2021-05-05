import sqlite3
from friendlylog import colored_logger as log
import traceback
from sys import stdout
from os.path import join
import re

DB_DIR = 'db'


class BookKeeper():
    def __init__(self, db):
        self.db = join(DB_DIR, db)
        self.init()

    def init(self):
        try:
            log.debug(f"Try to open database {self.db}")
            self.connection = sqlite3.connect(self.db)
            self.cursor = self.connection.cursor()
            self.cursor.execute(
                """CREATE TABLE IF NOT EXISTS mails (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                  mailid INT NOT NULL,
                  subject text NOT NULL,
                  _from text NULL,
                  _to text NOT NULL
                )""")
            self.connection.commit()
        except Exception as ex:
            log.error(ex)
            traceback.print_exc(file=stdout)

    def track(self, mailid: int, subject: str, _from: str, _to: str):
        subject = re.sub(r"'", '', subject)
        _from = re.sub(r"'", '', _from)
        sql = f"""INSERT INTO mails (mailid, subject, _from, _to) VALUES (
              {mailid}, "{subject}", "{_from}", '{_to}'
            )"""
        # log.debug(f"sql: {sql}")
        self.cursor.execute(
            f"""INSERT INTO mails (mailid, subject, _from, _to) VALUES (
              {mailid}, "{subject}", '{_from}', '{_to}'
            )""")
        self.connection.commit()

    def is_tracked(self, mailid: int):
        result = self.cursor.execute(
            f"""SELECT count(*)
              FROM mails
              WHERE mailid = {mailid}"""
        ).fetchone()
        return result[0] > 0
