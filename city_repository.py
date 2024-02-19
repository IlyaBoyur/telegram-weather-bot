import pymongo
from dataclasses import dataclass, asdict

import settings
from utils import get_cities_from_csv


@dataclass
class City:
    name: str
    url_source: str = ""
    longitude: float | None = None
    latitude: float | None = None


class CityNotExist(RuntimeError):
    pass


class MongoDBRepository:
    def __init__(
        self,
        db_url: str = "",
        db_name: str = "",
        collection_name: str = "collection",
    ) -> None:
        self.mongodb_url = db_url or settings.MONGODB_URL
        self.mongodb_name = db_name or settings.MONGODB_DBNAME
        self.collection_name = collection_name
        self.db = self._get_database()

    def _get_database(self) -> pymongo.MongoClient:
        """Get MongoDB database."""
        return pymongo.MongoClient(self.mongodb_url)[self.mongodb_name]

    def get_multi(self) -> list:
        return self.db[self.collection_name]

    def create_multi(self, objects: list[object]) -> bool:
        return self.db[self.collection_name].insert_many(
            [asdict(obj) for obj in objects]
        )

    def get(self, **filters) -> object:
        try:
            return next(
                obj
                for obj in self.db[self.collection_name]
                if all(getattr(obj, key) == value for key, value in filters)
            )
        except StopIteration:
            raise RuntimeError("Object does not exist.")

    def first(self, **filters) -> object | None:
        try:
            return next(
                obj
                for obj in self.db[self.collection_name]
                if all(getattr(obj, key) == value for key, value in filters)
            )
        except StopIteration:
            return None


class CityRepository(MongoDBRepository):
    def __init__(
        self, cities: list[City] | None = None, *args, **kwargs
    ) -> None:
        if cities is not None:
            self.create_multi(cities)
        super().__init__(*args, **kwargs)

    @classmethod
    def from_csv(cls):
        return cls(cities=get_cities_from_csv())
