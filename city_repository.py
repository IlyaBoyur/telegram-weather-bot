from dataclasses import dataclass


CITIES: list["City"] = []


class CityNotExist(RuntimeError):
    pass


@dataclass
class City:
    name: str
    url_source: str = ""
    longitude: float | None = None
    latitude: float | None = None


class CityRepository:
    def get(**filters) -> City:
        try:
            return next(city for city in CITIES if all(getattr(city, key)==value for key, value in filters))
        except StopIteration:
            raise CityNotExist
    
    def get_multi() -> list[City]:
        return CITIES

    def first(**filters) -> City | None:
        try:
            return next(city for city in CITIES if all(getattr(city, key)==value for key, value in filters))
        except StopIteration:
            return None
        
