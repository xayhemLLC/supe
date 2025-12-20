"""Action framework for the AB kernel.

This module defines a simple registry of actions that the system can
perform as part of the cognitive cycle.  An action is a callable
that produces side effects (e.g., logging, updating state, sending
messages).  Subselves should propose actions by name, and the
Overlord will pick one based on priorities.  The cognitive pulse
can then execute the selected action via this registry.

By default, this registry contains a few trivial actions:

* ``noop``: Do nothing.
* ``print``: Print a message to standard output.
* ``log``: Create a card labeled ``"log"`` containing a message.

Actions may take parameters encoded in the action string.  The
``execute_action`` function will parse the string: the first word
is taken as the action name and the remainder is passed as a
single argument (string) to the action.  Custom actions can be
registered with additional parameter parsing if desired.
"""

from __future__ import annotations

import json
from typing import Callable, Dict, Optional, Tuple

from .abdb import ABMemory
from .models import Buffer


class Action:
    """Encapsulate a callable action.

    Each action has a name, a callable and an optional description.
    The callable should accept three arguments: ``memory`` (an
    ``ABMemory`` instance), ``arg`` (a string parameter) and
    ``owner_self`` (the identity invoking the action).  The action
    may return any result, which is ignored by the caller.
    """

    def __init__(self, name: str, func: Callable[[ABMemory, str, Optional[str]], None], description: str = "") -> None:
        self.name = name
        self.func = func
        self.description = description

    def __call__(self, memory: ABMemory, arg: str, owner_self: Optional[str] = None) -> None:
        self.func(memory, arg, owner_self)


class ActionRegistry:
    """Registry for actions keyed by name."""

    def __init__(self) -> None:
        self._registry: Dict[str, Action] = {}

    def register(self, name: str, func: Callable[[ABMemory, str, Optional[str]], None], description: str = "") -> None:
        self._registry[name] = Action(name, func, description)

    def get(self, name: str) -> Optional[Action]:
        return self._registry.get(name)

    def execute(self, memory: ABMemory, action_str: str, owner_self: Optional[str] = None) -> None:
        """Parse and execute an action string.

        The action string should start with the action name followed
        by an optional argument separated by whitespace.  For
        example: ``"print Hello world"`` will invoke the ``print``
        action with argument ``"Hello world"``.

        Unknown action names result in a no-op.
        """
        if not action_str:
            return
        parts = action_str.split(maxsplit=1)
        name = parts[0]
        arg = parts[1] if len(parts) > 1 else ""
        action = self.get(name)
        if action is None:
            # Unknown action: fallback to noop if present
            noop_action = self.get("noop")
            if noop_action:
                noop_action(memory, action_str, owner_self)
            return
        action(memory, arg, owner_self)


# Global registry instance
registry = ActionRegistry()


def _noop_action(memory: ABMemory, arg: str, owner_self: Optional[str] = None) -> None:
    """A no-op action that does nothing."""
    # Purposefully does nothing.
    return


def _print_action(memory: ABMemory, arg: str, owner_self: Optional[str] = None) -> None:
    """Print the provided argument to standard output."""
    print(arg)


def _log_action(memory: ABMemory, arg: str, owner_self: Optional[str] = None) -> None:
    """Persist a log entry as a card in AB memory.

    The ``arg`` string is stored as the payload of a buffer named
    ``"log_message"`` on a card labeled ``"log"``.  This allows
    logging to be captured in the memory ledger.
    """
    buf = Buffer(
        name="log_message",
        headers={"content_type": "text/plain"},
        payload=arg.encode("utf-8"),
        exe=None,
    )
    memory.store_card(label="log", buffers=[buf], owner_self=owner_self)


def init_default_actions() -> None:
    """Register the default actions into the global registry."""
    registry.register("noop", _noop_action, "Do nothing")
    registry.register("print", _print_action, "Print a message to stdout")
    registry.register("log", _log_action, "Store a message as a log card")


# Initialize the default actions on module import
init_default_actions()