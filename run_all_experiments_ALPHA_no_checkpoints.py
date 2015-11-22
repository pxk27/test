#!/usr/bin/python

#
# A Python script to run all multi-core experiments for PARSEC 2.1 benchmarks.
#
# Copyright (C) Min Cai 2015
#

import os


def run(bench, l2_size, l2_assoc, l2_tags, num_threads):
    dir = 'results/alpha_no_checkpoints/' + bench + '/' + l2_size + '/' + str(l2_assoc) + 'way/' + l2_tags + '/' + str(num_threads) + 'c/'

    os.system('rm -fr ' + dir)
    os.system('mkdir -p ' + dir)

    cmd_run = 'build/ALPHA_MESI_Two_Level/gem5.opt -d ' + dir + ' configs/example/fs.py --two-phase --cpu-type=timing --num-cpus=' \
              + str(num_threads) + ' --script=ext/parsec/2.1/run_scripts/' \
              + bench + '_' + str(num_threads) + 'c_simsmall.rcS' \
              + ' --caches --l2cache --num-l2caches=1' \
              + ' --l1d_size=32kB --l1i_size=32kB --l2_size=' + l2_size + ' --l2_assoc=' + str(l2_assoc) + ' --l2_tags=' + l2_tags
    print cmd_run
    os.system(cmd_run)


def run_experiments(bench):
    # run(bench, '256kB', 8, 'LRU', 4)
    # run(bench, '512kB', 8, 'LRU', 4)
    # run(bench, '1MB', 8, 'LRU', 4)
    # run(bench, '2MB', 8, 'LRU', 4)
    # run(bench, '4MB', 8, 'LRU', 4)
    # run(bench, '8MB', 8, 'LRU', 4)
    #
    # run(bench, '256kB', 8, 'LRU', 1)
    # run(bench, '256kB', 8, 'LRU', 2)
    # run(bench, '256kB', 8, 'LRU', 8)
    # run(bench, '256kB', 8, 'LRU', 16)

    # run(bench, '256kB', 8, 'IbRDP', 4)
    run(bench, '256kB', 8, 'RRIP', 4)

# run_experiments('blackscholes')
# run_experiments('bodytrack')
# run_experiments('canneal')
# run_experiments('dedup')
run_experiments('facesim')
# run_experiments('ferret')
# run_experiments('fluidanimate')
# run_experiments('freqmine')
# run_experiments('streamcluster')
# run_experiments('swaptions')
# run_experiments('vips')
# run_experiments('x264')
