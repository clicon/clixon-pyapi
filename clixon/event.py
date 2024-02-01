from typing import Callable as function, Optional
from fnmatch import fnmatch
from clixon.args import get_logger

logger = get_logger()


class RPCEventHandler():
    """
    A simple event handler class.
    """

    def __init__(self) -> None:
        """
        Initialize the event handler.
        """

        self.events = {}

    def register(self, event: str) -> None:
        """
        Register a callback to an event.
        """

        def decorator(callback: function) -> function:
            if event not in self.events:
                self.events[event] = []
            self.events[event].append(callback)

            logger.debug(f"Registered {callback} to {event}")

            return callback
        return decorator

    def unregister(self, event: str, callback: function) -> None:
        """
        Unregister a callback from an event.
        """

        if event in self.events:
            self.events[event].remove(callback)

            logger.debug(f"Unregistered {callback} from {event}")

    def emit(self, event: str, not_found_error: Optional[bool] = False,
             *args: Optional[dict],
             **kwargs: Optional[dict]) -> None:
        """
        Emit an event.
        """

        for k, v in self.events.items():
            if fnmatch(event, k):
                for callback in v:
                    logger.debug(f"Emitting {event} to {callback}")
                    callback(*args, **kwargs)
        else:
            if not_found_error:
                raise Exception(f"Event {event} not found")
