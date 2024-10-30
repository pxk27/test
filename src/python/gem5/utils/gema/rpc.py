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
from typing import Optional
from xmlrpc.server import (
    SimpleXMLRPCRequestHandler,
    SimpleXMLRPCServer,
)


class GemaServer:
    """A server that provides XML-RPC interface to interact with gem5 configurations and simulations."""

    def __init__(self, root: Gema, port: int):
        """Initialize the GemaServer.

        Args:
            root: The root Gema instance that provides access to gem5 functionality
            port: The port number to run the server on
        """
        self.root = root
        self.port = port

    def run(self):
        """Start the XML-RPC server and register all available GemaFunctions.

        The server runs indefinitely until explicitly shut down. It provides
        introspection capabilities and serves RPC requests on localhost.
        """
        server = SimpleXMLRPCServer(
            ("localhost", self.port),
            requestHandler=RequestHandler,
            allow_none=True,
        )
        server.register_introspection_functions()
        server.register_instance(GemaFunctions(self.root))
        print(f"Starting server on port {self.port}.")
        print(
            "For help, call the 'get_endpoints' method or consult the documentation."
        )
        server.serve_forever()


class RequestHandler(SimpleXMLRPCRequestHandler):
    """Custom request handler for the XML-RPC server that restricts paths to /RPC2"""

    rpc_paths = ("/RPC2",)


