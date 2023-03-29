from __future__ import annotations
from typing import Any, Optional, Hashable
from pyignite import Client


class IgniteClient(Client):
    """Apache Ignite cache client
         page_size: cursor page size. Default is 1024
    """

    def __init__(self, config: dict[str, Any], use_ssl: bool = True, **kwargs: Any) -> None:
        self.cache_host = config.get('cache_host')
        self.cache_port = int(config.get('cache_port'))
        self._conn = None
        super().__init__(username=config.get('cache_login'), password=config.get('cache_pass'),
                         use_ssl=use_ssl, **kwargs)

    def __enter__(self) -> IgniteClient:
        self._conn = self.connect(self.cache_host, self.cache_port)
        return self

    def get_list(self, query: str, page_size: int = 1024) -> list[Any]:
        """Getting values from the cache by the first column as an array"""
        return [value[0] for value in self.sql(query_str=query, page_size=page_size)]

    def get_dict(self, query: str, page_size: int = 1024) -> dict[Hashable, Any]:
        """Getting information from the cache in the form of a dictionary
           The request must be in the format select id_dictionary, value_dictionary"""
        return {value[0]: value[1] for value in self.sql(query_str=query, page_size=page_size)}

    def select_all(self, query: str, page_size: int = 1024) -> list[tuple[Any]]:
        """Getting all values from the cache as an array of tuples"""
        return list(self.sql(query_str=query, page_size=page_size))

    def get_first_value(self, query: str, page_size: int = 1024) -> Any:
        """Getting the first value of the first row from the cache"""
        result = next(self.sql(query_str=query, page_size=page_size), None)
        if not result:
            return None
        return result[0]

    def get_first_row(self, query: str, page_size: int = 1024) -> Any:
        """Getting the first line from the cache"""
        return next(self.sql(query_str=query, page_size=page_size), None)

    def __exit__(self, exc_type: Optional[str], exc_val: Optional[str], exc_tb: Optional[str]) -> None:
        self.close()
