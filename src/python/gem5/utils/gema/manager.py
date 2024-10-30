# Copyright (c) 2024 The Regents of the University of California
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

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from gem5.utils.gema import Gema

import os
import signal
from datetime import datetime
from pathlib import Path

import psutil

from gem5.simulate.simulator import Simulator
from gem5.utils.gema.rpc_data import GemaSimulation
from gem5.utils.multiprocessing import Process


class GemaSimulationManager:
    """
    A class responsible for managing gem5 simulation processes and their lifecycle.

    This manager handles simulation creation, process management, logging, and
    provides functionality to control running simulations (pause, resume, kill).
    """

    def __init__(self, root: Gema) -> None:
        self.root = root

    def _generate_log_path(self, sim_id: int, config_id: int) -> Path:
        """
        Generate a unique log directory path for a simulation.

        Args:
            sim_id: The unique identifier for the simulation
            config_id: The identifier of the configuration being simulated

        Returns:
            Path: A Path object pointing to the unique log directory for this simulation,
                 relative to the gem5 home directory
        """
        import inspect

        here = Path(inspect.getfile(inspect.currentframe())).resolve()
        gem5_home = here.parents[5]
        log_path = gem5_home / f"m5out/sim_{sim_id}_config_{config_id}"
        return log_path

    def _generate_sim_save(self, config_id: int) -> int:
        """
        Create and save a new simulation record based on a configuration.

        Creates a new GemaSimulation object with a unique ID, associates it with
        the given configuration, and stores it in the simulation history.

        Args:
            config_id: The identifier of the configuration to use for the simulation

        Returns:
            int: The newly generated simulation ID
        """
        current_sim_id = len(self.root.sims) + 1
        config = self.root.configurator._get_config_by_id(config_id)

        new_sim = GemaSimulation(
            sim_id=current_sim_id,
            config=config,
            generated_on=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            path=str(self._generate_log_path(current_sim_id, config_id)),
            pid=os.getpid(),
        )

        self.root.sims.append(new_sim)
        return current_sim_id

    def _get_simulation_by_id(
        self, sim_id: int, config_id: int
    ) -> GemaSimulation | None:
        """
        Retrieve a simulation record by its ID and configuration ID.

        Args:
            sim_id: The unique identifier of the simulation to find
            config_id: The identifier of the configuration associated with the simulation

        Returns:
            GemaSimulation|None: The matching simulation object if found, None otherwise
        """
        for sim in self.root.sims:
            if sim.sim_id == sim_id and sim.config.config_id == config_id:
                return sim
        return None

    def start_subprocess(self, config_id: int) -> None:
        """
        Launch a new gem5 simulation as a subprocess.

        Creates a new simulation record and starts it as a separate process using
        gem5's multiprocessing utilities. Updates the simulation record with the
        new process ID once started.

        Args:
            config_id: The identifier of the configuration to simulate
        """
        c_sim_id = self._generate_sim_save(config_id)
        process = Process(
            target=self.run_gem5_simulator,
            args=[c_sim_id, config_id],
            name=(f"config_{config_id}_sim_{os.getpid()}"),
        )

        current_sim = self._get_simulation_by_id(c_sim_id, config_id)
        process.start()

        if current_sim:
            current_sim.pid = process.pid

    def run_gem5_simulator(self, sim_id: int, config_id: int) -> None:
        """
        Execute a gem5 simulation with the specified configuration.

        Retrieves the simulation configuration, converts it to a gem5-compatible format,
        and runs the simulation. Outputs completion status and statistics when done.

        Args:
            sim_id: The unique identifier of the simulation to run
            config_id: The identifier of the configuration to use
        """
        current_sim = self._get_simulation_by_id(sim_id, config_id)

        if not current_sim:
            return

        gema_config = current_sim.config
        gem5_config = self.root.configurator.generate_gem5_config(gema_config)

        simulator = Simulator(board=gem5_config)
        simulator.override_outdir(Path(current_sim.path))

        simulator.run()
        print(
            f"Simulation for sim_id {sim_id} completed at tick {simulator.get_current_tick()} with exit cause: {simulator.get_last_exit_event_cause()}"
        )

    def _valid_id_or_pid(self, identifier: int) -> int | bool:
        """
        Validate and resolve a simulation identifier or process ID.

        Checks if the given identifier corresponds to either a valid simulation ID
        with an associated process ID, or directly to a valid process ID of a running
        simulation.

        Args:
            identifier: Either a simulation ID or a process ID to validate

        Returns:
            int|bool: The associated process ID if valid, False otherwise
        """
        # Check if the identifier matches a pid in any simulation
        saved_sim = next(
            (sim for sim in self.root.sims if sim.pid == identifier), None
        )
        if saved_sim:
            return identifier  # If it's a valid pid, return it

        # If not a pid, check if it's a valid sim_id with an associated pid
        saved_sim = next(
            (sim for sim in self.root.sims if sim.sim_id == identifier), None
        )
        if saved_sim and saved_sim.pid is not None:
            return (
                saved_sim.pid
            )  # If it's a valid sim_id with a pid, return the pid

        return (
            False  # Return False if neither a valid pid nor a sim_id with pid
        )

    def manage_simulation(self, identifier: int, command: str) -> str:
        """
        Control and monitor a running simulation process.

        Provides capabilities to check status, pause, resume, or terminate a running
        simulation identified either by its simulation ID or process ID.

        Args:
            identifier: Either a simulation ID or process ID of the simulation to manage
            command: The management command to execute. Valid commands are:
                    'status': Get current simulation state, runtime
                    'pause': Temporarily suspend the simulation
                    'resume': Continue a paused simulation
                    'kill': Terminate the simulation

        Returns:
            str: A message describing the result of the management command

        The status command returns:
            - Current state (running/paused/terminated)
            - Runtime duration

        Error conditions:
            - Invalid identifier: Returns "Invalid sim_id or pid"
            - Process not found: Returns "No such process; it may have already terminated"
            - Operation timeout: Returns timeout message
            - Invalid command: Returns list of valid commands
            - Other errors: Returns error description
        """
        valid_pid = self._valid_id_or_pid(identifier)
        if not valid_pid:
            return "Invalid sim_id or pid"

        try:
            process = psutil.Process(valid_pid)

            # Status Command
            if command == "status":
                status = process.status()
                start_time = datetime.fromtimestamp(process.create_time())
                runtime = datetime.now() - start_time
                state = (
                    "paused" if status == psutil.STATUS_STOPPED else "running"
                )
                if status == psutil.STATUS_ZOMBIE:
                    state = "terminated (zombie state)"
                return f"Simulation with PID {valid_pid} is {state}. Runtime: {runtime}."

            # Pause Command
            elif command == "pause":
                if process.is_running():
                    process.send_signal(signal.SIGSTOP)
                    return f"Simulation with PID {valid_pid} paused."
                return f"Simulation with PID {valid_pid} is not running."

            # Resume Command
            elif command == "resume":
                if process.status() == psutil.STATUS_STOPPED:
                    process.send_signal(signal.SIGCONT)
                    return f"Simulation with PID {valid_pid} resumed."
                return f"Simulation with PID {valid_pid} is not paused."

            # Kill Command
            elif command == "kill":
                if process.is_running():
                    process.terminate()
                    process.wait(timeout=5)
                    return f"Simulation with PID {valid_pid} terminated."
                return f"Simulation with PID {valid_pid} is not running."

            else:
                return "Invalid command. Use 'status', 'pause', 'resume', or 'kill'."

        except psutil.NoSuchProcess:
            return "No such process; it may have already terminated."
        except psutil.TimeoutExpired:
            return f"Operation on simulation with PID {valid_pid} timed out."
        except Exception as e:
            return f"An error occurred: {e}"
