/*
 * Copyright (c) 2021 Daniel R. Carvalho
 * All rights reserved
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

#include "base/filters/block_bloom_filter.hh"
#include "params/BloomFilterBlock.hh"

using namespace gem5;

// Uses a single mask to hash the address. The mask is as wide as possible
// (i.e., a 16-entry filter uses 4-bit indices, so the mask has 4 bits)
#define GEM5_DECLARE_FILTER_PARAMS(name) \
    BloomFilterBlockParams name; \
    name.eventq_index = 0; \
    name.size = 16; \
    name.offset_bits = 6; \
    name.num_bits = 1; \
    name.threshold = 1; \
    name.masks_lsbs = {0}; \
    name.masks_sizes = {4}

/** Test that a filter is initialized in a cleared state. */
TEST(BloomFilterBlockTest, Construct)
{
    GEM5_DECLARE_FILTER_PARAMS(params);
    BloomFilter::Block filter(params);
    ASSERT_EQ(filter.getTotalCount(), 0);
}

/**
 * Test that setting a single address yields a true positive when checking
 * if that address is present.
 */
TEST(BloomFilterBlockTest, SetIsSetTruePositive)
{
    GEM5_DECLARE_FILTER_PARAMS(params);
    BloomFilter::Block filter(params);
    ASSERT_EQ(filter.getTotalCount(), 0);

    filter.set(0);
    ASSERT_EQ(filter.getTotalCount(), 1);
    ASSERT_EQ(filter.getCount(0), 1);
    ASSERT_TRUE(filter.isSet(0));
}

/**
 * Test that, when the hash matches, setting address A yields a false positive
 * for an address B that hasn't been inserted.
 */
TEST(BloomFilterBlockTest, SetIsSetFalsePositive)
{
    GEM5_DECLARE_FILTER_PARAMS(params);
    BloomFilter::Block filter(params);
    ASSERT_EQ(filter.getTotalCount(), 0);

    filter.set(0);
    ASSERT_EQ(filter.getTotalCount(), 1);
    ASSERT_EQ(filter.getCount(1), 1);
    ASSERT_TRUE(filter.isSet(1));
}

/**
 * Test that, when the hash does not match, setting address A yields a true
 * negative for an address B that hasn't been inserted.
 */
TEST(BloomFilterBlockTest, SetIsSetTrueNegative)
{
    GEM5_DECLARE_FILTER_PARAMS(params);
    BloomFilter::Block filter(params);
    ASSERT_EQ(filter.getTotalCount(), 0);

    filter.set(0);
    ASSERT_EQ(filter.getTotalCount(), 1);
    ASSERT_EQ(filter.getCount(1 << params.offset_bits), 0);
    ASSERT_FALSE(filter.isSet(1 << params.offset_bits));
}

/**
 * Test false negative by setting two conflicting addresses, and then
 * unsetting one of them.
 */
TEST(BloomFilterBlockTest, SetIsSetFalseNegative)
{
    GEM5_DECLARE_FILTER_PARAMS(params);
    BloomFilter::Block filter(params);
    ASSERT_EQ(filter.getTotalCount(), 0);

    filter.set(0);
    filter.set(1);
    ASSERT_EQ(filter.getTotalCount(), 1);
    ASSERT_EQ(filter.getCount(0), 1);
    ASSERT_TRUE(filter.isSet(0));
    ASSERT_EQ(filter.getCount(1), 1);
    ASSERT_TRUE(filter.isSet(1));

    // Unsetting one of them will generate a false negative for the other
    filter.unset(1);
    ASSERT_EQ(filter.getTotalCount(), 0);
    ASSERT_EQ(filter.getCount(0), 0);
    ASSERT_FALSE(filter.isSet(0));
    ASSERT_EQ(filter.getCount(1), 0);
    ASSERT_FALSE(filter.isSet(1));
}

/**
 * Test that isSet works for multiple simultaneously set entries by
 * simultaneously saturating different entries at the same time.
 */
