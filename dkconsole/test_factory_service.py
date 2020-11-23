from django.test import TestCase
from dkconsole.service_factory import factory


class SomeClass():
    @classmethod
    def return_42(cls):
        return 42


class SomeInterfaceClass():
    @classmethod
    def return_100(cls):
        raise NotImplementedError


class SomeConcreteClass(SomeInterfaceClass):
    @classmethod
    def return_43(cls):
        return 43

    @classmethod
    def return_100(cls):
        return 101


class AnotherConcreteClass(SomeInterfaceClass):
    @classmethod
    def return_100(cls):
        return 102


class TestFactoryService(TestCase):
    def test_python_class_behavior(self):
        # Verify we can assign a class to a variable and use that variable to invoke classmethod

        serviceClass = SomeClass
        assert serviceClass.return_42() == 42

    def test_service_factory(self):
        factory.register('vehicle', SomeClass)

        svc: SomeClass = factory.create('vehicle')

        assert svc.return_42() == 42
        assert svc == SomeClass

    def test_concrete_class(self):
        factory.register('vehicle', SomeConcreteClass)

        svc: SomeInterfaceClass = factory.create('vehicle')

        assert svc.return_100() == 101      # Calling a method as defined in interface, overriding interface method to return 101
        assert svc.return_43() == 43        # Calling a concrete class method, code completion will not happen

    def test_another_concrete_class(self):
        factory.register('vehicle', SomeConcreteClass)

        svc: SomeInterfaceClass = factory.create('vehicle')

        assert svc.return_100() == 101      # Calling a method as defined in interface, overriding interface method to return 102


