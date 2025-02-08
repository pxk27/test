#!/usr/bin/env python3

# Copyright (c) 2023 The Regents of the University of California
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

"""
This module provides functionality to communicate with gem5 processes via shared memory
and signals.

The module uses logging for debug output which is disabled by default. To enable debug
logging, Set environment variable:

export PYTHONLOG=DEBUG
"""

import json
import logging
import os
import signal
import sys
from multiprocessing import shared_memory
from time import sleep
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def send_signal(pid: int, id: int, payload: str) -> None:
    """
    Sends a signal with payload to a gem5 process via shared memory.

    Args:
        pid: Process ID of the target gem5 process
        id: Message ID for the signal
        payload: String payload to send

    Raises:
        ProcessLookupError: If the specified PID does not exist
    """
    shared_mem_name = "shared_gem5_signal_mem_" + str(pid)
    shared_mem_size = 4096
    try:
        shm = shared_memory.SharedMemory(
            name=shared_mem_name, create=True, size=shared_mem_size
        )
    except FileExistsError:
        shm = shared_memory.SharedMemory(name=shared_mem_name)

    shm.buf[:shared_mem_size] = b"\x00" * shared_mem_size
    try:
        final_payload = create_json(id, payload)
        shm.buf[: len(final_payload.encode())] = final_payload.encode()
        # Note: SIGHUP is used as SIGUSR1 and SIGUSR2 are already in used by
        # gem5 for other purposes. SIGRTMIN and SIGRTMAX (usually the suggested
        # alternative when SIGUSR1 and SIGUSR2 unavailable) cannot be used in
        # this case as they are not supported on MacOS.
        #
        # SIGHUP is compatible with both Linux and MacOS and was not otherwise
        # used by gem5. In general, SIGHUP is a signal that is
        # for use in interacting with system daemons to request reloading of
        # their configurations.
        os.kill(pid, signal.SIGHUP)
    except ProcessLookupError:
        logger.error(
            "Process does not exist! Check that you are using the correct PID."
        )
        shm.close()
        shm.unlink()
        sys.exit(1)
    except json.decoder.JSONDecodeError as e:
        logger.error(
            f"JSON Parsing Error: {str(e)}\nPayload that caused error: {payload}"
        )
        shm.close()
        shm.unlink()
        sys.exit(1)
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        shm.close()
        shm.unlink()
        sys.exit(1)

    logger.info(
        f"Sent a SIGHUP signal to PID {pid} with payload: '{final_payload}'"
    )

    while bytes(shm.buf[:shared_mem_size]).decode().strip("\x00") != "done":
        logger.info("Waiting for gem5 to finish using shared memory...")
        sleep(1)
    logger.info("Done message received")
    shm.close()
    try:
        shm.unlink()
    except FileNotFoundError:
        pass


def validate_key(key: str) -> bool:
    """Validate that a key is a valid string identifier."""
    if not isinstance(key, str):
        return False
    if not key:
        return False
    # Check if key is a valid identifier (starts with letter/underscore,
    # contains only letters, numbers, underscores)
    if not key[0].isalpha() and key[0] != "_":
        return False
    return all(c.isalnum() or c == "_" for c in key)


def create_json(id: int, payload: Optional[str] = "{}") -> str:
    """
    Create a properly formatted JSON message for gem5.

    Args:
        id: Message ID (must be numeric)
        payload: JSON string containing key-value pairs

    Returns:
        Formatted JSON string

    Raises:
        ValueError: If payload format is invalid
    """
    try:
        payload_dict = json.loads(payload)

        # Ensure payload is a dictionary
        if not isinstance(payload_dict, dict):
            raise ValueError("Payload must be a dictionary/object")

        # Validate and convert all values to strings
        formatted_dict = {}
        for key, value in payload_dict.items():
            # Validate key
            if not validate_key(key):
                raise ValueError(f"Invalid key format: {key}")

            # Convert value to string
            formatted_dict[key] = str(value)

        final_dict = {
            "id": int(id),  # Ensure ID is numeric
            "payload": formatted_dict,
        }

        # Verify final size
        final_json = json.dumps(final_dict)
        if len(final_json.encode()) >= 4096:
            raise ValueError("JSON payload too large (must be < 4096 bytes)")

        return final_json

    except json.JSONDecodeError:
        raise ValueError("Invalid JSON payload format")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        logger.error("Usage: python sender.py <PID> <Hypercall ID> <Payload>")
        sys.exit(1)

    logger.debug(sys.argv)

    try:
        if len(sys.argv) == 4:
            send_signal(int(sys.argv[1]), int(sys.argv[2]), sys.argv[3])
        else:
            send_signal(int(sys.argv[1]), int(sys.argv[2]), "{}")
    except ValueError as e:
        logger.error(f"Error: {str(e)}")
        sys.exit(1)
