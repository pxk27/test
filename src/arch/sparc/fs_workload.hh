/*
 * Copyright (c) 2002-2005 The Regents of The University of Michigan
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are
 * met: redistributions of source code must retain the above copyright
 * notice, this list of conditions and the following disclaimer;
 * redistributions in binary form must reproduce the above copyright
 * notice, this list of conditions and the following disclaimer in the
 * documentation and/or other materials provided with the distribution;
 * neither the name of the copyright holders nor the names of its
 * contributors may be used to endorse or promote products derived from
 * this software without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
 * "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
 * LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
 * A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
 * OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
 * SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
 * LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
 * DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
 * THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
 * (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

#ifndef __ARCH_SPARC_FS_WORKLOAD_HH__
#define __ARCH_SPARC_FS_WORKLOAD_HH__

#include "arch/sparc/faults.hh"
#include "arch/sparc/remote_gdb.hh"
#include "params/SparcFsWorkload.hh"
#include "sim/workload.hh"

namespace gem5
{

namespace SparcISA
{

class FsWorkload : public Workload
{
  protected:
    loader::SymbolTable defaultSymtab;

  public:
    PARAMS(SparcFsWorkload);

    FsWorkload(const SparcFsWorkloadParams &params) : Workload(params) {}

    void initState() override;

    void
    setSystem(System *sys) override
    {
        Workload::setSystem(sys);
        gdb =
            BaseRemoteGDB::build<RemoteGDB>(params().remote_gdb_port, system);
    }

    Addr
    getEntry() const override
    {
        Addr pc, npc;
        getREDVector(0x001, pc, npc);
        return pc;
    }

    loader::Arch
    getArch() const override
    {
        return loader::SPARC64;
    }

    ByteOrder
    byteOrder() const override
    {
        return ByteOrder::big;
    }

    const loader::SymbolTable &
    symtab(ThreadContext *tc) override
    {
        return defaultSymtab;
    }

    bool
    insertSymbol(const loader::Symbol &symbol) override
    {
        return defaultSymtab.insert(symbol);
    }
};

} // namespace SparcISA
} // namespace gem5

#endif // __ARCH_SPARC_FS_WORKLOAD_HH__