class GemaFunctions:
    """Provides the XML-RPC accessible functions for interacting with gem5 configurations and simulations."""

    def __init__(self, root: Gema):
        self.root = root

    def rpc_json_response(func):
        """Decorator that converts function returns into JSON formatted responses.

        This decorator handles the serialization of complex objects (including dataclasses)
        into JSON format and provides consistent error handling for all RPC methods.

        Returns:
            str: A JSON-formatted string containing either the successful result or error details
        """
        import json
        from dataclasses import (
            asdict,
            is_dataclass,
        )
        from functools import wraps

        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                print(result)

                def convert(obj):
                    if is_dataclass(obj):
                        return asdict(obj)
                    elif isinstance(obj, list):
                        return [convert(item) for item in obj]
                    elif isinstance(obj, dict):
                        return {
                            key: convert(value) for key, value in obj.items()
                        }
                    return obj

                return json.dumps(convert(result), indent=4)

            except Exception as e:
                error_response = {
                    "status": "error",
                    "message": "Internal server error",
                    "details": str(e),
                }
                return json.dumps(error_response, indent=4)

        return wrapper

    @rpc_json_response
    def get_endpoints(self) -> dict:
        """Retrieve a comprehensive list of all available RPC endpoints and their descriptions.

        Returns:
            dict: A dictionary containing endpoint names as keys, with descriptions and parameter
                 information as values
        """
        endpoints = {
            "get_endpoints": {
                "desc": "Retrieve a comprehensive list of all available RPC endpoints and their descriptions",
                "params": None,
                "returns": "dict: Dictionary of all endpoints with descriptions and parameters",
            },
            "get_config_options": {
                "desc": "Retrieve all available configuration options and their valid values from the gem5 system",
                "params": None,
                "returns": "dict: Configuration options and their acceptable values",
            },
            "get_configs": {
                "desc": "Retrieve a list of all stored configurations in the system",
                "params": None,
                "returns": "list[GemaConfiguration]: List of all configuration objects",
            },
            "get_sims": {
                "desc": "Retrieve a list of all stored simulations in the system",
                "params": None,
                "returns": "list[GemaSimulation]: List of all simulation objects",
            },
            "manage_sim": {
                "desc": "Control a running simulation by ID or process ID",
                "params": "(id: int, cmd: str)",
                "details": {
                    "id": "Simulation ID or process ID",
                    "cmd": "Command to execute on the simulation (status, pause, resume, or kill)",
                },
                "returns": "str: Result message of the management command",
            },
            "shutdown": {
                "desc": "Gracefully terminate the gEMA server with a 1-second delay to allow response transmission",
                "params": None,
                "returns": "str: Confirmation message with process ID",
            },
            "add_config": {
                "desc": "Create a new configuration with specified ID and optional initialization data",
                "params": "(config_id: int, d_data: Optional[dict])",
                "details": {
                    "config_id": "Unique identifier for the configuration",
                    "d_data": "Optional dictionary containing initial configuration data",
                },
                "returns": "str: Success or failure message",
            },
            "set_board": {
                "desc": "Configure board parameters for a specific configuration",
                "params": "(config_id: int, type: str, clk: float)",
                "details": {
                    "config_id": "Configuration identifier",
                    "type": "Board type identifier",
                    "clk": "Clock frequency in GHz",
                },
                "returns": "str: Configuration update status",
            },
            "set_processor": {
                "desc": "Set processor configuration parameters",
                "params": "(config_id: int, isa: str, type: str, cpu: str, ncores: int)",
                "details": {
                    "config_id": "Configuration identifier",
                    "isa": "Instruction Set Architecture",
                    "type": "Processor type",
                    "cpu": "CPU model identifier",
                    "ncores": "Number of CPU cores",
                },
                "returns": "str: Configuration update status",
            },
            "set_memory": {
                "desc": "Configure memory system parameters",
                "params": "(config_id: int, type: str, size: int)",
                "details": {
                    "config_id": "Configuration identifier",
                    "type": "Memory system type",
                    "size": "Memory size in bytes",
                },
                "returns": "str: Configuration update status",
            },
            "set_cache": {
                "desc": "Configure cache hierarchy with customizable cache levels",
                "params": "(config_id: int, type: str, l1d_size: int, l1i_size: int, l2_size: Optional[int], l1d_assoc: Optional[int], l1i_assoc: Optional[int], l2_assoc: Optional[int])",
                "details": {
                    "config_id": "Configuration identifier",
                    "type": "Cache hierarchy type",
                    "l1d_size": "L1 data cache size in bytes",
                    "l1i_size": "L1 instruction cache size in bytes",
                    "l2_size": "Optional L2 cache size in bytes",
                    "l1d_assoc": "Optional L1 data cache associativity",
                    "l1i_assoc": "Optional L1 instruction cache associativity",
                    "l2_assoc": "Optional L2 cache associativity",
                },
                "returns": "str: Configuration update status",
            },
            "set_resource": {
                "desc": "Set additional resource for a specific configuration",
                "params": "(config_id: int, resource: str)",
                "details": {
                    "config_id": "Configuration identifier",
                    "resource": "Resource identifier or path",
                },
                "returns": "str: Resource update status",
            },
            "run_simulation": {
                "desc": "Start a new simulation using the specified configuration",
                "params": "(config_id: int)",
                "details": {
                    "config_id": "Identifier of the configuration to use"
                },
                "returns": "str: Simulation start status message",
            },
            "get_config_by_id": {
                "desc": "Retrieve a specific configuration by its identifier",
                "params": "(config_id: int)",
                "details": {
                    "config_id": "Identifier of the configuration to retrieve"
                },
                "returns": "Union[GemaConfiguration, str]: Configuration object or error message",
            },
            "delete_config": {
                "desc": "Remove a specific configuration from the system",
                "params": "(config_id: int)",
                "details": {
                    "config_id": "Identifier of the configuration to delete"
                },
                "returns": "str: Deletion status message",
            },
        }
        return endpoints

    @rpc_json_response
    def get_config_options(self):
        """Retrieve all available configuration options from the gem5 system.

        Returns:
            dict: A dictionary containing all valid configuration options and their acceptable values
        """
        return self.root.retriever.get_config_options()

    @rpc_json_response
    def run_simulation(self, config_id: int):
        """Start a new simulation using the specified configuration.

        Args:
            config_id: The identifier of the configuration to use for the simulation

        Returns:
            str: A message indicating whether the simulation was successfully started
        """
        if self.root.configurator._get_config_by_id(config_id) is None:
            response = f"Config with ID {config_id} does not exist."
            return response
        response = f"Starting simulation using Config ID: {config_id}"
        self.root.manager.start_subprocess(config_id)
        return response

    @rpc_json_response
    def shutdown(self):
        """Gracefully terminate the gema server process.

        Creates a new thread to handle the shutdown after a 1-second delay to allow
        the shutdown response to be sent to the client.

        Returns:
            str: A confirmation message including the process ID being terminated
        """
        import threading
        import time

        def delayed_shutdown():
            time.sleep(1)
            os._exit(0)

        response = f"Terminating gEMA server process, pid: {os.getpid()}"
        threading.Thread(target=delayed_shutdown).start()
        return response

    @rpc_json_response
    def add_config(self, config_id: int, d_data: dict | None = None):
        """Create a new GemaConfiguration with the specified ID and optional initial data.

        Args:
            config_id: The unique identifier for the new configuration
            d_data: Optional dictionary containing initial configuration data

        Returns:
            str: A message indicating success or failure of the configuration creation
        """
        if self.root.configurator.add_config(config_id, d_data) is False:
            response = f"Config with ID {config_id} already exists."
            return response

        response = f"Config with ID {config_id} has been successfully created."
        return response

    @rpc_json_response
    def delete_config(self, config_id: int):
        """Remove a GemaConfiguration from the system.

        Args:
            config_id: The identifier of the configuration to delete

        Returns:
            str: A message indicating whether the configuration was successfully deleted
        """
        if self.root.configurator.delete_config(config_id) is False:
            response = f"Config with ID {config_id} does not exist."
            return response

        response = f"Config with ID {config_id} has been successfully deleted."
        return response

    @rpc_json_response
    def set_board(self, config_id: int, type: str, clk: float):
        """Configure the board parameters for a specific configuration.

        Args:
            config_id: The identifier of the configuration to modify
            type: The type of board to configure
            clk: The clock frequency in GHz

        Returns:
            str: A message indicating whether the board configuration was successfully updated
        """
        if self.root.configurator.set_board(config_id, type, clk) is False:
            response = f"Config with ID {config_id} does not exist, or given parameter is invalid."
            return response
        response = (
            f"Board configuration updated for ID {config_id} successfully."
        )
        return response

    @rpc_json_response
    def set_processor(
        self, config_id: int, isa: str, type: str, cpu: str, ncores: int
    ):
        """Configure the processor parameters for a specific configuration.

        Args:
            config_id: The identifier of the configuration to modify
            isa: The instruction set architecture
            type: The type of processor
            cpu: The CPU model to use
            ncores: The number of CPU cores

        Returns:
            str: A message indicating whether the processor configuration was successfully updated
        """
        if (
            self.root.configurator.set_processor(
                config_id, isa, type, cpu, ncores
            )
            is False
        ):
            response = f"Config with ID {config_id} does not exist, or given parameter is invalid."
            return response
        response = (
            f"Processor configuration updated for ID {config_id} successfully."
        )
        return response

    @rpc_json_response
    def set_memory(self, config_id: int, type: str, size: int):
        """Configure the memory parameters for a specific configuration.

        Args:
            config_id: The identifier of the configuration to modify
            type: The type of memory system
            size: The size of memory in bytes

        Returns:
            str: A message indicating whether the memory configuration was successfully updated
        """
        if self.root.configurator.set_memory(config_id, type, size) is False:
            response = f"Config with ID {config_id} does not exist, or given parameter is invalid."
            return response
        response = (
            f"Memory configuration updated for ID {config_id} successfully."
        )
        return response

    @rpc_json_response
    def set_cache(
        self,
        config_id: int,
        type: str,
        l1d_size: int,
        l1i_size: int,
        l2_size: int | None = None,
        l1d_assoc: int | None = None,
        l1i_assoc: int | None = None,
        l2_assoc: int | None = None,
    ):
        """Configure the cache hierarchy for a specific configuration.

        Args:
            config_id: The identifier of the configuration to modify
            type: The type of cache hierarchy
            l1d_size: The size of the L1 data cache in bytes
            l1i_size: The size of the L1 instruction cache in bytes
            l2_size: Optional size of the L2 cache in bytes
            l1d_assoc: Optional associativity of the L1 data cache
            l1i_assoc: Optional associativity of the L1 instruction cache
            l2_assoc: Optional associativity of the L2 cache

        Returns:
            str: A message indicating whether the cache configuration was successfully updated
        """
        if (
            self.root.configurator.set_cache(
                config_id,
                type,
                l1d_size,
                l1i_size,
                l2_size,
                l1d_assoc,
                l1i_assoc,
                l2_assoc,
            )
            is False
        ):
            response = f"Config with ID {config_id} does not exist, or given parameter is invalid."
            return response
        response = (
            f"Cache configuration updated for ID {config_id} successfully."
        )
        return response

    @rpc_json_response
    def set_resource(self, config_id: int, resource: str):
        """Set a specific resource for a configuration.

        Args:
            config_id: The identifier of the configuration to modify
            resource: The resource to set

        Returns:
            str: A message indicating whether the resource was successfully updated
        """
        if self.root.configurator.set_resource(config_id, resource) is False:
            response = f"Config with ID {config_id} does not exist."
            return response
        response = f"Resource updated for ID {config_id} successfully."
        return response

    @rpc_json_response
    def get_config_by_id(self, config_id: int):
        """Retrieve a specific configuration by its ID.

        Args:
            config_id: The identifier of the configuration to retrieve

        Returns:
            Union[GemaConfiguration, str]: The requested configuration object or an error message
                                        if the configuration doesn't exist
        """
        cfg = self.root.configurator._get_config_by_id(config_id)
        if cfg != None:
            return cfg
        else:
            response = f"Config with ID {config_id} does not exist."
            return response

    @rpc_json_response
    def get_configs(self):
        """Retrieve all stored configurations.

        Returns:
            list[GemaConfiguration]: A list of all stored configuration objects
        """
        return self.root.configurator.configs

    @rpc_json_response
    def get_sims(self):
        """Retrieve all stored simulations.

        Returns:
            list[GemaSimulation]: A list of all stored simulation objects
        """
        return self.root.sims

    @rpc_json_response
    def manage_sim(self, id: int, cmd: str):
        """Manage a running simulation by ID or PID.

        Args:
            id: The simulation ID or process ID
            cmd: The command to execute on the simulation

        Returns:
            str: A message indicating the result of the management command
        """
        response = self.root.manager.manage_simulation(id, cmd)
        return response
