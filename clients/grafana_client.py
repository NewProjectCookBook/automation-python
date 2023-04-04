from __future__ import annotations

from typing import Any

from influxdb import InfluxDBClient
from requests import Response


class GrafanaClient:
    """ GrafanaClient helps to save test results """
    def __init__(self, host: str, port: int, username: str, password: str, database: str) -> None:
        """
        Initializes the InfluxDB client.

        :param host: The InfluxDB host.
        :param port: The InfluxDB port.
        :param username: The InfluxDB username.
        :param password: The InfluxDB password.
        :param database: The InfluxDB database name.
        """
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.database = database
        self.client = None

    def __enter__(self) -> GrafanaClient:
        """
        Creates a connection to InfluxDB.

        :return: The InfluxDB client instance.
        """
        self.client = InfluxDBClient(host=self.host, port=self.port, username=self.username, password=self.password,
                                     database=self.database)
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        """ Closes the connection to InfluxDB. """
        self.client.close()

    def query(self, query: str) -> list[tuple[Any]]:
        """
        Executes a query on the InfluxDB database.

        :param query: The InfluxDB query to execute.
        :return: The query results as a list of tuples.
        """
        result = self.client.query(query)
        return result.raw['series'][0]['values']

    def insert_request_results(self, measurement: str, response: Response) -> None:
        """
        Inserts the total request time from a `requests` response object into InfluxDB.

        :param measurement: The name of the measurement to insert into.
        :param response: The `requests` response object to extract the total time from.
        """
        total_time = response.elapsed.total_seconds()
        json_body = [
            {
                'measurement': measurement,
                'fields': {
                    'total_time': total_time
                }
            }
        ]
        self.client.write_points(json_body)

    def select_all(self, measurement: str) -> list[tuple[Any]]:
        """
        Selects all data from a specified measurement.

        :param measurement: The name of the measurement to select from.
        :return: The query results as a list of tuples.
        """
        query = f'SELECT * FROM {measurement}'
        result = self.client.query(query)
        return result.raw['series'][0]['values']

    def execute(self, query: str) -> list[tuple[Any]]:
        """
        Executes a query on the InfluxDB database.

        :param query: The InfluxDB query to execute.
        :return: The query results as a list of tuples.
        """
        result = self.client.query(query)
        return result.raw['series'][0]['values']