TEST(BloomFilterBlockTest, MultipleIsSet)
{
    GEM5_DECLARE_FILTER_PARAMS(params);
    BloomFilter::Block filter(params);
    ASSERT_EQ(filter.getTotalCount(), 0);

    filter.set(0);
    ASSERT_EQ(filter.getTotalCount(), 1);
    filter.set(1 << params.offset_bits);
    ASSERT_EQ(filter.getTotalCount(), 2);
    ASSERT_EQ(filter.getCount(0), 1);
    ASSERT_TRUE(filter.isSet(0));
    ASSERT_EQ(filter.getCount(1 << params.offset_bits), 1);
    ASSERT_TRUE(filter.isSet(1 << params.offset_bits));
    ASSERT_EQ(filter.getCount(2 << params.offset_bits), 0);
    ASSERT_FALSE(filter.isSet(2 << params.offset_bits));

    filter.clear();
    ASSERT_EQ(filter.getTotalCount(), 0);
    filter.set(1 << params.offset_bits);
    ASSERT_EQ(filter.getTotalCount(), 1);
    filter.set(2 << params.offset_bits);
    ASSERT_EQ(filter.getTotalCount(), 2);
    ASSERT_EQ(filter.getCount(0), 0);
    ASSERT_FALSE(filter.isSet(0));
    ASSERT_EQ(filter.getCount(1 << params.offset_bits), 1);
    ASSERT_TRUE(filter.isSet(1 << params.offset_bits));
    ASSERT_EQ(filter.getCount(2 << params.offset_bits), 1);
    ASSERT_TRUE(filter.isSet(2 << params.offset_bits));

    filter.clear();
    ASSERT_EQ(filter.getTotalCount(), 0);
    filter.set(0);
    ASSERT_EQ(filter.getTotalCount(), 1);
    filter.set(2 << params.offset_bits);
    ASSERT_EQ(filter.getTotalCount(), 2);
    ASSERT_EQ(filter.getCount(0), 1);
    ASSERT_TRUE(filter.isSet(0));
    ASSERT_EQ(filter.getCount(1 << params.offset_bits), 0);
    ASSERT_FALSE(filter.isSet(1 << params.offset_bits));
    ASSERT_EQ(filter.getCount(2 << params.offset_bits), 1);
    ASSERT_TRUE(filter.isSet(2 << params.offset_bits));

    filter.clear();
    ASSERT_EQ(filter.getTotalCount(), 0);
    filter.set(0);
    ASSERT_EQ(filter.getTotalCount(), 1);
    filter.set(1 << params.offset_bits);
    ASSERT_EQ(filter.getTotalCount(), 2);
    filter.set(2 << params.offset_bits);
    ASSERT_EQ(filter.getTotalCount(), 3);
    ASSERT_EQ(filter.getCount(0), 1);
    ASSERT_TRUE(filter.isSet(0));
    ASSERT_EQ(filter.getCount(1 << params.offset_bits), 1);
    ASSERT_TRUE(filter.isSet(1));
    ASSERT_EQ(filter.getCount(2 << params.offset_bits), 1);
    ASSERT_TRUE(filter.isSet(2));
}

/**
 * Test that isSet takes the threshold into consideration. This test
 * increases the number of bits in the filter's entries to be able to
 * raise the threshold at which an entry is considered as set.
 */
