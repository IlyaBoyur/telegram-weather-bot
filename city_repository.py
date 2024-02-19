from dataclasses import dataclass
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
    def __init__(self, cities: list[City] | None = None):
        self.cities = cities or get_cities()

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
