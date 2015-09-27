#!/usr/bin/python

#
# A Python script to generate all common-case runscripts for parsec 2.1 benchmarks.
#
# Copyright (C) Min Cai 2015
#

import os

# benches = ['blackscholes', 'bodytrack', 'canneal', 'dedup', 'facesim',
#            'ferret', 'fluidanimate', 'freqmine', 'streamcluster',
#            'swaptions', 'vips', 'x264', 'rtview']
benches = ['blackscholes']

# num_threads = [1, 2, 4, 8, 16, 32]
num_threads = [4]

for bench in benches:
    for num_thread in num_threads:
        cmd_first_run = 'build/X86_MESI_Two_Level/gem5.debug configs/example/fs.py --num-cpus=' \
                        + str(num_thread) + ' --script=ext/parsec/2.1/run_scripts/' \
                        + bench + '_' + str(num_thread) + 'c_simsmall_chkpts.rcS'
        os.system(cmd_first_run)

        cmd_second_run = 'build/X86_MESI_Two_Level/gem5.debug configs/example/fs.py --cpu-type=timing --num-cpus=' \
                         + str(num_thread) \
                         + ' --caches --l2cache --num-l2caches=' \
                         + str(num_thread) \
                         + ' --l1d_size=32kB --l1i_size=32kB --l2_size=256kB --checkpoint-restore=1'
        os.system(cmd_second_run)