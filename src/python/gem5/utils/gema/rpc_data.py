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

from dataclasses import (
    dataclass,
    field,
)
from typing import Optional


@dataclass
class GemaBoard:
    type: Optional[str] = None
    clk: Optional[float] = None


@dataclass
class GemaProcessor:
    isa: Optional[str] = None
    type: Optional[str] = None
    cpu: Optional[str] = None
    ncores: Optional[int] = None


@dataclass
class GemaMemory:
    type: Optional[str] = None
    size: Optional[int] = None


@dataclass
class GemaCache:
    type: Optional[str] = None
    l1d_size: Optional[int] = None
    l1i_size: Optional[int] = None
    l2_size: Optional[int] = None
    l1d_assoc: Optional[int] = None
    l1i_assoc: Optional[int] = None
    l2_assoc: Optional[int] = None


@dataclass
class GemaConfiguration:
    config_id: int
    resource: Optional[str] = None
    board: GemaBoard = field(default_factory=GemaBoard)
    processor: GemaProcessor = field(default_factory=GemaProcessor)
    memory: GemaMemory = field(default_factory=GemaMemory)
    cache: GemaCache = field(default_factory=GemaCache)


@dataclass
class GemaSimulation:
    sim_id: int
    config: GemaConfiguration
    generated_on: str
    path: str
    pid: Optional[int] = None
