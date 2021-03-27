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

#include "base/filters/perfect_bloom_filter.hh"
#include "params/BloomFilterPerfect.hh"

using namespace gem5;

#define GEM5_DECLARE_FILTER_PARAMS(name) \
    BloomFilterPerfectParams name; \
    name.eventq_index = 0; \
    name.size = 1; \
    name.offset_bits = 6; \
    name.num_bits = 1; \
    name.threshold = 1

/** Test that a filter is initialized in a cleared state. */
TEST(BloomFilterPerfectTest, Construct)
{
    GEM5_DECLARE_FILTER_PARAMS(params);
    BloomFilter::Perfect filter(params);
    ASSERT_EQ(filter.getTotalCount(), 0);
}

/**
 * Test that setting a single entry will only set that entry, and no other
 * entry.
 */
TEST(BloomFilterPerfectTest, SingleIsSet)
{
    GEM5_DECLARE_FILTER_PARAMS(params);
    BloomFilter::Perfect filter(params);
    ASSERT_EQ(filter.getTotalCount(), 0);

    filter.set(0);
    ASSERT_EQ(filter.getTotalCount(), 1);
    ASSERT_EQ(filter.getCount(0), 1);
    ASSERT_TRUE(filter.isSet(0));
    ASSERT_EQ(filter.getCount(1), 0);
    ASSERT_FALSE(filter.isSet(1));
    ASSERT_EQ(filter.getCount(2), 0);
    ASSERT_FALSE(filter.isSet(2));

    filter.clear();
    ASSERT_EQ(filter.getTotalCount(), 0);
    filter.set(1);
    ASSERT_EQ(filter.getTotalCount(), 1);
    ASSERT_EQ(filter.getCount(0), 0);
    ASSERT_FALSE(filter.isSet(0));
    ASSERT_EQ(filter.getCount(1), 1);
    ASSERT_TRUE(filter.isSet(1));
    ASSERT_EQ(filter.getCount(2), 0);
    ASSERT_FALSE(filter.isSet(2));

    filter.clear();
    ASSERT_EQ(filter.getTotalCount(), 0);
    filter.set(2);
    ASSERT_EQ(filter.getTotalCount(), 1);
    ASSERT_EQ(filter.getCount(0), 0);
    ASSERT_FALSE(filter.isSet(0));
    ASSERT_EQ(filter.getCount(1), 0);
    ASSERT_FALSE(filter.isSet(1));
    ASSERT_EQ(filter.getCount(2), 1);
    ASSERT_TRUE(filter.isSet(2));
}

/**
 * Test that isSet works for multiple simultaneously set entries by
 * simultaneously saturating different entries at the same time.
 */
TEST(BloomFilterPerfectTest, MultipleIsSet)
{
    GEM5_DECLARE_FILTER_PARAMS(params);
    BloomFilter::Perfect filter(params);
    ASSERT_EQ(filter.getTotalCount(), 0);

    filter.set(0);
    ASSERT_EQ(filter.getTotalCount(), 1);
    filter.set(1);
    ASSERT_EQ(filter.getTotalCount(), 2);
    ASSERT_EQ(filter.getCount(0), 1);
    ASSERT_TRUE(filter.isSet(0));
    ASSERT_EQ(filter.getCount(1), 1);
    ASSERT_TRUE(filter.isSet(1));
    ASSERT_EQ(filter.getCount(2), 0);
    ASSERT_FALSE(filter.isSet(2));

    filter.clear();
    ASSERT_EQ(filter.getTotalCount(), 0);
    filter.set(1);
    ASSERT_EQ(filter.getTotalCount(), 1);
    filter.set(2);
    ASSERT_EQ(filter.getTotalCount(), 2);
    ASSERT_EQ(filter.getCount(0), 0);
    ASSERT_FALSE(filter.isSet(0));
    ASSERT_EQ(filter.getCount(1), 1);
    ASSERT_TRUE(filter.isSet(1));
    ASSERT_EQ(filter.getCount(2), 1);
    ASSERT_TRUE(filter.isSet(2));

    filter.clear();
    ASSERT_EQ(filter.getTotalCount(), 0);
    filter.set(0);
    ASSERT_EQ(filter.getTotalCount(), 1);
    filter.set(2);
    ASSERT_EQ(filter.getTotalCount(), 2);
    ASSERT_EQ(filter.getCount(0), 1);
    ASSERT_TRUE(filter.isSet(0));
    ASSERT_EQ(filter.getCount(1), 0);
    ASSERT_FALSE(filter.isSet(1));
    ASSERT_EQ(filter.getCount(2), 1);
    ASSERT_TRUE(filter.isSet(2));

    filter.clear();
    ASSERT_EQ(filter.getTotalCount(), 0);
    filter.set(0);
    ASSERT_EQ(filter.getTotalCount(), 1);
    filter.set(1);
    ASSERT_EQ(filter.getTotalCount(), 2);
    filter.set(2);
    ASSERT_EQ(filter.getTotalCount(), 3);
    ASSERT_EQ(filter.getCount(0), 1);
    ASSERT_TRUE(filter.isSet(0));
    ASSERT_EQ(filter.getCount(1), 1);
    ASSERT_TRUE(filter.isSet(1));
    ASSERT_EQ(filter.getCount(2), 1);
    ASSERT_TRUE(filter.isSet(2));
}

/** Test that setting a single entry twice will not pass its threshold. */
TEST(BloomFilterPerfectTest, SingleTwiceGetCount)
{
    GEM5_DECLARE_FILTER_PARAMS(params);
    BloomFilter::Perfect filter(params);
    ASSERT_EQ(filter.getTotalCount(), 0);

    filter.set(0);
    filter.set(0);
    ASSERT_EQ(filter.getTotalCount(), 1);
    ASSERT_EQ(filter.getCount(0), 1);
}

