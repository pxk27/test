# Copyright (c) 2023-2025 The Regents of the University of California
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
This script is based on
configs/example/gem5_library/x86-ubuntu-run-with-kvm-no-perf.py

This test runs an X86 Ubuntu 24.04 boot for 15 billion ticks. It resets at 15
billion ticks, then dumps the stats. With the exception of a few stats that
should not be reset with m5.stats.reset(), all stats should have a value
of 0, nan, or simply not be present. We also check that no new stats appear
when you reset compared to when you don't.

We skip over stats that have values of 0 in the run that doesn't reset, as we
cannot tell whether the stat has reset or not.

"""
import math
import sys

import m5

from gem5.components.boards.x86_board import X86Board
from gem5.components.processors.cpu_types import CPUTypes
from gem5.components.processors.simple_switchable_processor import (
    SimpleSwitchableProcessor,
)
from gem5.isas import ISA
from gem5.resources.resource import obtain_resource
from gem5.simulate.exit_event import ExitEvent
from gem5.simulate.simulator import Simulator
from gem5.utils.requires import requires

requires(
    isa_required=ISA.X86,
)

from gem5.components.cachehierarchies.classic.private_l1_shared_l2_cache_hierarchy import (
    PrivateL1SharedL2CacheHierarchy,
)

cache_hierarchy = PrivateL1SharedL2CacheHierarchy(
    l1d_size="64KiB", l1i_size="64KiB", l2_size="1MiB"
)

from gem5.components.memory import DualChannelDDR4_2400

memory = DualChannelDDR4_2400(size="3GiB")

processor = SimpleSwitchableProcessor(
    starting_core_type=CPUTypes.ATOMIC,
    switch_core_type=CPUTypes.TIMING,
    isa=ISA.X86,
    num_cores=2,
)

board = X86Board(
    clk_freq="3GHz",
    processor=processor,
    memory=memory,
    cache_hierarchy=cache_hierarchy,
)

workload = obtain_resource("x86-ubuntu-24.04-boot-with-systemd")
board.set_workload(workload)


def max_tick_handler_end_reset():
    m5.stats.reset()
    m5.stats.dump()
    yield True


simulator = Simulator(
    board=board,
    on_exit_event={
        ExitEvent.MAX_TICK: max_tick_handler_end_reset(),
    },
)

simulator.set_max_ticks(15_000_000_000)  # 15 ms
simulator.run()

end_reset_dict = {}
no_reset_dict = {}


def read_stats_files(filepath: str, stats_dict: dict) -> None:
    with open(filepath) as stats:
        for line in stats:
            tmp = line.split()
            if len(tmp) > 1:
                stats_dict[tmp[0]] = tmp[1]
    stats_dict.pop("----------", None)


read_stats_files("./gem5/stats-reset/base-case-stats.txt", no_reset_dict)
read_stats_files(f"{m5.options.outdir}/stats.txt", end_reset_dict)

# These stats are either constant, should carry over across resets, or have to
# do with the host
exclude_from_check = [
    "finalTick",
    "simFreq",
    "hostSeconds",
    "hostMemory",
    "UNDEFINED",
    "clk_domain",
    "peakBW",
]

# These are the stats that don't reset when m5.stats.reset() is called, and
# which I don't know if they are supposed to reset
# idleFraction is in the uncertain list because it could be calculated from the
# total number of ticks instead of the number of ticks elapsed between resets.
uncertain_exclude_from_check = [
    "tagsInUse",
    "occupancies",
    "occupanciesTaskId",
    "avgOccs",
    "ageTaskId_1024",
    "ratioOccsTaskId",
    "pwrStateTime",
    "pwrStateResidencyTicks",
    "idleFraction",
    "notIdleFraction",
]


def is_excluded(key: str) -> bool:
    return bool(
        set(key.replace("::", ".").split(".")).intersection(
            set(exclude_from_check + uncertain_exclude_from_check)
        )
    )


not_reset_properly = {}
missing_keys = {}

# If a stat is present when you reset but isn't there if you don't reset,
# something is wrong
for key, value in end_reset_dict.items():
    if key not in no_reset_dict and not (
        math.isnan(float(value))
        or float(value) == 0.0
        and not is_excluded(key)
    ):
        missing_keys[key] = value

for key, value in end_reset_dict.items():
    # Get stats that weren't reset properly.
    if value != "nan" and float(value) != 0.0 and not is_excluded(key):
        not_reset_properly[key] = value


def print_failed_stats(fail_dict: dict, message: str) -> None:
    if fail_dict:
        print(f"{len(fail_dict)} {message}")
        for key in fail_dict:
            print(key)


print_failed_stats(not_reset_properly, "incorrectly reset stats:")
print_failed_stats(
    missing_keys, "stats in test stats.txt but not in reference stats.txt:"
)

if missing_keys or not_reset_properly:
    sys.exit(1)
