# Copyright (c) 2025  The Regents of the University of California
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met: redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer;
# redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution;
# neither the name of the copyright holders nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from abc import (
    ABCMeta,
    abstractmethod,
)
from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    Generator,
    List,
    Optional,
    Type,
    Union,
)

import m5
from m5 import options
from m5.util import warn

from gem5.simulate.exit_event import ExitEvent
from gem5.utils.override import overrides

from .exit_event_generators import (
    dump_stats_generator,
    exit_generator,
    reset_stats_generator,
    save_checkpoint_generator,
    skip_generator,
    spatter_exit_generator,
    switch_generator,
    warn_default_decorator,
)


class ExitHandlerMeta(ABCMeta):
    """Metaclass for ExitHandler that automatically registers subclasses"""

    def __new__(mcs, name, bases, attrs, hypercall_num: int = None) -> Any:
        cls = super().__new__(mcs, name, bases, attrs)
        # Don't register the base ExitHandler class itself
        if name != "ExitHandler":
            # Extract ID from class name, e.g. CheckpointExitHandler -> Checkpoint
            assert (
                hypercall_num is not None
            ), f"Hypercall number must be provided for {name}. Use "
            "`class {name}(ExitHandler, hypercall_num={hypercall_num}):`"
            ExitHandler._handler_map[hypercall_num] = cls

        return cls


class ExitHandler(metaclass=ExitHandlerMeta):

    _handler_map: Dict[str, Type["ExitHandler"]] = {}

    @classmethod
    def get_handler_id(cls) -> int:
        """Returns the ID of the exit handler"""
        return cls._handler_id

    @classmethod
    def get_handler_map(cls) -> Dict[str, Type["ExitHandler"]]:
        """Returns the mapping of exit handler IDs to handler classes"""
        return cls._handler_map

    def __init__(self, payload: Dict[str, str]) -> None:
        self._payload = payload

    def handle(self, simulator: "Simulator") -> bool:
        self._process(simulator)
        return self._exit_simulation()

    @abstractmethod
    def _process(self, simulator: "Simulator") -> None:
        raise NotImplementedError(
            "Method '_process' must be implemented by a subclass"
        )

    @abstractmethod
    def _exit_simulation(self) -> bool:
        raise NotImplementedError(
            "Method '_exit_simulation' must be implemented by a subclass"
        )


class ScheduledExitEventHandler(ExitHandler, hypercall_num=6):
    """A handler designed to be the default for  an Exit scheduled to occur
    at a specified tick. For example, these Exit exits can be triggered through be
    src/python/m5/simulate.py's `scheduleTickExitFromCurrent` and
    `scheduleTickExitAbsolute` functions.

    It will exit the simulation loop by default.

    The `justification` and `scheduled_at_tick` methods are provided to give
    richer information about this schedule exit.
    """

    @overrides(ExitHandler)
    def _process(self, simulator: "Simulator") -> None:
        pass

    def justification(self) -> Optional[str]:
        """Returns the justification for the scheduled exit event.

        This information may be passed to when scheduling the event event to
        remind the user why the event was scheduled, or used in cases where
        lots of scheduled events are used and there is a need to differentiate
        them.

        Returns "None" if this information was not set.
        """
        return (
            None
            if "justification" not in self._payload
            else self._payload["justification"]
        )

    def scheduled_at_tick(self) -> Optional[int]:
        """Returns the tick in which the event was scheduled on (not scheduled
        to occur, but the tick the event was created).

        Returns "None" if this information is not available.
        """
        return (
            None
            if "scheduled_at_tick" not in self._payload
            else int(self._payload["scheduled_at_tick"])
        )

    @overrides(ExitHandler)
    def _exit_simulation(self) -> bool:
        return True


class KernelBootedExitHandler(ExitHandler, hypercall_num=1):
    @overrides(ExitHandler)
    def _process(self, simulator: "Simulator") -> None:
        pass

    @overrides(ExitHandler)
    def _exit_simulation(self) -> bool:
        return False


class AfterBootExitHandler(ExitHandler, hypercall_num=2):
    @overrides(ExitHandler)
    def _process(self, simulator: "Simulator") -> None:
        pass

    @overrides(ExitHandler)
    def _exit_simulation(self) -> bool:
        return False


class AfterBootScriptExitHandler(ExitHandler, hypercall_num=3):
    @overrides(ExitHandler)
    def _process(self, simulator: "Simulator") -> None:
        pass

    @overrides(ExitHandler)
    def _exit_simulation(self) -> bool:
        return True


class ToTickExitHandler(ExitHandler, hypercall_num=5):
    @overrides(ExitHandler)
    def _process(self, simulator: "Simulator") -> None:
        pass

    @overrides(ExitHandler)
    def _exit_simulation(self) -> bool:
        return True


