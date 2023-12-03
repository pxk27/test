/*
 * Copyright (c) 2020 ARM Limited
 * All rights reserved
 *
 * The license below extends only to copyright in the software and shall
 * not be construed as granting a license to any other intellectual
 * property including but not limited to intellectual property relating
 * to a hardware implementation of the functionality of the software
 * licensed hereunder.  You may use the software subject to the license
 * terms below provided that you ensure that this notice is replicated
 * unmodified and in its entirety in all distributions of the software,
 * modified or unmodified, in source code or in binary form.
 *
 * Copyright (c) 2003-2005 The Regents of The University of Michigan
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

#ifndef __FAULTS_HH__
#define __FAULTS_HH__

#include "base/types.hh"
#include "cpu/null_static_inst.hh"
#include "cpu/static_inst_fwd.hh"
#include "mem/htm.hh"
#include "sim/stats.hh"

namespace gem5
{

class ThreadContext;

typedef const char *FaultName;
typedef statistics::Scalar FaultStat;

class FaultBase
{
  public:
    virtual FaultName name() const = 0;
    virtual void invoke(ThreadContext *tc,
                        const StaticInstPtr &inst = nullStaticInstPtr);
    virtual ~FaultBase(){};
};

class UnimpFault : public FaultBase
{
  private:
    std::string panicStr;

  public:
    UnimpFault(std::string _str) : panicStr(_str) {}

    FaultName
    name() const override
    {
        return "Unimplemented simulator feature";
    }

    void invoke(ThreadContext *tc,
                const StaticInstPtr &inst = nullStaticInstPtr) override;
};

// A fault to trigger a system call in SE mode.
class SESyscallFault : public FaultBase
{
    const char *
    name() const override
    {
        return "syscall_fault";
    }

    void invoke(ThreadContext *tc,
                const StaticInstPtr &inst = nullStaticInstPtr) override;
};

class ReExec : public FaultBase
{
  public:
    virtual FaultName
    name() const override
    {
        return "Re-execution fault";
    }

    void invoke(ThreadContext *tc,
                const StaticInstPtr &inst = nullStaticInstPtr) override;
};

/*
 * This class is needed to allow system call retries to occur for blocking
 * system calls in SE mode. A retry fault will be generated by the system call
 * emulation code if blocking conditions arise; the fault is passed up the
 * function call chain into the CPU model where it is handled by retrying the
 * syscall instruction on a later tick.
 */
class SyscallRetryFault : public FaultBase
{
  public:
    FaultName
    name() const override
    {
        return "System call retry fault";
    }

    SyscallRetryFault() {}

    void invoke(ThreadContext *tc,
                const StaticInstPtr &inst = nullStaticInstPtr) override;
};

class GenericPageTableFault : public FaultBase
{
  private:
    Addr vaddr;

  public:
    FaultName
    name() const override
    {
        return "Generic page table fault";
    }

    GenericPageTableFault(Addr va) : vaddr(va) {}

    void invoke(ThreadContext *tc,
                const StaticInstPtr &inst = nullStaticInstPtr) override;

    Addr
    getFaultVAddr() const
    {
        return vaddr;
    }
};

class GenericAlignmentFault : public FaultBase
{
  private:
    Addr vaddr;

  public:
    FaultName
    name() const override
    {
        return "Generic alignment fault";
    }

    GenericAlignmentFault(Addr va) : vaddr(va) {}

    void invoke(ThreadContext *tc,
                const StaticInstPtr &inst = nullStaticInstPtr) override;

    Addr
    getFaultVAddr() const
    {
        return vaddr;
    }
};

class GenericHtmFailureFault : public FaultBase
{
  protected:
    uint64_t htmUid; // unique identifier used for debugging
    HtmFailureFaultCause cause;

  public:
    GenericHtmFailureFault(uint64_t htm_uid, HtmFailureFaultCause _cause)
        : htmUid(htm_uid), cause(_cause)
    {}

    FaultName
    name() const override
    {
        return "Generic HTM failure fault";
    }

    uint64_t
    getHtmUid() const
    {
        return htmUid;
    }

    HtmFailureFaultCause
    getHtmFailureFaultCause() const
    {
        return cause;
    }

    void invoke(ThreadContext *tc,
                const StaticInstPtr &inst = nullStaticInstPtr) override;
};

} // namespace gem5

#endif // __FAULTS_HH__