TEST(BloomFilterBlockTest, SingleIsSetThreshold)
{
    GEM5_DECLARE_FILTER_PARAMS(params);
    params.num_bits = 2;
    params.threshold = 2;
    BloomFilter::Block filter(params);
    ASSERT_EQ(filter.getTotalCount(), 0);

    filter.set(0);
    ASSERT_EQ(filter.getTotalCount(), 1);
    ASSERT_FALSE(filter.isSet(0));
    ASSERT_FALSE(filter.isSet(1 << params.offset_bits));
    ASSERT_FALSE(filter.isSet(2 << params.offset_bits));
    filter.set(0);
    ASSERT_EQ(filter.getTotalCount(), 2);
    ASSERT_TRUE(filter.isSet(0));
    ASSERT_FALSE(filter.isSet(1 << params.offset_bits));
    ASSERT_FALSE(filter.isSet(2 << params.offset_bits));

    filter.clear();
    filter.set(1 << params.offset_bits);
    ASSERT_EQ(filter.getTotalCount(), 1);
    ASSERT_FALSE(filter.isSet(0));
    ASSERT_FALSE(filter.isSet(1 << params.offset_bits));
    ASSERT_FALSE(filter.isSet(2 << params.offset_bits));
    filter.set(1 << params.offset_bits);
    ASSERT_EQ(filter.getTotalCount(), 2);
    ASSERT_FALSE(filter.isSet(0));
    ASSERT_TRUE(filter.isSet(1 << params.offset_bits));
    ASSERT_FALSE(filter.isSet(2 << params.offset_bits));

    filter.clear();
    filter.set(2 << params.offset_bits);
    ASSERT_EQ(filter.getTotalCount(), 1);
    ASSERT_FALSE(filter.isSet(0));
    ASSERT_FALSE(filter.isSet(1 << params.offset_bits));
    ASSERT_FALSE(filter.isSet(2 << params.offset_bits));
    filter.set(2 << params.offset_bits);
    ASSERT_EQ(filter.getTotalCount(), 2);
    ASSERT_FALSE(filter.isSet(0));
    ASSERT_FALSE(filter.isSet(1 << params.offset_bits));
    ASSERT_TRUE(filter.isSet(2 << params.offset_bits));

    // Setting different entries once should not make any of them
    // reach the threshold
    filter.clear();
    filter.set(0);
    filter.set(1 << params.offset_bits);
    filter.set(2 << params.offset_bits);
    ASSERT_EQ(filter.getTotalCount(), 3);
    ASSERT_FALSE(filter.isSet(0));
    ASSERT_FALSE(filter.isSet(1 << params.offset_bits));
    ASSERT_FALSE(filter.isSet(2 << params.offset_bits));
}

/**
 * Test that the hash is correct. The configuration allows two hash values,
 * since each mask uses only 1 bit and they are XORed.
 */
TEST(BloomFilterBlockTest, Hash1Bit)
{
    GEM5_DECLARE_FILTER_PARAMS(params);
    params.num_bits = 4;
    params.offset_bits = 0;
    params.masks_lsbs = {1, 3};
    params.masks_sizes = {1, 1};
    BloomFilter::Block filter(params);
    ASSERT_EQ(filter.getTotalCount(), 0);

    filter.set(0);
    ASSERT_EQ(filter.getCount(0), 1); // 0 ^ 0 = 0
    filter.set(1);
    ASSERT_EQ(filter.getCount(1), 2); // 0 ^ 0 = 0
    filter.set(2);
    ASSERT_EQ(filter.getCount(2), 1); // 0 ^ 1 = 1
    filter.set(3);
    ASSERT_EQ(filter.getCount(3), 2); // 0 ^ 1 = 1
    filter.set(4);
    ASSERT_EQ(filter.getCount(4), 3); // 0 ^ 0 = 0
    filter.set(5);
    ASSERT_EQ(filter.getCount(5), 4); // 0 ^ 0 = 0
    filter.set(6);
    ASSERT_EQ(filter.getCount(6), 3); // 0 ^ 1 = 1
    filter.set(7);
    ASSERT_EQ(filter.getCount(7), 4); // 0 ^ 1 = 1
    filter.set(8);
    ASSERT_EQ(filter.getCount(8), 5); // 1 ^ 0 = 0
    filter.set(9);
    ASSERT_EQ(filter.getCount(9), 6); // 1 ^ 0 = 0
    filter.set(10);
    ASSERT_EQ(filter.getCount(10), 5); // 1 ^ 1 = 1
    filter.set(11);
    ASSERT_EQ(filter.getCount(11), 6); // 1 ^ 1 = 1
    filter.set(12);
    ASSERT_EQ(filter.getCount(12), 7); // 1 ^ 0 = 0
    filter.set(13);
    ASSERT_EQ(filter.getCount(13), 8); // 1 ^ 0 = 0
    filter.set(14);
    ASSERT_EQ(filter.getCount(14), 7); // 1 ^ 1 = 1
    filter.set(15);
    ASSERT_EQ(filter.getCount(15), 8); // 1 ^ 1 = 1
}