class CheckpointExitHandler(ExitHandler, hypercall_num=7):
    @overrides(ExitHandler)
    def _process(self, simulator: "Simulator") -> None:
        checkpoint_dir = simulator._checkpoint_path
        if not checkpoint_dir:
            checkpoint_dir = options.outdir
        m5.checkpoint(
            (Path(checkpoint_dir) / f"cpt.{str(m5.curTick())}").as_posix()
        )

    @overrides(ExitHandler)
    def _exit_simulation(self) -> bool:
        return False


class WorkBeginExitHandler(ExitHandler, hypercall_num=4):
    @overrides(ExitHandler)
    def _process(self, simulator: "Simulator") -> None:
        m5.stats.reset()

    @overrides(ExitHandler)
    def _exit_simulation(self) -> bool:
        return False


class WorkEndExitHandler(ExitHandler, hypercall_num=5):
    @overrides(ExitHandler)
    def _process(self, simulator: "Simulator") -> None:
        m5.stats.dump()

    @overrides(ExitHandler)
    def _exit_simulation(self) -> bool:
        return False

class ClassicGeneratorExitHandler(ExitHandler, hypercall_num=0):
    """A handler designed to be the default for the classic exit event.

    ``on_exit_event`` usage notes
    ---------------------------

    With Generators
    ===============

    The ``on_exit_event`` parameter specifies a Python generator for each
    exit event. `next(<generator>)` is run each time an exit event. The
    generator may yield a boolean. If this value of this boolean is ``True``
    the Simulator run loop will exit, otherwise
    the Simulator run loop will continue execution. If the generator has
    finished (i.e. a ``StopIteration`` exception is thrown when
    ``next(<generator>)`` is executed), then the default behavior for that
    exit event is run.

    As an example, a user may specify their own exit event setup like so:

    .. code-block::

        def unique_exit_event():
            processor.switch()
            yield False
            m5.stats.dump()
            yield False
            yield True

        simulator = Simulator(
            board=board
            on_exit_event = {
                ExitEvent.Exit : unique_exit_event(),
            },
        )


    This will execute ``processor.switch()`` the first time an exit event is
    encountered, will dump gem5 statistics the second time an exit event is
    encountered, and will terminate the Simulator run loop the third time.

    With a list of functions
    ========================

    Alternatively, instead of passing a generator per exit event, a list of
    functions may be passed. Each function must take no mandatory arguments
    and return True if the simulator is to exit after being called.

    An example:

    .. code-block::

        def stop_simulation() -> bool:
            return True

        def switch_cpus() -> bool:
            processor.switch()
            return False

        def print_hello() -> None:
            # Here we don't explicitly return a boolean, but the simulator
            # treats a None return as False. Ergo the Simulation loop is not
            # terminated.
            print("Hello")


        simulator = Simulator(
            board=board,
            on_exit_event = {
                ExitEvent.Exit : [
                    print_hello,
                    switch_cpus,
                    print_hello,
                    stop_simulation
                ],
            },
        )


    Upon each ``EXIT`` type exit event the list will function as a queue,
    with the top function of the list popped and executed. Therefore, in
    this example, the first ``EXIT`` type exit event will cause ``print_hello``
    to be executed, and the second ``EXIT`` type exit event will cause the
    ``switch_cpus`` function to run. The third will execute ``print_hello``
    again before finally, on the forth exit event will call
    ``stop_simulation`` which will stop the simulation as it returns ``False``.

    With a function
    ===============
    A single function can be passed. In this case every exit event of that
    type will execute that function every time. The function should not
    accept any mandatory parameters and return a boolean specifying if the
    simulation loop should end after it is executed.
    An example:

    .. code-block::

        def print_hello() -> bool:
            print("Hello")
            return False
        simulator = Simulator(
            board=board,
            on_exit_event = {
                ExitEvent.Exit : print_hello
            },
        )

    The above will print "Hello" on every ``Exit`` type Exit Event. As the
    function returns False, the simulation loop will not end on these
    events.


    Exit Event defaults
    ===================

    Each exit event has a default behavior if none is specified by the
    user. These are as follows:

        * ExitEvent.EXIT:  exit simulation
        * ExitEvent.CHECKPOINT: take a checkpoint
        * ExitEvent.FAIL : exit simulation
        * ExitEvent.SWITCHCPU: call ``switch`` on the processor
        * ExitEvent.WORKBEGIN: reset stats
        * ExitEvent.WORKEND: dump stats
        * ExitEvent.USER_INTERRUPT: exit simulation
        * ExitEvent.MAX_TICK: exit simulation
        * ExitEvent.SCHEDULED_TICK: exit simulation
        * ExitEvent.SIMPOINT_BEGIN: reset stats
        * ExitEvent.MAX_INSTS: exit simulation

    These generators can be found in the ``exit_event_generator.py`` module.
    """

    def __init__(self, payload: Dict[str, str]) -> None:
        super().__init__(payload)
        self._exit_on_completion = None

    @classmethod
    def set_exit_event_map(
        cls,
        on_exit_event: Optional[
            Dict[
                ExitEvent,
                Union[
                    Generator[Optional[bool], None, None],
                    List[Callable],
                    Callable,
                ],
            ]
        ],
        expected_execution_order: Optional[List[ExitEvent]],
        board: Optional["Board"],
    ) -> None:
        # We specify a dictionary here outlining the default behavior for each
        # exit event. Each exit event is mapped to a generator.
        cls._default_on_exit_dict = {
            ExitEvent.EXIT: exit_generator(),
            ExitEvent.CHECKPOINT: warn_default_decorator(
                save_checkpoint_generator,
                "checkpoint",
                "creating a checkpoint and continuing",
            )(),
            ExitEvent.FAIL: exit_generator(),
            ExitEvent.SPATTER_EXIT: warn_default_decorator(
                spatter_exit_generator,
                "spatter exit",
                "dumping and resetting stats after each sync point. "
                "Note that there will be num_cores*sync_points spatter_exits.",
            )(spatter_gen=board.get_processor()),
            ExitEvent.SWITCHCPU: warn_default_decorator(
                switch_generator,
                "switch CPU",
                "switching the CPU type of the processor and continuing",
            )(processor=board.get_processor()),
            ExitEvent.WORKBEGIN: warn_default_decorator(
                reset_stats_generator,
                "work begin",
                "resetting the stats and continuing",
            )(),
            ExitEvent.WORKEND: warn_default_decorator(
                dump_stats_generator,
                "work end",
                "dumping the stats and continuing",
            )(),
            ExitEvent.USER_INTERRUPT: exit_generator(),
            ExitEvent.MAX_TICK: exit_generator(),
            ExitEvent.SCHEDULED_TICK: exit_generator(),
            ExitEvent.SIMPOINT_BEGIN: warn_default_decorator(
                skip_generator,
                "simpoint begin",
                "resetting the stats and continuing",
            )(),
            ExitEvent.MAX_INSTS: warn_default_decorator(
                exit_generator,
                "max instructions",
                "exiting the simulation",
            )(),
            ExitEvent.KERNEL_PANIC: exit_generator(),
            ExitEvent.KERNEL_OOPS: exit_generator(),
        }

        if on_exit_event:
            cls._on_exit_event = {}
            for key, value in on_exit_event.items():
                if isinstance(value, Generator):
                    cls._on_exit_event[key] = value
                elif isinstance(value, List):
                    # In instances where we have a list of functions, we
                    # convert this to a generator.
                    cls._on_exit_event[key] = (func() for func in value)
                elif isinstance(value, Callable):
                    # In instances where the user passes a lone function, the
                    # function is called on every exit event of that type. Here
                    # we convert the function into an infinite generator.

                    # We check if the function is a generator. If it is we
                    # throw a warning as this is likely a mistake.
                    import inspect

                    if inspect.isgeneratorfunction(value):
                        warn(
                            f"Function passed for '{key.value}' exit event "
                            "is not a generator but a function that returns "
                            "a generator. Did you mean to do this? (e.g., "
                            "did you mean `ExitEvent.EVENT : gen()` instead "
                            "of `ExitEvent.EVENT : gen`)"
                        )

                    def function_generator(func: Callable):
                        while True:
                            yield func()

                    cls._on_exit_event[key] = function_generator(func=value)
                else:
                    raise Exception(
                        f"`on_exit_event` for '{key.value}' event is "
                        "not a Generator or List[Callable]."
                    )
        else:
            cls._on_exit_event = cls._default_on_exit_dict

        cls._expected_execution_order = expected_execution_order

    @overrides(ExitHandler)
    def _process(self, simulator: "Simulator") -> None:
        #  # Translate the exit event cause to the exit event enum.
        exit_enum = ExitEvent.translate_exit_status(
            simulator.get_last_exit_event_cause()
        )

        # Check to see the run is corresponding to the expected execution
        # order (assuming this check is demanded by the user).
        if self._expected_execution_order:
            expected_enum = self._expected_execution_order[
                simulator._exit_event_count
            ]
            if exit_enum.value != expected_enum.value:
                raise Exception(
                    f"Expected a '{expected_enum.value}' exit event but a "
                    f"'{exit_enum.value}' exit event was encountered."
                )

        # Record the current tick and exit event enum.
        simulator._tick_stopwatch.append(
            (exit_enum, simulator.get_current_tick())
        )

        try:
            # If the user has specified their own generator for this exit
            # event, use it.
            self._exit_on_completion = next(self._on_exit_event[exit_enum])
        except StopIteration:
            # If the user's generator has ended, throw a warning and use
            # the default generator for this exit event.
            warn(
                "User-specified generator/function list for the exit "
                f"event'{exit_enum.value}' has ended. Using the default "
                "generator."
            )
            self._exit_on_completion = next(
                self._default_on_exit_dict[exit_enum]
            )

        except KeyError:
            # If the user has not specified their own generator for this
            # exit event, use the default.
            self._exit_on_completion = next(
                self._default_on_exit_dict[exit_enum]
            )

    @overrides(ExitHandler)
    def _exit_simulation(self) -> bool:
        assert (
            self._exit_on_completion is not None
        ), "Exit on completion boolean var is not set."
        return self._exit_on_completion
