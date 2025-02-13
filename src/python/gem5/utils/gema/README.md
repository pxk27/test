## Overview

gEMA (**g**em5 **E**xternal **M**odules **A**PI) is a flexible and powerful API designed to allow external programs to integrate and manage gem5 simulations. Building upon the gem5 standard library, it simplifies the configuration, execution, and management of simulations by providing an easy-to-use XML-RPC interface. Through its comprehensive set of RPC methods, gEMA enables external programs to interact with gem5 for configuration management, simulation control, and system monitoring.

## Features

### Configuration Management
- **get_config_options()**: Retrieve all available configuration options and their valid values
- **get_configs()**: List all stored configurations
- **get_config_by_id(config_id)**: Retrieve a specific configuration by ID
- **add_config(config_id, d_data)**: Create a new configuration with optional initial data
- **delete_config(config_id)**: Remove a specific configuration

### Component Configuration
- **set_board(config_id, type, clk)**: Configure board parameters including type and clock frequency
- **set_processor(config_id, isa, type, cpu, ncores)**: Set processor configuration including ISA, type, CPU model, and core count
- **set_memory(config_id, type, size)**: Configure memory system type and size
- **set_cache(config_id, type, l1d_size, l1i_size, l2_size, l1d_assoc, l1i_assoc, l2_assoc)**: Set up cache hierarchy with customizable cache sizes and associativity
- **set_resource(config_id, resource)**: Configure additional resources for a specific configuration

### Simulation Control
- **run_simulation(config_id)**: Start a new simulation using the specified configuration
- **get_sims()**: Retrieve list of all stored simulations
- **manage_sim(id, cmd)**: Control running simulations through various commands

### System Management
- **get_endpoints()**: List all available RPC endpoints with descriptions and parameters
- **shutdown()**: Gracefully terminate the gEMA server

## Integration

gEMA's XML-RPC interface makes it straightforward to integrate with existing tools and systems. The API provides:

- JSON-formatted responses for all methods
- Comprehensive error handling and status messages
- Support for complex data structures through JSON serialization
- Introspection capabilities for service discovery

See [rpc-example.py](../../../../../configs/example/gem5_library/gema/rpc-example.py) for example usage.

## Response Format

All RPC methods return JSON-formatted responses that include:
- Success responses with requested data or confirmation messages
- Error responses with:
  - Status: "error"
  - Message: Error description
  - Details: Specific error information