/**
 * Test that the hash is correct. The configuration allows four hash values,
 * since each mask uses only 2 bits and they are XORed.
 */
TEST(BloomFilterBlockTest, Hash2Bits)
{
    GEM5_DECLARE_FILTER_PARAMS(params);
    params.num_bits = 3;
    params.offset_bits = 0;
    params.masks_lsbs = {0, 2};
    params.masks_sizes = {2, 2};
    BloomFilter::Block filter(params);
    ASSERT_EQ(filter.getTotalCount(), 0);

    filter.set(0);
    ASSERT_EQ(filter.getCount(0), 1); // 00 ^ 00 = 00
    filter.set(1);
    ASSERT_EQ(filter.getCount(1), 1); // 00 ^ 01 = 01
    filter.set(2);
    ASSERT_EQ(filter.getCount(2), 1); // 00 ^ 10 = 10
    filter.set(3);
    ASSERT_EQ(filter.getCount(3), 1); // 00 ^ 11 = 11
    filter.set(4);
    ASSERT_EQ(filter.getCount(4), 2); // 01 ^ 00 = 01
    filter.set(5);
    ASSERT_EQ(filter.getCount(5), 2); // 01 ^ 01 = 00
    filter.set(6);
    ASSERT_EQ(filter.getCount(6), 2); // 01 ^ 10 = 11
    filter.set(7);
    ASSERT_EQ(filter.getCount(7), 2); // 01 ^ 11 = 10
    filter.set(8);
    ASSERT_EQ(filter.getCount(8), 3); // 10 ^ 00 = 10
    filter.set(9);
    ASSERT_EQ(filter.getCount(9), 3); // 10 ^ 01 = 11
    filter.set(10);
    ASSERT_EQ(filter.getCount(10), 3); // 10 ^ 10 = 00
    filter.set(11);
    ASSERT_EQ(filter.getCount(11), 3); // 10 ^ 11 = 01
    filter.set(12);
    ASSERT_EQ(filter.getCount(12), 4); // 11 ^ 00 = 11
    filter.set(13);
    ASSERT_EQ(filter.getCount(13), 4); // 11 ^ 01 = 10
    filter.set(14);
    ASSERT_EQ(filter.getCount(14), 4); // 11 ^ 10 = 01
    filter.set(15);
    ASSERT_EQ(filter.getCount(15), 4); // 11 ^ 11 = 00
}

/** Test that merging two empty bloom filters results in an empty filter. */
TEST(BloomFilterBlockTest, MergeBothEmpty)
{
    GEM5_DECLARE_FILTER_PARAMS(params);

    BloomFilter::Block filter(params);
    BloomFilter::Block filter2(params);

    filter.merge(&filter2);
    ASSERT_EQ(filter.getTotalCount(), 0);
    ASSERT_EQ(filter2.getTotalCount(), 0);
}

/**
 * Test that merging a populated filter with an empty filter does not modify
 * any of the filters.
 */
TEST(BloomFilterBlockTest, MergeWithEmpty)
{
    GEM5_DECLARE_FILTER_PARAMS(params);

    BloomFilter::Block filter(params);
    filter.set(1 << params.offset_bits);

    BloomFilter::Block filter2(params);

    filter.merge(&filter2);
    ASSERT_EQ(filter.getTotalCount(), 1);
    ASSERT_TRUE(filter.isSet(1 << params.offset_bits));
    ASSERT_EQ(filter2.getTotalCount(), 0);
}

/**
 * Test that merging an empty filter with a populated filter results in
 * two equal filters.
 */
