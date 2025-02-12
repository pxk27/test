# Copyright (c) 2021 The Univerity of Texas at Austin
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
This script boots with KVM then switches processors and exits.
"""

import argparse

import m5
from m5.objects import Root

from gem5.coherence_protocol import CoherenceProtocol
from gem5.components.boards.arm_board import ArmBoard
from gem5.components.boards.riscv_board import RiscvBoard
from gem5.components.boards.x86_board import X86Board
from gem5.components.memory import SingleChannelDDR3_1600
from gem5.components.processors.cpu_types import (
    CPUTypes,
    get_cpu_type_from_str,
    get_cpu_types_str_set,
)
from gem5.components.processors.simple_switchable_processor import (
    SimpleSwitchableProcessor,
)
from gem5.isas import (
    ISA,
    get_isa_from_str,
)
from gem5.resources.resource import obtain_resource
from gem5.runtime import get_runtime_coherence_protocol
from gem5.simulate.exit_event import ExitEvent
from gem5.simulate.simulator import Simulator
from gem5.utils.requires import requires

parser = argparse.ArgumentParser(
    description="A script to test switching cpus. This test boots"
    "the linux kernel with the KVM cpu, then switches cpus until exiting."
)
parser.add_argument(
    "-m",
    "--mem-system",
    type=str,
    choices=("classic", "mi_example", "mesi_two_level"),
    required=True,
    help="The memory system.",
)
parser.add_argument(
    "-n",
    "--num-cpus",
    type=int,
    choices=(1, 2, 4, 8),
    required=True,
    help="The number of CPUs.",
)
parser.add_argument(
    # "-c",
    "--start-cpu",
    type=str,
    choices=get_cpu_types_str_set(),
    required=True,
    help="The starting CPU type.",
)
parser.add_argument(
    "--end-cpu",
    type=str,
    choices=get_cpu_types_str_set(),
    required=True,
    help="The end CPU type.",
)
parser.add_argument(
    "-r",
    "--resource-directory",
    type=str,
    required=False,
    help="The directory in which resources will be downloaded or exist.",
)
parser.add_argument(
    "-k",
    "--kernel-args",
    type=str,
    # default="init=/root/gem5_init.sh",
    help="Additional kernel boot arguments.",
)

parser.add_argument(
    "--isa",
    type=str,
    required=True,
    help="The ISA",
    choices=["X86", "ARM", "RISCV"],
)

args = parser.parse_args()

coherence_protocol_required = None
if args.mem_system == "mi_example":
    coherence_protocol_required = CoherenceProtocol.MI_EXAMPLE
elif args.mem_system == "mesi_two_level":
    coherence_protocol_required = CoherenceProtocol.MESI_TWO_LEVEL

if args.isa == "X86":
    requires(
        isa_required=ISA.X86,
    )
elif args.isa == "ARM":
    requires(
        isa_required=ISA.ARM,
    )
else:
    requires(
        isa_required=ISA.RISCV,
    )
requires(coherence_protocol_required=coherence_protocol_required)


cache_hierarchy = None
if args.mem_system == "mi_example":
    from gem5.components.cachehierarchies.ruby.mi_example_cache_hierarchy import (
        MIExampleCacheHierarchy,
    )

    cache_hierarchy = MIExampleCacheHierarchy(size="32KiB", assoc=8)
elif args.mem_system == "mesi_two_level":
    from gem5.components.cachehierarchies.ruby.mesi_two_level_cache_hierarchy import (
        MESITwoLevelCacheHierarchy,
    )

    cache_hierarchy = MESITwoLevelCacheHierarchy(
        l1d_size="16KiB",
        l1d_assoc=8,
        l1i_size="16KiB",
        l1i_assoc=8,
        l2_size="256KiB",
        l2_assoc=16,
        num_l2_banks=1,
    )
elif args.mem_system == "classic":
    from gem5.components.cachehierarchies.classic.private_l1_cache_hierarchy import (
        PrivateL1CacheHierarchy,
    )

    cache_hierarchy = PrivateL1CacheHierarchy(
        l1d_size="16KiB", l1i_size="16KiB"
    )
else:
    raise NotImplementedError(
        f"Memory system '{args.mem_system}' is not supported in the boot tests."
    )

assert cache_hierarchy != None

# Setup the system memory.
memory = SingleChannelDDR3_1600(size="3GiB")

# Setup a Processor.
processor = SimpleSwitchableProcessor(
    starting_core_type=get_cpu_type_from_str(args.start_cpu),
    switch_core_type=get_cpu_type_from_str(args.end_cpu),
    isa=get_isa_from_str(args.isa),
    num_cores=args.num_cpus,
)

if args.isa == "X86":
    # Setup the board.
    board = X86Board(
        clk_freq="3GHz",
        processor=processor,
        memory=memory,
        cache_hierarchy=cache_hierarchy,
    )

    # kernel_args = board.get_default_kernel_args() + [args.kernel_args]

    # Set the Full System workload.
    # board.set_kernel_disk_workload(
    #     kernel=obtain_resource(
    #         "x86-linux-kernel-5.4.0-105-generic",
    #         resource_directory=args.resource_directory,
    #         resource_version="1.0.0",
    #     ),
    #     disk_image=obtain_resource(
    #         "x86-ubuntu-24.04-img",
    #         resource_directory=args.resource_directory,
    #         resource_version="1.0.0",
    #     ),
    #     # The first exit signals to switch processors.
    #     # readfile_contents="m5 exit\nm5 exit\n",
    #     kernel_args=[
    #         "earlyprintk=ttyS0",
    #         "console=ttyS0",
    #         "lpj=7999923",
    #         "root=/dev/sda2",
    #         "no_systemd=true"
    #     ],
    # )

    board.set_workload(obtain_resource("x86-ubuntu-24.04-boot-no-systemd"))

elif args.isa == "ARM":
    # Setup the board.
    board = ArmBoard(
        clk_freq="3GHz",
        processor=processor,
        memory=memory,
        cache_hierarchy=cache_hierarchy,
    )

    # kernel_args = board.get_default_kernel_args() + [args.kernel_args]

    # Set the Full System workload.
    # board.set_kernel_disk_workload(
    #     kernel=obtain_resource(
    #         "arm64-linux-kernel-5.4.49",
    #         resource_directory=args.resource_directory,
    #         resource_version="1.0.0",
    #     ),
    #     disk_image=obtain_resource(
    #         "arm-ubuntu-24.04-img",
    #         resource_directory=args.resource_directory,
    #         resource_version="2.0.0",
    #     ),
    #     # The first exit signals to switch processors.
    #     bootloader=obtain_resource(
    #         "arm64-bootloader-foundation",
    #         resource_directory=args.resource_directory,
    #         resource_version="1.0.0"
    #     ),
    #     kernel_args=[
    #         "console=ttyAMA0",
    #         "lpj=19988480",
    #         "norandmaps",
    #         "root=/dev/vda2",
    #         "rw",
    #         "no_systemd=true"
    #     ]
    # )

    board.set_workload(obtain_resource("arm-ubuntu-24.04-boot-no-systemd"))
else:  # RISCV
    board = RiscvBoard(
        clk_freq="3GHz",
        processor=processor,
        memory=memory,
        cache_hierarchy=cache_hierarchy,
    )
    # kernel_args = board.get_default_kernel_args() + [args.kernel_args]

    # board.set_kernel_disk_workload(
    # kernel=obtain_resource(
    #     "riscv-linux-6.6.33-kernel",
    #     resource_directory=args.resource_directory,
    #     resource_version="1.0.0",
    # ),
    # disk_image=obtain_resource(
    #     "riscv-ubuntu-24.04-img",
    #     resource_directory=args.resource_directory,
    #     resource_version="1.0.0",
    # ),
    # # The first exit signals to switch processors.
    # bootloader=obtain_resource(
    #     "riscv-bootloader-opensbi-1.3.1",
    #     resource_directory=args.resource_directory,
    #     resource_version="1.0.0"
    # ),
    # kernel_args=[
    #         "console=ttyS0",
    #         "root=/dev/vda1",
    #         "rw",
    #         "no_systemd=true"
    #     ],
    # )

    board.set_workload(obtain_resource("riscv-ubuntu-24.04-boot-no-systemd"))


# Begin running of the simulation. This will exit once the Linux system boot
# is complete.
print("Running with ISA: " + processor.get_isa().name)
print("Running with protocol: " + get_runtime_coherence_protocol().name)


def exit_event_handler():
    processor.switch()  # switch processor after the first exit event, which takes place when the kernel is finished booting
    yield False
    yield True


simulator = Simulator(
    board=board,
    on_exit_event={
        # When we reach the first exit, we switch cores. For the second exit we
        # simply exit the simulation (default behavior).
        ExitEvent.EXIT: exit_event_handler()
    },
    # This parameter allows us to state the expected order-of-execution.
    # That is, we expect two exit events. If anyother event is triggered, an
    # exeception will be thrown.
    expected_execution_order=[ExitEvent.EXIT, ExitEvent.EXIT],
)

simulator.run()

print(
    "Exiting @ tick {} because {}.".format(
        simulator.get_current_tick(), simulator.get_last_exit_event_cause()
    )
)
