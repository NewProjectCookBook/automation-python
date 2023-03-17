from __future__ import annotations

import os
from enum import Enum

import oracledb
import psycopg2
import json
import zlib

from typing import Any, TypeVar, NoReturn
from abc import ABC, abstractmethod


class DBInterface(ABC):
    @property
    @abstractmethod
    def cursor(self) -> NoReturn:
        """Getting a cursor to work with the database client"""
        raise NotImplemented

    @abstractmethod
    def get_list(self, query: str) -> NoReturn:
        """Getting values from the base by the first column as an array"""
        raise NotImplemented

    @abstractmethod
    def get_dict(self, query: str) -> NoReturn:
        """Getting information from the database in the form of a dictionary
           The request must be in the format select id_dictionary, value_dictionary"""
        raise NotImplemented

    @abstractmethod
    def select_all(self, query: str) -> NoReturn:
        """Getting all values from the base as an array of tuples"""
        raise NotImplemented

    @abstractmethod
    def get_first_value(self, query: str) -> NoReturn:
        """Getting the first value of the first row from the base"""
        raise NotImplemented

    @abstractmethod
    def get_first_row(self, query: str) -> NoReturn:
        """Getting the first row from the base"""
        raise NotImplemented

    @abstractmethod
    def get_lob_list(self, query: str) -> NoReturn:
        """Retrieving multiple cell data from a LOB database"""
        raise NotImplemented

    @abstractmethod
    def get_waited_lob_data(self, query: str) -> NoReturn:
        """Getting from LOB database from one cell"""
        raise NotImplemented

    @abstractmethod
    def bytes_into_json(self, query: str) -> NoReturn:
        """Convert byte data stream to json format"""
        raise NotImplemented


class DBCommon(DBInterface):
    @property
    def cursor(self) -> NoReturn:
        raise NotImplemented

    def get_list(self, query: str) -> list[Any]:
        return [value[0] for value in self.cursor.execute(query).fetchall()]

    def get_dict(self, query: str) -> dict[Any, Any]:
        return {value[0]: value[1] for value in self.cursor.execute(query).fetchall()}

    def select_all(self, query: str) -> list[tuple]:
        return self.cursor.execute(query).fetchall()

    def get_first_value(self, query: str) -> Any:
        result = self.cursor.execute(query).fetchone()
        if not result:
            return None
        return result[0]

    def get_first_row(self, query: str) -> Any:
        return self.cursor.execute(query).fetchone()

    def get_lob_list(self, query: str) -> list | None:
        result = self.cursor.execute(query).fetchall()
        if not result:
            return None
        return [lob[0] for lob in result]

    def get_waited_lob_data(self, query: str) -> str | bytes | None:
        result = self.cursor.execute(query).fetchall()
        if not result or not result[0][0]:
            return None
        return result[0][0].read()

    def bytes_into_json(self, query: str) -> Any:
        data = self.get_waited_lob_data(query=query)
        assert data is not None, 'Got an empty value on fetch'
        data = json.loads((zlib.decompress(data, zlib.MAX_WBITS | 16)).decode('UTF-8'))
        return data


class OracleClient(DBCommon):

    def __init__(self, connection_string: str) -> None:
        self.connection_string = connection_string
        self.connector = oracledb.connect(self.connection_string, encoding='UTF-8', nencoding='UTF-8')
        self._cursor = self.connector.cursor()

    @property
    def cursor(self) -> oracledb.Cursor:
        """Getting a cursor to work with the database client"""
        return self._cursor


class PostgresClient(DBCommon):

    def __init__(self, connection_string: str) -> None:
        self.connection_string = connection_string
        self.connector = psycopg2.connect(self.connection_string, encoding='UTF-8', nencoding='UTF-8')
        self._cursor = self.connector.cursor()

    @property
    def cursor(self) -> psycopg2.extensions.cursor:
        """Getting a cursor to work with the database client"""
        return self._cursor


class DBClient:
    def __init__(self, connection_string: str) -> None:
        self.db_type = os.getenv('db_type') or DBList.ORACLE.value
        self.conn = connection_string
        self.db_client = None

    def __enter__(self) -> DBClientType:
        db = {
            DBList.ORACLE.value: OracleClient,
            DBList.POSTGRES.value: PostgresClient,
        }
        self.db_client = db[self.db_type](connection_string=self.conn)
        return self.db_client

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self.db_client:
            if exc_tb is None:
                self.db_client.connector.commit()
            else:
                self.db_client.connector.rollback()
            self.db_client.cursor.close()
            self.db_client.connector.close()


DBClientType = TypeVar("DBClientType", OracleClient, PostgresClient)


class DBList(Enum):
    ORACLE = 'db'
    POSTGRES = 'dbpg'
