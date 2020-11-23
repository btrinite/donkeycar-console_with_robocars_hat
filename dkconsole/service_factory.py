class ServiceFactory:
    def __init__(self):
        self.__services = {}

    def register(self, name, service_class):
        # Maybe add some validation
        self.__services[name] = service_class

    def create(self, name, *args, **kwargs):
        # Maybe add some error handling or fallbacks
        # return self.__services[name](*args, **kwargs)

        return self.__services[name]


factory = ServiceFactory()
