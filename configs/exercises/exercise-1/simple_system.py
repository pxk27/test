import m5
from m5.objects import *

# Add the common scripts to our path
m5.util.addToPath("../../")

# import the caches which we made
from learning_gem5.part1.caches import *

# Create system
system = System()

# Create clock domain
system.clk_domain = SrcClockDomain()
system.clk_domain.clock = '3GHz'
system.clk_domain.voltage_domain = VoltageDomain()

# Give ourselves 4GB of RAM
system.mem_mode = 'timing'
system.mem_ranges = [AddrRange('4GB')]

# Create a simple x86 timing CPU core
system.cpu = X86TimingSimpleCPU()

# Create memory bus
system.membus = SystemXBar()

cache_enabled = (input("Configure system with cache?: ").lower() == "yes")
if cache_enabled:
    # Create L1 cache
    system.cpu.icache = L1ICache()
    system.cpu.dcache = L1DCache()

    # Connect CPU to L1 cache
    system.cpu.icache.connectCPU(system.cpu)
    system.cpu.dcache.connectCPU(system.cpu)

    # Create L2 bus
    system.l2bus = L2XBar()

    # Connect L2 bus to L1 cache
    system.cpu.icache.connectBus(system.l2bus)
    system.cpu.dcache.connectBus(system.l2bus)

    # Create L2 cache and connect it to memory bus
    system.l2cache = L2Cache()
    system.l2cache.connectCPUSideBus(system.l2bus)
    system.l2cache.connectMemSideBus(system.membus)
else:
    # Connect CPU cache ports to memory bus ports since we aren't using cache
    system.cpu.icache_port = system.membus.cpu_side_ports
    system.cpu.dcache_port = system.membus.cpu_side_ports

# Create interrupt controller
system.cpu.createInterruptController()

# Connect the parellel I/O ports
system.cpu.interrupts[0].pio = system.membus.mem_side_ports
system.cpu.interrupts[0].int_requestor = system.membus.cpu_side_ports
system.cpu.interrupts[0].int_responder = system.membus.mem_side_ports

# Connect system port to memory bus to allow for reading and writing to memory
system.system_port = system.membus.cpu_side_ports

# Create memory controller and DRAM configuration
system.mem_ctrl = MemCtrl()
system.mem_ctrl.dram = DDR3_1600_8x8()
system.mem_ctrl.dram.range = system.mem_ranges[0]
system.mem_ctrl.port = system.membus.mem_side_ports

# Set path to binary file
binary = 'tests/test-progs/sum/bin/x86/linux/sum'

# for gem5 V21 and beyond
system.workload = SEWorkload.init_compatible(binary)

# Create process with specified binary path
process = Process()
process.cmd = [binary]
system.cpu.workload = process
system.cpu.createThreads()

# Instantiate root system
root = Root(full_system = False, system = system)
m5.instantiate()

# Begin simulation
print("Beginning simulation!")
exit_event = m5.simulate()

# Inspect system state
print('Exiting @ tick {} because {}'
      .format(m5.curTick(), exit_event.getCause()))
