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

from gem5.utils.gema.options import *
from gem5.utils.gema.rpc_data import *


class GemaConfigGenerator:
    """A class responsible for creating and managing gem5 simulation configurations.

    This class provides functionality to create, modify, and generate gem5 simulation
    configurations through a high-level interface. It manages multiple configuration
    objects and provides methods to set various simulation parameters including board,
    processor, memory, and cache specifications.
    """

    def __init__(self, root: Gema):
        self.root = root
        self.configs = []

    def add_config(
        self, config_id: int, d_data: Optional[dict] = None
    ) -> bool:
        """Create and add a new simulation configuration to the manager.

        This method creates a new GemaConfiguration object with the specified ID.
        If dictionary data is provided, it will be used to populate the configuration.

        Args:
            config_id (int): Unique identifier for the new configuration.
            d_data (Optional[dict]): Dictionary containing initial configuration data.
                                   If provided, this will be used to populate the configuration.

        Returns:
            bool: True if the configuration was successfully added, False if a configuration
                 with the given ID already exists.
        """
        if self._get_config_by_id(config_id) != None:
            return False

        if d_data != None:
            self.configs.append(
                self._convert_dict_to_gema(config_id=config_id, data=d_data)
            )
        else:
            self.configs.append(GemaConfiguration(config_id=config_id))
        return True

    def _convert_dict_to_gema(
        self, config_id: int, data: dict
    ) -> GemaConfiguration:
        """Convert a dictionary representation into a GemaConfiguration object.

        This method takes a dictionary containing configuration parameters and creates
        a fully populated GemaConfiguration object with all its components.

        Args:
            config_id (int): The unique identifier for the configuration.
            data (dict): Dictionary containing configuration parameters for all components
                        (board, processor, memory, cache, and resource).

        Returns:
            GemaConfiguration: A fully populated configuration object with all specified
                             components and settings.
        """
        return GemaConfiguration(
            config_id=config_id,
            resource=data.get("resource", {}).get("name"),
            board=GemaBoard(**data.get("board", {})),
            processor=GemaProcessor(**data.get("processor", {})),
            memory=GemaMemory(**data.get("memory", {})),
            cache=GemaCache(**data.get("cache", {})),
        )

    def delete_config(self, config_id: int) -> bool:
        """Remove a configuration from the manager.

        Args:
            config_id (int): The unique identifier of the configuration to delete.

        Returns:
            bool: True if the configuration was found and deleted, False if no configuration
                 with the given ID exists.
        """
        config = self._get_config_by_id(config_id)

        if config is None:
            return False

        self.configs = [
            cfg for cfg in self.configs if cfg.config_id != config_id
        ]
        return True

    def set_board(self, config_id: int, type: str, clk: float) -> bool:
        """Configure the board settings for a specific configuration.

        Args:
            config_id (int): The unique identifier of the configuration to modify.
            type (str): The type of board to use (e.g., 'SimpleBoard', 'X86Board').
            clk (float): The clock frequency in GHz.

        Returns:
            bool: True if the board settings were successfully updated, False if the
                 configuration doesn't exist or if the clock frequency is invalid (≤ 0).
        """
        config = self._get_config_by_id(config_id)
        if config is None or clk <= 0:
            return False

        config.board = GemaBoard(type=type, clk=clk)
        return True

    def set_processor(
        self, config_id: int, isa: str, type: str, cpu: str, ncores: int
    ) -> bool:
        """Configure the processor settings for a specific configuration.

        Args:
            config_id (int): The unique identifier of the configuration to modify.
            isa (str): The instruction set architecture (e.g., 'X86', 'ARM').
            type (str): The type of processor (e.g., 'SimpleProcessor').
            cpu (str): The CPU model to use.
            ncores (int): The number of CPU cores.

        Returns:
            bool: True if the processor settings were successfully updated, False if the
                 configuration doesn't exist or if the number of cores is invalid (≤ 0).
        """
        config = self._get_config_by_id(config_id)
        if config is None or ncores <= 0:
            return False

        config.processor = GemaProcessor(
            isa=isa, type=type, cpu=cpu, ncores=ncores
        )
        return True

    def set_memory(self, config_id: int, type: str, size: int) -> bool:
        """Configure the memory settings for a specific configuration.

        Args:
            config_id (int): The unique identifier of the configuration to modify.
            type (str): The type of memory system to use.
            size (int): The size of memory in MB.

        Returns:
            bool: True if the memory settings were successfully updated, False if the
                 configuration doesn't exist or if the memory size is invalid (≤ 0).
        """
        config = self._get_config_by_id(config_id)
        if config is None or size <= 0:
            return False

        config.memory = GemaMemory(type=type, size=size)
        return True

    def set_cache(
        self,
        config_id: int,
        type: str,
        l1d_size: int,
        l1i_size: int,
        l2_size: Optional[int] = None,
        l1d_assoc: Optional[int] = None,
        l1i_assoc: Optional[int] = None,
        l2_assoc: Optional[int] = None,
    ) -> bool:
        """Configure the cache hierarchy for a specific configuration.

        This method sets up the cache hierarchy with the specified parameters. It supports
        configurations with or without L2 cache, and allows customization of cache sizes
        and associativities.

        Args:
            config_id (int): The unique identifier of the configuration to modify.
            type (str): The type of cache hierarchy (e.g., 'NoCache', 'PrivateL1CacheHierarchy').
            l1d_size (int): The size of the L1 data cache in KB.
            l1i_size (int): The size of the L1 instruction cache in KB.
            l2_size (Optional[int]): The size of the L2 cache in KB, if applicable.
            l1d_assoc (Optional[int]): The associativity of the L1 data cache.
            l1i_assoc (Optional[int]): The associativity of the L1 instruction cache.
            l2_assoc (Optional[int]): The associativity of the L2 cache, if applicable.

        Returns:
            bool: True if the cache settings were successfully updated, False if the
                 configuration doesn't exist or if the cache sizes are invalid (≤ 0).
        """
        config = self._get_config_by_id(config_id)
        if config is None or l1d_size <= 0 or l1i_size <= 0:
            return False

        config.cache = GemaCache(
            type=type,
            l1d_size=l1d_size,
            l1i_size=l1i_size,
            l2_size=l2_size,
            l1d_assoc=l1d_assoc,
            l1i_assoc=l1i_assoc,
            l2_assoc=l2_assoc,
        )
        return True

    def set_resource(self, config_id: int, resource: str) -> bool:
        """Set the simulation resource (workload) for a specific configuration.

        Args:
            config_id (int): The unique identifier of the configuration to modify.
            resource (str): The name of the resource/workload to use.

        Returns:
            bool: True if the resource was successfully set, False if the configuration
                 doesn't exist.
        """
        config = self._get_config_by_id(config_id)
        if config == None:
            return False

        config.resource = resource
        return True

    def generate_gem5_config(self, gema_obj: GemaConfiguration):
        """Generate a complete gem5 configuration from a GemaConfiguration object.

        This method creates a fully specified gem5 configuration by combining all the
        components specified in the GemaConfiguration object. It performs validation
        of all required fields and creates the appropriate gem5 objects.

        Args:
            gema_obj (GemaConfiguration): A complete GemaConfiguration object containing
                                        all necessary simulation parameters.

        Returns:
            The complete gem5 configuration object if successful, None if any validation
            fails or an error occurs during configuration generation.

        Raises:
            ValueError: If any required configuration fields are missing or invalid.
        """
        try:
            # Validate that no required fields in gema_obj are None
            if any(
                getattr(gema_obj, attr) is None
                for attr in [
                    "board",
                    "processor",
                    "memory",
                    "cache",
                    "resource",
                ]
            ):
                raise ValueError("Configuration fields must not be None")

            # Ensure all sub-fields are populated
            if (
                any(
                    getattr(gema_obj.board, attr) is None
                    for attr in ["type", "clk"]
                )
                or any(
                    getattr(gema_obj.processor, attr) is None
                    for attr in ["type", "isa", "cpu", "ncores"]
                )
                or any(
                    getattr(gema_obj.memory, attr) is None
                    for attr in ["type", "size"]
                )
            ):
                raise ValueError(
                    "Sub-fields in board, processor, or memory must not be None"
                )

            # Extract and format configuration fields
            brd = eval(gema_obj.board.type)
            clk = f"{gema_obj.board.clk}GHz"
            proc = eval(gema_obj.processor.type)
            cpu_type = CPUTypes[gema_obj.processor.cpu.upper()]
            isa = ISA[gema_obj.processor.isa.upper()]
            ncores = gema_obj.processor.ncores
            mem_type = eval(gema_obj.memory.type)
            msize = f"{gema_obj.memory.size}MB"
            cache = self.get_cache_configuration(gema_obj.cache)

            # Check that cache configuration is not None
            if cache is None:
                raise ValueError(
                    "Cache configuration is invalid or incomplete"
                )

            # Create and return the gem5 configuration
            configuration = brd(
                clk_freq=clk,
                processor=proc(cpu_type=cpu_type, isa=isa, num_cores=ncores),
                memory=mem_type(size=msize),
                cache_hierarchy=cache,
            )
            configuration.set_se_binary_workload(
                obtain_resource(gema_obj.resource)
            )

            return configuration

        except ValueError as ve:
            print(f"Configuration Error: {ve}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

    def get_cache_configuration(self, cache_config: GemaCache):
        """Create a gem5 cache hierarchy object from a GemaCache configuration.

        This method translates the cache configuration parameters into a gem5 cache
        hierarchy object, handling different cache types and their parameters.

        Args:
            cache_config (GemaCache): The cache configuration object containing all
                                    cache hierarchy parameters.

        Returns:
            A gem5 cache hierarchy object if successful, None if the configuration is
            invalid or an error occurs during creation.
        """
        try:
            cache_class = globals()[cache_config.type]
            init_params = {
                "l1d_size": f"{cache_config.l1d_size}KiB",
                "l1i_size": f"{cache_config.l1i_size}KiB",
                "l2_size": (
                    f"{cache_config.l2_size}KiB"
                    if cache_config.l2_size
                    else None
                ),
                "l1d_assoc": cache_config.l1d_assoc or None,
                "l1i_assoc": cache_config.l1i_assoc or None,
                "l2_assoc": cache_config.l2_assoc or None,
            }
            valid_params = {
                key: value
                for key, value in init_params.items()
                if value is not None
            }
            cache_object = cache_class(**valid_params)

            return cache_object
        except (KeyError, ValueError, TypeError):
            return None

    def _get_config_by_id(self, config_id: int) -> Optional[GemaConfiguration]:
        """Retrieve a configuration object by its ID.

        Args:
            config_id (int): The unique identifier of the configuration to retrieve.

        Returns:
            Optional[GemaConfiguration]: The configuration object if found, None otherwise.
        """
        for cfg in self.configs:
            if cfg.config_id == config_id:
                return cfg
        return None
