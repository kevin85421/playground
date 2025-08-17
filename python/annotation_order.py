from abc import ABC, abstractmethod

class Base(ABC):

    @staticmethod
    @abstractmethod
    def get_communicator_metadata():
        pass


class Impl(Base):
    pass

# 會報錯：TypeError: Can't instantiate abstract class Impl with abstract method get_communicator_metadata
impl = Impl()
