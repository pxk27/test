from gem5.components.boards.simple_board import SimpleBoard
from gem5.components.cachehierarchies.classic.no_cache import NoCache
from gem5.components.cachehierarchies.classic.private_l1_private_l2_cache_hierarchy import PrivateL1PrivateL2CacheHierarchy
from gem5.components.memory.single_channel import SingleChannelDDR4_2400
from gem5.components.processors.cpu_types import CPUTypes
from gem5.components.processors.simple_processor import SimpleProcessor
from gem5.isas import ISA
from gem5.resources.resource import BinaryResource
from gem5.simulate.simulator import Simulator

cache_enabled = (input("Configure system with cache?: ").lower() == "yes")
if cache_enabled:
    cache_hierarchy = PrivateL1PrivateL2CacheHierarchy(
        l1d_size="16kB",
        l1i_size="64kB",
        l2_size="256kB",
    )
else:
    cache_hierarchy = NoCache()

# Give ourselves 4GB of the best DDR4 the simulator has to offer
memory = SingleChannelDDR4_2400(size="4GB")

# X86 CPU
processor = SimpleProcessor(cpu_type=CPUTypes.TIMING, isa=ISA.X86, num_cores=1)

board = SimpleBoard(
    clk_freq="3GHz",
    processor=processor,
    memory=memory,
    cache_hierarchy=cache_hierarchy,
)

binary = BinaryResource(local_path="tests/test-progs/sum/bin/x86/linux/sum")
board.set_se_binary_workload(binary)

simulator = Simulator(board=board)
simulator.run()
