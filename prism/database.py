# Copyright 2021-xx iiPython

# Modules
import os
import sqlite3
from typing import Union, Any
from prism.config import config
from sqlite3.dbapi2 import Cursor, Row

# Connection handler
class DBConnection(object):
    def __init__(self, db_path: str) -> None:
        self.db_path = os.path.abspath(db_path).replace("\\", "/")
        self.db_name = self.db_path.split("/")[-1].split(".db")[0]
        self._load_db()

    def __factory__(self, cursor: Cursor, row: Row) -> dict:
        data = {}
        for idx, col in enumerate(cursor.description):
            data[col[0]] = row[idx]

        return data

    def _load_db(self) -> None:
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = self.__factory__
        self.cursor = self.conn.cursor()

    def _close_db(self) -> None:
        self.conn.commit()
        self.conn.close()

    def save(self) -> None:
        self._close_db()
        self._load_db()
        return self.cursor

    def create(self, values: tuple, table: str = None) -> Cursor:
        if table is None:
            table = self.db_name

        self.cursor.execute(f"INSERT INTO {table} VALUES ({('?,' * len(values))[:-1]})", values)
        return self.save()

    def update(self, values: dict, identifiers: Union[tuple, list], table: str = None) -> Cursor:
        if table is None:
            table = self.db_name

        if isinstance(identifiers, tuple):
            identifiers = [identifiers]

        # Convert booleans
        for val in values:
            current_val = values[val]
            if isinstance(current_val, bool):
                values[val] = current_val == 1

        # Handle updating table
        for v in values:
            self.cursor.execute(f"UPDATE {table} SET {v}=? WHERE {''.join(f'{identifier[0]}=? AND ' for identifier in identifiers)[:-5]}", [values[v]] + [_[1] for _ in identifiers] if len(identifiers) > 1 else (values[v], identifiers[0][1],))

        return self.save()

    def get(self, identifier: tuple, key: str = None, table: str = None) -> Any:
        if table is None:
            table = self.db_name

        if not self.test_for(identifier, table):
            return None

        # Grab data
        self.cursor.execute(f"SELECT * FROM {table} WHERE {identifier[0]}=?", (identifier[1],))
        data = self.cursor.fetchone()
        if key is not None:
            data = data[key]

        return data

    def getall(self, identifier: tuple, key: str = None, table: str = None) -> Any:
        if table is None:
            table = self.db_name

        if not self.test_for(identifier, table):
            return None

        # Grab data
        self.cursor.execute(f"SELECT * FROM {table} WHERE {identifier[0]}=?", (identifier[1],))
        data = self.cursor.fetchall()
        return data

    def test_for(self, identifiers: Union[tuple, list], table: str = None) -> bool:
        if table is None:
            table = self.db_name

        if isinstance(identifiers, tuple):
            identifiers = [identifiers]

        self.cursor.execute(f"SELECT * FROM {table} WHERE {''.join(f'{identifier[0]}=? AND ' for identifier in identifiers)[:-5]}", [_[1] for _ in identifiers] if len(identifiers) > 1 else (identifiers[0][1],))
        return self.cursor.fetchone() is not None

    def execute(self, *args, **kwargs) -> Cursor:
        return self.cursor.execute(*args, **kwargs)

# Database handler
class Database(object):
    def __init__(self) -> None:
        self._db_cache = {}
        self._db_dir = os.path.abspath(config.get(["paths", "db_dir"]))

    def load_db(self, name: str) -> DBConnection:
        if not name.endswith(".db"):
            name += ".db"

        db_path = os.path.join(self._db_dir, name)
        if name not in self._db_cache:
            db_conn = DBConnection(db_path)
            self._db_cache[name] = db_conn

        return self._db_cache[name]
