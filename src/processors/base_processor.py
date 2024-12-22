from abc import ABC, abstractmethod

class BaseProcessor(ABC):
    @abstractmethod
    def process_frame(self, frame):
        pass 