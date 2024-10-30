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

"""gem5 External Modules API (gEMA)

This module provides the main interface for managing gem5 simulations through a
remote API. It coordinates configuration generation, option discovery,
simulation management, and remote procedure calls through a unified interface.

"""

__version__ = "1.0"
__all__ = ["Gema"]

from gem5.utils.gema.config import GemaConfigGenerator
from gem5.utils.gema.manager import GemaSimulationManager
from gem5.utils.gema.options import GemaOptionRetreiver
from gem5.utils.gema.rpc import GemaServer


class Gema:
    """Main application class for the gem5 External Modules API (gEMA).

    This class serves as the central coordinator for all gEMA functionality,
    integrating configuration management, option discovery, simulation control,
    and RPC services. It provides a unified interface for managing gem5
    simulations through its component classes.

    Attributes:
        configurator (GemaConfigGenerator): Handles creation and management of
            simulation configurations.
        retriever (GemaOptionRetreiver): Dynamically fetches available simulation options.
        manager (GemaSimulationManager): Controls simulation execution and
            lifecycle management.
        server (GemaServer): Provides RPC interface for remote control and
            monitoring.
        sims (list): Maintains list of active simulation instances.

    Note:
        The Gema class follows a composition pattern, delegating specific
        functionality to specialized component classes while maintaining
        centralized coordination.
    """

    def __init__(self, port: int):
        """Initialize a new gEMA instance.

        Creates and initializes all component managers and controllers needed
        for gem5 simulation management. Sets up the RPC server for remote
        access on the specified port.

        Args:
            port (int): Network port number for the RPC server. This port
                must be available for the server to start successfully.
        """
        self.configurator = GemaConfigGenerator(self)
        self.retriever = GemaOptionRetreiver(self)
        self.manager = GemaSimulationManager(self)
        self.server = GemaServer(self, port)
        self.sims = []

    def run(self):
        """Start the gEMA instance and begin serving requests.

        This method initiates the RPC server and begins processing client
        requests. It runs indefinitely until interrupted or explicitly
        stopped.

        Note:
            This is a blocking call - the method will not return until the
            server is shut down. The server can be interrupted with Ctrl+C
            or by sending a termination signal to the process.
        """
        self.server.run()
