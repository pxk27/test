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

import readline
from xmlrpc.client import ServerProxy


def create_config_1(gema_server: ServerProxy):
    """Creates config 1 using gema RPC methods."""
    gema_server.add_config(1)
    gema_server.set_board(1, "SimpleBoard", 3.5)
    gema_server.set_processor(1, "x86", "SimpleProcessor", "timing", 1)
    gema_server.set_memory(1, "SingleChannelDDR3_1600", 1024)
    gema_server.set_cache(1, "PrivateL1PrivateL2CacheHierarchy", 64, 64, 256)
    gema_server.set_resource(1, "x86-hello64-static")


def create_config_2(gema_server: ServerProxy):
    """Creates config 2 using gema RPC methods and a predefined dictionary."""
    example_cfg = {
        "board": {"type": "SimpleBoard", "clk": 3.0},
        "processor": {
            "isa": "x86",
            "type": "SimpleProcessor",
            "cpu": "timing",
            "ncores": 2,
        },
        "memory": {"type": "SingleChannelDDR3_1600", "size": 2048},
        "cache": {
            "type": "PrivateL1CacheHierarchy",
            "l1d_size": 64,
            "l1i_size": 64,
            "l2_size": 0,
            "l1d_assoc": 0,
            "l1i_assoc": 0,
            "l2_assoc": 0,
        },
        "resource": {"name": "x86-npb-cg-size-s"},
    }
    gema_server.add_config(2, example_cfg)


def convert_arg(arg):
    """Try to convert the argument to an appropriate type (int, float, or leave as str)."""
    try:
        return int(arg)
    except ValueError:
        try:
            return float(arg)
        except ValueError:
            return arg


def interactive_terminal(server):
    """Interactive terminal to execute remote commands."""
    print(
        "Type 'exit' to quit. Type 'history' or use the arrow keys to access command history."
    )
    print("For help, call the 'get_endpoints' method or consult the README.")

    while True:
        try:
            user_input = input("\nEnter command: ").strip()

            if user_input == "exit":
                print("Exiting the terminal.")
                break

            if user_input == "history":
                print("\nCommand History:")
                for i in range(readline.get_current_history_length()):
                    print(f"{i+1}: {readline.get_history_item(i+1)}")
                continue

            command_parts = user_input.split()
            method_name = command_parts[0]
            args = command_parts[1:]

            converted_args = [convert_arg(arg) for arg in args]
            result = getattr(server, method_name)(*converted_args)
            print(result)

        except Exception as e:
            print(f"Error: {e}")


def setup():
    port = input(
        "Enter the port number to connect to the server (default is 8000): "
    ).strip()
    if not port:
        port = 8000
    else:
        try:
            port = int(port)
        except ValueError:
            print("Invalid port number. Using default port 8000.")
            port = 8000

    host_ip = f"http://localhost:{port}"
    server = ServerProxy(host_ip)
    print("RPC Terminal connected to:", host_ip)
    return server


def main(server):
    # Ask the user which mode to operate in
    print("\nChoose the operation mode:")
    print("1. Predefined Configuration Setup")
    print("2. Interactive RPC Command Terminal")
    mode_choice = input("Choice (1 or 2): ").strip()

    if mode_choice == "1":
        # Ask the user which configuration to create
        print(
            "\nThis example demonstrates running simulations in a simple (gem5-like) script."
        )
        print("Choose the configuration method to try: ")
        print("1. RPC Functions")
        print("2. Pre-defined Dictionary Data")
        config_choice = input("Choice (1 or 2): ").strip()
        if config_choice == "1":
            create_config_1(server)
            print("Config 1 created successfully.")
            print("Starting simulation for Config 1...")
            print(server.run_simulation(1))
            print(server.manage_sim(1, "status"))
        elif config_choice == "2":
            create_config_2(server)
            print("Config 2 created successfully.")
            print("Starting simulation for Config 2...")
            print(server.run_simulation(2))
        else:
            print("Invalid configuration choice. Exiting program.")

    elif mode_choice == "2":
        interactive_terminal(server)

    else:
        print("Invalid mode choice. Exiting program.")


if __name__ == "__main__":
    server = setup()
    while True:
        main(server)
