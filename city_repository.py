import pymongo
from dataclasses import dataclass

import settings
from utils import get_cities


@dataclass
class City:
    name: str
    url_source: str = ""
    longitude: float | None = None
    latitude: float | None = None


class CityNotExist(RuntimeError):
    pass


class CityRepository:
    def __init__(self, cities: list[City] | None = None, use_mongodb: bool | None = None):
        self.db = self._get_database()
        self.use_mongodb = use_mongodb if use_mongodb is not None else settings.USE_MONGODB

    def get(self, **filters) -> City:
        try:
            return next(
                city
                for city in self.cities
                if all(getattr(city, key) == value for key, value in filters)
            )
        except StopIteration:
            raise CityNotExist

    def get_multi(self) -> list[City]:
        return self.cities

    def first(self, **filters) -> City | None:
        try:
            return next(
                city
                for city in self.cities
                if all(getattr(city, key) == value for key, value in filters)
            )
        except StopIteration:
            return None

    @property
    def cities(self):
        if self.use_mongodb:
            return self.db.cities
        return get_cities()

    def _get_database(self):
        """Get MongoDB database."""
        return pymongo.MongoClient(settings.MONGODB_URL)[settings.MONGODB_DBNAME]