TEST(BloomFilterBlockTest, DISABLED_MergeWithEmpty2)
{
    GEM5_DECLARE_FILTER_PARAMS(params);

    BloomFilter::Block filter(params);

    BloomFilter::Block filter2(params);
    filter2.set(1 << params.offset_bits);

    filter.merge(&filter2);
    ASSERT_EQ(filter.getTotalCount(), 1);
    ASSERT_TRUE(filter.isSet(1 << params.offset_bits));
    ASSERT_EQ(filter2.getTotalCount(), 1);
    ASSERT_TRUE(filter.isSet(1 << params.offset_bits));
}

/**
 * Test merging two filters with intersecting entries. The caller is modified,
 * but the other filter is not.
 */
TEST(BloomFilterBlockTest, MergeNoIntersection)
{
    GEM5_DECLARE_FILTER_PARAMS(params);

    BloomFilter::Block filter(params);
    filter.set(1 << params.offset_bits);
    filter.set(2 << params.offset_bits);
    filter.set(5 << params.offset_bits);
    filter.set(8 << params.offset_bits);

    BloomFilter::Block filter2(params);
    filter2.set(3 << params.offset_bits);
    filter2.set(4 << params.offset_bits);
    filter2.set(9 << params.offset_bits);

    filter.merge(&filter2);
    ASSERT_EQ(filter.getTotalCount(), 7);
    ASSERT_TRUE(filter.isSet(1 << params.offset_bits));
    ASSERT_TRUE(filter.isSet(2 << params.offset_bits));
    ASSERT_TRUE(filter.isSet(3 << params.offset_bits));
    ASSERT_TRUE(filter.isSet(4 << params.offset_bits));
    ASSERT_TRUE(filter.isSet(5 << params.offset_bits));
    ASSERT_TRUE(filter.isSet(8 << params.offset_bits));
    ASSERT_TRUE(filter.isSet(9 << params.offset_bits));
    ASSERT_EQ(filter2.getTotalCount(), 3);
    ASSERT_TRUE(filter2.isSet(3 << params.offset_bits));
    ASSERT_TRUE(filter2.isSet(4 << params.offset_bits));
    ASSERT_TRUE(filter2.isSet(9 << params.offset_bits));
}

/** Test merging two filters with insersecting entries. */
TEST(BloomFilterBlockTest, MergeIntersectionThreshold1)
{
    GEM5_DECLARE_FILTER_PARAMS(params);

    BloomFilter::Block filter(params);
    filter.set(1 << params.offset_bits);
    filter.set(2 << params.offset_bits);
    filter.set(5 << params.offset_bits);
    filter.set(8 << params.offset_bits);

    BloomFilter::Block filter2(params);
    filter2.set(3 << params.offset_bits);
    filter2.set(5 << params.offset_bits);
    filter2.set(9 << params.offset_bits);

    filter.merge(&filter2);
    ASSERT_EQ(filter.getTotalCount(), 6);
    ASSERT_TRUE(filter.isSet(1 << params.offset_bits));
    ASSERT_TRUE(filter.isSet(2 << params.offset_bits));
    ASSERT_TRUE(filter.isSet(3 << params.offset_bits));
    ASSERT_TRUE(filter.isSet(5 << params.offset_bits));
    ASSERT_TRUE(filter.isSet(8 << params.offset_bits));
    ASSERT_TRUE(filter.isSet(9 << params.offset_bits));
    ASSERT_EQ(filter2.getTotalCount(), 3);
    ASSERT_TRUE(filter2.isSet(3 << params.offset_bits));
    ASSERT_TRUE(filter2.isSet(5 << params.offset_bits));
    ASSERT_TRUE(filter2.isSet(9 << params.offset_bits));
}

/**
 * Test merging two filters with insersecting entries and threshold at 2.
 * One entry is populated so that it only reaches the threshold after merging.
 * One entry is populated so that when merged it will become saturated.
 */
