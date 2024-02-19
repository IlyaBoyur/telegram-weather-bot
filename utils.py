def get_cities():
    from .city_repository import CityRepository

    return CityRepository().get_multi()
