from abc import ABC, abstractmethod


class BaseStorage(ABC):
    @abstractmethod
    def save(self, file_obj, key: str) -> str: ...

    @abstractmethod
    def get_url(self, key: str, expires_in: int = 3600) -> str: ...

    @abstractmethod
    def delete(self, key: str) -> None: ...

    @abstractmethod
    def exists(self, key: str) -> bool: ...