TEST(BloomFilterBlockTest, MergeIntersectionThreshold2)
{
    GEM5_DECLARE_FILTER_PARAMS(params);
    params.num_bits = 2;
    params.threshold = 2;

    BloomFilter::Block filter(params);
    filter.set(1 << params.offset_bits);
    filter.set(2 << params.offset_bits);
    filter.set(5 << params.offset_bits);
    filter.set(5 << params.offset_bits);
    filter.set(8 << params.offset_bits);

    BloomFilter::Block filter2(params);
    filter2.set(2 << params.offset_bits);
    filter2.set(5 << params.offset_bits);
    filter2.set(5 << params.offset_bits);
    filter2.set(5 << params.offset_bits);
    filter2.set(9 << params.offset_bits);

    filter.merge(&filter2);
    // 1 one, 2 twos, 3 fives (saturated), 1 eight, 1 nine
    ASSERT_EQ(filter.getTotalCount(), 8);
    ASSERT_TRUE(filter.isSet(2 << params.offset_bits));
    ASSERT_TRUE(filter.isSet(5 << params.offset_bits));
    ASSERT_EQ(filter2.getTotalCount(), 5);
    ASSERT_FALSE(filter2.isSet(2 << params.offset_bits));
    ASSERT_TRUE(filter2.isSet(5 << params.offset_bits));
}

/** Test that trying to merge filters of different sizes fails. */
TEST(BloomFilterBlockDeathTest, MergeDifferent)
{
#ifdef NDEBUG
    GTEST_SKIP() << "Skipping as assertions are "
        "stripped out of fast builds";
#endif

    GEM5_DECLARE_FILTER_PARAMS(params);
    BloomFilter::Block filter(params);

    GEM5_DECLARE_FILTER_PARAMS(params2);
    params2.size = params.size + 1;
    BloomFilter::Block filter2(params2);

    ASSERT_DEATH(filter.merge(&filter2), "");
}

/** Test that an error is thrown when there are no masks. */
TEST(BloomFilterBlockDeathTest, NoMask)
{
#ifdef NDEBUG
    GTEST_SKIP() << "Skipping as assertions are "
        "stripped out of fast builds";
#endif

    GEM5_DECLARE_FILTER_PARAMS(params);
    params.masks_lsbs = {};
    params.masks_sizes = {};
    ASSERT_ANY_THROW(BloomFilter::Block filter(params));
}

/**
 * Test that an error is thrown when the information regarding each mask
 * is not complete. Eack mask should contain its LSB and size information.
 */
TEST(BloomFilterBlockDeathTest, IncompleteMask)
{
#ifdef NDEBUG
    GTEST_SKIP() << "Skipping as assertions are "
        "stripped out of fast builds";
#endif

    GEM5_DECLARE_FILTER_PARAMS(params);
    params.masks_lsbs = {0, 10};
    params.masks_sizes = {5};
    ASSERT_ANY_THROW(BloomFilter::Block filter(params));
}

/**
 * Test that an error is thrown when the mask is larger than the filter
 * (the size too large).
 */
TEST(BloomFilterBlockDeathTest, InvalidMaskLargeSize)
{
#ifdef NDEBUG
    GTEST_SKIP() << "Skipping as assertions are "
        "stripped out of fast builds";
#endif

    GEM5_DECLARE_FILTER_PARAMS(params);
    params.masks_lsbs = {3};
    params.masks_sizes = {60};
    ASSERT_ANY_THROW(BloomFilter::Block filter(params));
}

/**
 * Test that an error is thrown when the mask includes bits outside the
 * range of an address.
 */
TEST(BloomFilterBlockDeathTest, InvalidMaskLSB)
{
#ifdef NDEBUG
    GTEST_SKIP() << "Skipping as assertions are "
        "stripped out of fast builds";
#endif

    GEM5_DECLARE_FILTER_PARAMS(params);
    params.masks_lsbs = {60};
    params.masks_sizes = {5};
    ASSERT_ANY_THROW(BloomFilter::Block filter(params));
}

#undef GEM5_DECLARE_FILTER_PARAMS
