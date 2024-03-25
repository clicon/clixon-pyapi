from fnmatch import fnmatch
from logging import getLogger
from typing import Callable as function, Optional


class RPCEventHandler():
    """
    A simple event handler class.
    """

    def __init__(self) -> None:
        """
        Initialize the event handler.

        :return: None
        :rtype: None
        """

        self.events = {}
        self.logger = getLogger(__name__)

    def register(self, event: str) -> None:
        """
        Register a callback to an event.

        :param event: The event to register to.
        :type event: str
        :return: None
        :rtype: None
        """

        def decorator(callback: function) -> function:
            """
            A decorator to register a callback to an event.
            :param callback: The callback to register.

            :return: The callback.
            :rtype: function

            """

            # If the event is not in the events dictionary, add it.
            if event not in self.events:
                self.events[event] = []
            self.events[event].append(callback)

            self.logger.debug(f"Registered {callback} to {event}")

            return callback
        return decorator

    def unregister(self, event: str, callback: function) -> None:
        """
        Unregister a callback from an event.

        :param event: The event to unregister from.
        :type event: str
        :param callback: The callback to unregister.
        :type callback: function

        """

        if event in self.events:
            self.events[event].remove(callback)

            self.logger.debug(f"Unregistered {callback} from {event}")

    def emit(self, event: str, not_found_error: Optional[bool] = False,
             *args: Optional[dict],
             **kwargs: Optional[dict]) -> None:
        """
        Emit an event.

        :param event: The event to emit.
        :type event: str
        :param not_found_error: Whether to raise an error if the event fails
        :type not_found_error: bool
        :param args: The arguments to pass to the callback.
        :type args: dict
        :param kwargs: The keyword arguments to pass to the callback.
        :type kwargs: dict
        :return: None
        :rtype: None

        """

        for k, v in self.events.items():
            if fnmatch(event, k):
                for callback in v:
                    self.logger.debug(f"Emitting {event} to {callback}")
                    callback(*args, **kwargs)
        else:
            if not_found_error:
                raise Exception(f"Event {event} not found")
