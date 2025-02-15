/**
 * Copyright (c) 2025 Daniel R. Carvalho
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

#include <gtest/gtest-spi.h>
#include <gtest/gtest.h>

#include <cassert>

#include "mem/cache/replacement_policies/fifo_rp.hh"
#include "params/FIFORP.hh"

// Create a dummy RP class so that we can verify if the replacement data is
// of the expected type for this RP
class DummyFIFO : public gem5::replacement_policy::FIFO
{
  public:
    using gem5::replacement_policy::FIFO::FIFO;

    /// Verify that the data is of the expected type
    bool
    validateType(
        const std::shared_ptr<gem5::replacement_policy::ReplacementData>
            repl_data) const
    {
        return nullptr != std::dynamic_pointer_cast<
            gem5::replacement_policy::FIFO::FIFOReplData>(repl_data);
    }
};

/// Common fixture that initializes the replacement policy
class FIFORPTestF : public ::testing::Test
{
  public:
    std::shared_ptr<DummyFIFO> rp;

    FIFORPTestF()
    {
        gem5::FIFORPParams params;
        params.eventq_index = 0;
        rp = std::make_shared<DummyFIFO>(params);
    }
};

/// Test that instantiating an entry generates the replacement data of the
/// expected type
TEST_F(FIFORPTestF, InstantiatedEntry)
{
    const auto repl_data = rp->instantiateEntry();

    // instantiateEntry must return a valid pointer
    ASSERT_NE(repl_data, nullptr);

    // instantiateEntry must return a pointer of the tested class'
    // replacement data type
    ASSERT_TRUE(rp->validateType(repl_data));
}

/// Test that if there is one candidate, then it will always be the victim,
/// regardless of its replacement data
TEST_F(FIFORPTestF, GetVictim1Candidate)
{
    gem5::ReplaceableEntry entry;
    entry.replacementData = rp->instantiateEntry();
    gem5::ReplacementCandidates candidates;
    candidates.push_back(&entry);
    ASSERT_EQ(rp->getVictim(candidates), &entry);

    rp->invalidate(entry.replacementData);
    ASSERT_EQ(rp->getVictim(candidates), &entry);

    rp->reset(entry.replacementData);
    ASSERT_EQ(rp->getVictim(candidates), &entry);

    rp->touch(entry.replacementData);
    ASSERT_EQ(rp->getVictim(candidates), &entry);
}

/// Fixture that tests victimization
class FIFORPVictimizationTestF : public FIFORPTestF
{
  protected:
    // The entries being victimized
    std::vector<gem5::ReplaceableEntry> entries;

    // The entries, in candidate form
    gem5::ReplacementCandidates candidates;

  public:
    // The number of entries is arbitrary. It does not need to be high, since
    // having more entries is not expected to increase coverage
    FIFORPVictimizationTestF() : FIFORPTestF(), entries(4) {
        for (auto &entry : entries) {
            entry.replacementData = rp->instantiateEntry();
            candidates.push_back(&entry);
        }
    }
};

/// Test that when all entries are invalid the first candidate will always be
/// selected, regardless of the order of the invalidations
TEST_F(FIFORPVictimizationTestF, GetVictimAllInvalid)
{
    auto expected_victim = &entries.front();

    // At this point all candidates are considered to be first, since
    // no entries have ever been reset
    ASSERT_EQ(rp->getVictim(candidates), expected_victim);

    // Since all candidates are already invalid, nothing changes if we
    // invalidate all of them again
    for (auto &entry : entries) {
        rp->invalidate(entry.replacementData);
    }
    ASSERT_EQ(rp->getVictim(candidates), expected_victim);

    // Even if we invalidate the entry being selected for victimization last
    rp->invalidate(expected_victim->replacementData);
    ASSERT_EQ(rp->getVictim(candidates), expected_victim);
}

/// Test that when there is at least a single invalid entry, it will be
/// selected during the victimization
TEST_F(FIFORPVictimizationTestF, GetVictimOneInvalid)
{
    for (auto &entry : entries) {
        // Validate all entries to start from a clean state
        for (auto &entry : entries) {
            rp->reset(entry.replacementData);
        }

        // Set one of the entries as invalid
        rp->invalidate(entry.replacementData);

        ASSERT_EQ(rp->getVictim(candidates), &entry);
    }
}

/// Test that the first entry to be reset will be selected during victimization
TEST_F(FIFORPVictimizationTestF, GetVictim)
{
    for (size_t i = 0; i < entries.size(); ++i) {
        SCOPED_TRACE(i);
        auto &entry = entries[i];

        // Reset one of the entries to make it become the single first entry
        rp->reset(entry.replacementData);

        // Now change ticks and validate all other entries to make them not
        // tie for first entry
        for (size_t j = 0; j < entries.size(); ++j) {
            if (i != j) {
                rp->reset(entries[j].replacementData);
            }
        }

        ASSERT_EQ(rp->getVictim(candidates), &entry);
    }
}

/// Test that the first entry to be reset will be selected during
/// victimization, even if it was touched before the victimization process
TEST_F(FIFORPVictimizationTestF, GetVictimAfterTouch)
{
    for (size_t i = 0; i < entries.size(); ++i) {
        SCOPED_TRACE(i);
        auto &entry = entries[i];

        // Reset one of the entries to make it become first entry
        rp->reset(entry.replacementData);

        // Now change ticks and validate all other entries to make them not
        // tie for first entry
        for (size_t j = 0; j < entries.size(); ++j) {
            if (i != j) {
                rp->reset(entries[j].replacementData);
            }
        }

        // Even if we touch the first entry, it will not stop being the
        // first entry, so it will be selected for victimization
        rp->touch(entry.replacementData);

        ASSERT_EQ(rp->getVictim(candidates), &entry);
    }
}

typedef FIFORPTestF FIFORPFDeathTest;

TEST_F(FIFORPFDeathTest, InvalidateNull)
{
    ASSERT_DEATH(rp->invalidate(nullptr), "");
}

TEST_F(FIFORPFDeathTest, ResetNull)
{
    ASSERT_DEATH(rp->reset(nullptr), "");
}

TEST_F(FIFORPFDeathTest, TouchNull)
{
    ASSERT_DEATH(rp->touch(nullptr), "");
}

TEST_F(FIFORPFDeathTest, NoCandidates)
{
    gem5::ReplacementCandidates candidates;
    ASSERT_DEATH(rp->getVictim(candidates), "");
}