/** Test that merging two empty bloom filters results in an empty filter. */
TEST(BloomFilterPerfectTest, MergeBothEmpty)
{
    GEM5_DECLARE_FILTER_PARAMS(params);

    BloomFilter::Perfect filter(params);
    BloomFilter::Perfect filter2(params);

    filter.merge(&filter2);
    ASSERT_EQ(filter.getTotalCount(), 0);
    ASSERT_EQ(filter2.getTotalCount(), 0);
}

/**
 * Test that merging a populated filter with an empty filter does not modify
 * any of the filters.
 */
TEST(BloomFilterPerfectTest, MergeWithEmpty)
{
    GEM5_DECLARE_FILTER_PARAMS(params);

    BloomFilter::Perfect filter(params);
    filter.set(1);

    BloomFilter::Perfect filter2(params);

    filter.merge(&filter2);
    ASSERT_EQ(filter.getTotalCount(), 1);
    ASSERT_TRUE(filter.isSet(1));
    ASSERT_EQ(filter2.getTotalCount(), 0);
}

/**
 * Test that merging an empty filter with a populated filter results in
 * two equal filters.
 */
TEST(BloomFilterPerfectTest, MergeWithEmpty2)
{
    GEM5_DECLARE_FILTER_PARAMS(params);

    BloomFilter::Perfect filter(params);

    BloomFilter::Perfect filter2(params);
    filter2.set(1);

    filter.merge(&filter2);
    ASSERT_EQ(filter.getTotalCount(), 1);
    ASSERT_TRUE(filter.isSet(1));
    ASSERT_EQ(filter2.getTotalCount(), 1);
    ASSERT_TRUE(filter.isSet(1));
}

/**
 * Test merging two filters with intersecting entries. The caller is modified,
 * but the other filter is not.
 */
TEST(BloomFilterPerfectTest, MergeNoIntersection)
{
    GEM5_DECLARE_FILTER_PARAMS(params);

    BloomFilter::Perfect filter(params);
    filter.set(1);
    filter.set(2);
    filter.set(5);
    filter.set(8);

    BloomFilter::Perfect filter2(params);
    filter2.set(3);
    filter2.set(4);
    filter2.set(9);

    filter.merge(&filter2);
    ASSERT_EQ(filter.getTotalCount(), 7);
    ASSERT_TRUE(filter.isSet(1));
    ASSERT_TRUE(filter.isSet(2));
    ASSERT_TRUE(filter.isSet(3));
    ASSERT_TRUE(filter.isSet(4));
    ASSERT_TRUE(filter.isSet(5));
    ASSERT_TRUE(filter.isSet(8));
    ASSERT_TRUE(filter.isSet(9));
    ASSERT_EQ(filter2.getTotalCount(), 3);
    ASSERT_TRUE(filter2.isSet(3));
    ASSERT_TRUE(filter2.isSet(4));
    ASSERT_TRUE(filter2.isSet(9));
}

/** Test merging two filters with insersecting entries. */
TEST(BloomFilterPerfectTest, MergeIntersection)
{
    GEM5_DECLARE_FILTER_PARAMS(params);

    BloomFilter::Perfect filter(params);
    filter.set(1);
    filter.set(2);
    filter.set(5);
    filter.set(8);

    BloomFilter::Perfect filter2(params);
    filter2.set(3);
    filter2.set(5);
    filter2.set(9);

    filter.merge(&filter2);
    ASSERT_EQ(filter.getTotalCount(), 6);
    ASSERT_TRUE(filter.isSet(1));
    ASSERT_TRUE(filter.isSet(2));
    ASSERT_TRUE(filter.isSet(3));
    ASSERT_TRUE(filter.isSet(5));
    ASSERT_TRUE(filter.isSet(8));
    ASSERT_TRUE(filter.isSet(9));
    ASSERT_EQ(filter2.getTotalCount(), 3);
    ASSERT_TRUE(filter2.isSet(3));
    ASSERT_TRUE(filter2.isSet(5));
    ASSERT_TRUE(filter2.isSet(9));
}

/** Test that a perfect filter's size must always be 1. */
TEST(BloomFilterPerfectDeathTest, Size)
{
#ifdef NDEBUG
    GTEST_SKIP() << "Skipping as assertions are "
        "stripped out of fast builds";
#endif

    GEM5_DECLARE_FILTER_PARAMS(params);
    params.size = 2;
    ASSERT_ANY_THROW(BloomFilter::Perfect filter(params));
}

/** Test that a perfect filter's entries' sizes must always be 1. */
TEST(BloomFilterPerfectDeathTest, NumBits)
{
#ifdef NDEBUG
    GTEST_SKIP() << "Skipping as assertions are "
        "stripped out of fast builds";
#endif

    GEM5_DECLARE_FILTER_PARAMS(params);
    params.num_bits = 2;
    ASSERT_ANY_THROW(BloomFilter::Perfect filter(params));
}

/** Test that a perfect filter's threshold must always be 1. */
TEST(BloomFilterPerfectDeathTest, Threshold)
{
#ifdef NDEBUG
    GTEST_SKIP() << "Skipping as assertions are "
        "stripped out of fast builds";
#endif

    GEM5_DECLARE_FILTER_PARAMS(params);
    params.threshold = 2;
    ASSERT_ANY_THROW(BloomFilter::Perfect filter(params));
}

#undef GEM5_DECLARE_FILTER_PARAMS
