"""
Unit tests for the spade module.

:copyright: Copyright 2014-2016 by the Elephant team, see `doc/authors.rst`.
:license: Modified BSD, see LICENSE.txt for details.
"""
from __future__ import division

import sys
import unittest

import neo
import numpy as np
import quantities as pq
from numpy.testing.utils import assert_array_equal

import elephant.conversion as conv
import elephant.spade as spade
import elephant.spike_train_generation as stg
from elephant.spade import HAVE_FIM

python_version_major = sys.version_info.major


class SpadeTestCase(unittest.TestCase):
    def setUp(self):
        # Spade parameters
        self.binsize = 1 * pq.ms
        self.winlen = 10
        self.n_subset = 10
        self.n_surr = 10
        self.alpha = 0.05
        self.stability_thresh = [0.1, 0.1]
        self.psr_param = [0, 0, 0]
        self.min_occ = 4
        self.min_spikes = 4
        self.max_occ = 4
        self.max_spikes = 4
        self.min_neu = 4
        # Test data parameters
        # CPP parameters
        self.n_neu = 100
        self.amplitude = [0] * self.n_neu + [1]
        self.cpp = stg.cpp(rate=3 * pq.Hz, A=self.amplitude, t_stop=5 * pq.s)
        # Number of patterns' occurrences
        self.n_occ1 = 10
        self.n_occ2 = 12
        self.n_occ3 = 15
        # Patterns lags
        self.lags1 = [2]
        self.lags2 = [1, 2]
        self.lags3 = [1, 2, 3, 4, 5]
        # Length of the spiketrain
        self.t_stop = 3000
        # Patterns times
        self.patt1_times = neo.SpikeTrain(
            np.arange(
                0, 1000, 1000 // self.n_occ1)[:-1] *
            pq.ms, t_stop=self.t_stop * pq.ms)
        self.patt2_times = neo.SpikeTrain(
            np.arange(
                1000, 2000, 1000 // self.n_occ2)[:-1] *
            pq.ms, t_stop=self.t_stop * pq.ms)
        self.patt3_times = neo.SpikeTrain(
            np.arange(
                2000, 3000, 1000 // self.n_occ3)[:-1] *
            pq.ms, t_stop=self.t_stop * pq.ms)
        # Patterns
        self.patt1 = [self.patt1_times] + [neo.SpikeTrain(
            self.patt1_times.view(pq.Quantity) + l * pq.ms,
            t_stop=self.t_stop * pq.ms) for l in self.lags1]
        self.patt2 = [self.patt2_times] + [neo.SpikeTrain(
            self.patt2_times.view(pq.Quantity) + l * pq.ms,
            t_stop=self.t_stop * pq.ms) for l in self.lags2]
        self.patt3 = [self.patt3_times] + [neo.SpikeTrain(
            self.patt3_times.view(pq.Quantity) + l * pq.ms,
            t_stop=self.t_stop * pq.ms) for l in self.lags3]
        # Data
        self.msip = self.patt1 + self.patt2 + self.patt3
        # Expected results
        self.n_spk1 = len(self.lags1) + 1
        self.n_spk2 = len(self.lags2) + 1
        self.n_spk3 = len(self.lags3) + 1
        self.elements1 = list(range(self.n_spk1))
        self.elements2 = list(range(self.n_spk2))
        self.elements3 = list(range(self.n_spk3))
        self.elements_msip = [
            self.elements1,
            list(
                range(
                    self.n_spk1,
                    self.n_spk1 +
                    self.n_spk2)),
            list(
                range(
                    self.n_spk1 +
                    self.n_spk2,
                    self.n_spk1 +
                    self.n_spk2 +
                    self.n_spk3))]
        self.occ1 = np.unique(conv.BinnedSpikeTrain(
            self.patt1_times, self.binsize).spike_indices[0])
        self.occ2 = np.unique(conv.BinnedSpikeTrain(
            self.patt2_times, self.binsize).spike_indices[0])
        self.occ3 = np.unique(conv.BinnedSpikeTrain(
            self.patt3_times, self.binsize).spike_indices[0])
        self.occ_msip = [
            list(self.occ1), list(self.occ2), list(self.occ3)]
        self.lags_msip = [self.lags1, self.lags2, self.lags3]
        self.patt_psr = self.patt3 + [self.patt3[-1][:3]]

    # Testing cpp
    @unittest.skipUnless(HAVE_FIM, "Time consuming with pythonic FIM")
    def test_spade_cpp(self):
        output_cpp = spade.spade(self.cpp, self.binsize, 1,
                                 n_subsets=self.n_subset,
                                 stability_thresh=self.stability_thresh,
                                 n_surr=self.n_surr, alpha=self.alpha,
                                 psr_param=self.psr_param,
                                 output_format='patterns')['patterns']
        elements_cpp = []
        lags_cpp = []
        # collecting spade output
        for out in output_cpp:
            elements_cpp.append(sorted(out['neurons']))
            lags_cpp.append(list(out['lags'].magnitude))
        # check neurons in the patterns
        assert_array_equal(elements_cpp, [range(self.n_neu)])
        # check the lags
        assert_array_equal(lags_cpp, [np.array([0] * (self.n_neu - 1))])

    # Testing spectrum cpp
    def test_spade_spectrum_cpp(self):
        # Computing Spectrum
        spectrum_cpp = spade.concepts_mining(self.cpp, self.binsize,
                                             1, report='#')[0]
        # Check spectrum
        assert_array_equal(
            spectrum_cpp, [
                (len(
                    self.cpp), np.sum(
                    conv.BinnedSpikeTrain(
                        self.cpp[0], self.binsize).to_bool_array()), 1)])

    # Testing with multiple patterns input
    def test_spade_msip(self):
        output_msip = spade.spade(self.msip, self.binsize, self.winlen,
                                  n_subsets=self.n_subset,
                                  stability_thresh=self.stability_thresh,
                                  n_surr=self.n_surr, alpha=self.alpha,
                                  psr_param=self.psr_param,
                                  output_format='patterns')['patterns']
        elements_msip = []
        occ_msip = []
        lags_msip = []
        # collecting spade output
        for out in output_msip:
            elements_msip.append(out['neurons'])
            occ_msip.append(list(out['times'].magnitude))
            lags_msip.append(list(out['lags'].magnitude))
        elements_msip = sorted(elements_msip, key=lambda d: len(d))
        occ_msip = sorted(occ_msip, key=lambda d: len(d))
        lags_msip = sorted(lags_msip, key=lambda d: len(d))
        # check neurons in the patterns
        assert_array_equal(elements_msip, self.elements_msip)
        # check the occurrences time of the patters
        assert_array_equal(occ_msip, self.occ_msip)
        # check the lags
        assert_array_equal(lags_msip, self.lags_msip)

    @unittest.skipUnless(python_version_major == 3, "assertWarns requires 3.2")
    def test_parameters(self):
        """
        Test under different configuration of parameters than the default one
        """
        # test min_spikes parameter
        with self.assertWarns(UserWarning):
            # n_surr=0 and alpha=0.05 spawns expected UserWarning
            output_msip_min_spikes = spade.spade(
                self.msip,
                self.binsize,
                self.winlen,
                min_spikes=self.min_spikes,
                n_subsets=self.n_subset,
                n_surr=0,
                alpha=self.alpha,
                psr_param=self.psr_param,
                output_format='patterns')['patterns']
        # collecting spade output
        elements_msip_min_spikes = []
        for out in output_msip_min_spikes:
            elements_msip_min_spikes.append(out['neurons'])
        elements_msip_min_spikes = sorted(
            elements_msip_min_spikes, key=lambda d: len(d))
        lags_msip_min_spikes = []
        for out in output_msip_min_spikes:
            lags_msip_min_spikes.append(list(out['lags'].magnitude))
            pvalue = out['pvalue']
        lags_msip_min_spikes = sorted(
            lags_msip_min_spikes, key=lambda d: len(d))
        # check the lags
        assert_array_equal(lags_msip_min_spikes, [
            l for l in self.lags_msip if len(l) + 1 >= self.min_spikes])
        # check the neurons in the patterns
        assert_array_equal(elements_msip_min_spikes, [
            el for el in self.elements_msip if len(el) >= self.min_neu and len(
                el) >= self.min_spikes])
        # check that the p-values assigned are equal to -1 (n_surr=0)
        assert_array_equal(-1, pvalue)

        # test min_occ parameter
        output_msip_min_occ = spade.spade(self.msip, self.binsize, self.winlen,
                                          min_occ=self.min_occ,
                                          n_subsets=self.n_subset,
                                          n_surr=self.n_surr, alpha=self.alpha,
                                          psr_param=self.psr_param,
                                          output_format='patterns')['patterns']
        # collect spade output
        occ_msip_min_occ = []
        for out in output_msip_min_occ:
            occ_msip_min_occ.append(list(out['times'].magnitude))
        occ_msip_min_occ = sorted(occ_msip_min_occ, key=lambda d: len(d))
        # test occurrences time
        assert_array_equal(occ_msip_min_occ, [
            occ for occ in self.occ_msip if len(occ) >= self.min_occ])

        # test max_spikes parameter
        output_msip_max_spikes = spade.spade(
            self.msip,
            self.binsize,
            self.winlen,
            max_spikes=self.max_spikes,
            n_subsets=self.n_subset,
            n_surr=self.n_surr,
            alpha=self.alpha,
            psr_param=self.psr_param,
            output_format='patterns')['patterns']
        # collecting spade output
        elements_msip_max_spikes = []
        for out in output_msip_max_spikes:
            elements_msip_max_spikes.append(out['neurons'])
        elements_msip_max_spikes = sorted(
            elements_msip_max_spikes, key=lambda d: len(d))
        lags_msip_max_spikes = []
        for out in output_msip_max_spikes:
            lags_msip_max_spikes.append(list(out['lags'].magnitude))
        lags_msip_max_spikes = sorted(
            lags_msip_max_spikes, key=lambda d: len(d))
        # check the lags
        assert_array_equal([len(lags) < self.max_spikes for lags in
                            lags_msip_max_spikes], [True] * len(
            lags_msip_max_spikes))

        # test max_occ parameter
        output_msip_max_occ = spade.spade(self.msip, self.binsize, self.winlen,
                                          max_occ=self.max_occ,
                                          n_subsets=self.n_subset,
                                          n_surr=self.n_surr, alpha=self.alpha,
                                          psr_param=self.psr_param,
                                          output_format='patterns')['patterns']
        # collect spade output
        occ_msip_max_occ = []
        for out in output_msip_max_occ:
            occ_msip_max_occ.append(list(out['times'].magnitude))
        occ_msip_max_occ = sorted(occ_msip_max_occ, key=lambda d: len(d))
        # test occurrences time
        assert_array_equal(occ_msip_max_occ, [
            occ for occ in self.occ_msip if len(occ) <= self.max_occ])

    # test to compare the python and the C implementation of FIM
    # skip this test if C code not available
    @unittest.skipIf(not HAVE_FIM, 'Requires fim.so')
    def test_fpgrowth_fca(self):
        print("fim.so is found.")
        binary_matrix = conv.BinnedSpikeTrain(
            self.patt1, self.binsize).to_bool_array()
        context, transactions, rel_matrix = spade._build_context(
            binary_matrix, self.winlen)
        # mining the data with python fast_fca
        mining_results_fpg = spade._fpgrowth(
            transactions,
            rel_matrix=rel_matrix)
        # mining the data with C fim
        mining_results_ffca = spade._fast_fca(context)

        # testing that the outputs are identical
        assert_array_equal(sorted(mining_results_ffca[0][0]), sorted(
            mining_results_fpg[0][0]))
        assert_array_equal(sorted(mining_results_ffca[0][1]), sorted(
            mining_results_fpg[0][1]))

    # Tests 3d spectrum
    # Testing with multiple patterns input
    def test_spade_msip_3d(self):
        output_msip = spade.spade(self.msip, self.binsize, self.winlen,
                                  n_subsets=self.n_subset,
                                  stability_thresh=self.stability_thresh,
                                  n_surr=self.n_surr, spectrum='3d#',
                                  alpha=self.alpha, psr_param=self.psr_param,
                                  output_format='patterns')['patterns']
        elements_msip = []
        occ_msip = []
        lags_msip = []
        # collecting spade output
        for out in output_msip:
            elements_msip.append(out['neurons'])
            occ_msip.append(list(out['times'].magnitude))
            lags_msip.append(list(out['lags'].magnitude))
        elements_msip = sorted(elements_msip, key=lambda d: len(d))
        occ_msip = sorted(occ_msip, key=lambda d: len(d))
        lags_msip = sorted(lags_msip, key=lambda d: len(d))
        # check neurons in the patterns
        assert_array_equal(elements_msip, self.elements_msip)
        # check the occurrences time of the patters
        assert_array_equal(occ_msip, self.occ_msip)
        # check the lags
        assert_array_equal(lags_msip, self.lags_msip)

    # test under different configuration of parameters than the default one
    def test_parameters_3d(self):
        # test min_spikes parameter
        output_msip_min_spikes = spade.spade(
            self.msip,
            self.binsize,
            self.winlen,
            min_spikes=self.min_spikes,
            n_subsets=self.n_subset,
            n_surr=self.n_surr,
            spectrum='3d#',
            alpha=self.alpha,
            psr_param=self.psr_param,
            output_format='patterns')['patterns']
        # collecting spade output
        elements_msip_min_spikes = []
        for out in output_msip_min_spikes:
            elements_msip_min_spikes.append(out['neurons'])
        elements_msip_min_spikes = sorted(
            elements_msip_min_spikes, key=lambda d: len(d))
        lags_msip_min_spikes = []
        for out in output_msip_min_spikes:
            lags_msip_min_spikes.append(list(out['lags'].magnitude))
        lags_msip_min_spikes = sorted(
            lags_msip_min_spikes, key=lambda d: len(d))
        # check the lags
        assert_array_equal(lags_msip_min_spikes, [
            l for l in self.lags_msip if len(l) + 1 >= self.min_spikes])
        # check the neurons in the patterns
        assert_array_equal(elements_msip_min_spikes, [
            el for el in self.elements_msip if len(el) >= self.min_neu and len(
                el) >= self.min_spikes])

        # test min_occ parameter
        output_msip_min_occ = spade.spade(self.msip, self.binsize, self.winlen,
                                          min_occ=self.min_occ,
                                          n_subsets=self.n_subset,
                                          n_surr=self.n_surr, spectrum='3d#',
                                          alpha=self.alpha,
                                          psr_param=self.psr_param,
                                          output_format='patterns')['patterns']
        # collect spade output
        occ_msip_min_occ = []
        for out in output_msip_min_occ:
            occ_msip_min_occ.append(list(out['times'].magnitude))
        occ_msip_min_occ = sorted(occ_msip_min_occ, key=lambda d: len(d))
        # test occurrences time
        assert_array_equal(occ_msip_min_occ, [
            occ for occ in self.occ_msip if len(occ) >= self.min_occ])

    # Test computation spectrum
    def test_spectrum(self):
        # test 2d spectrum
        spectrum = spade.concepts_mining(self.patt3, self.binsize,
                                         self.winlen, report='#')[0]
        # test 3d spectrum
        assert_array_equal(spectrum, [[len(self.lags3) + 1, self.n_occ3, 1]])
        spectrum_3d = spade.concepts_mining(self.patt3, self.binsize,
                                            self.winlen, report='3d#')[0]
        assert_array_equal(spectrum_3d, [
            [len(self.lags3) + 1, self.n_occ3, max(self.lags3), 1]])

    def test_spade_raise_error(self):
        # Test list not using neo.Spiketrain
        self.assertRaises(TypeError, spade.spade, [
            [1, 2, 3], [3, 4, 5]], 1 * pq.ms, 4)
        # Test neo.Spiketrain with different t_stop
        self.assertRaises(AttributeError, spade.spade, [neo.SpikeTrain(
            [1, 2, 3] * pq.s, t_stop=5 * pq.s), neo.SpikeTrain(
            [3, 4, 5] * pq.s, t_stop=6 * pq.s)], 1 * pq.ms, 4)
        # Test wrong spectrum parameter
        self.assertRaises(ValueError, spade.spade, [neo.SpikeTrain(
            [1, 2, 3] * pq.s, t_stop=6 * pq.s), neo.SpikeTrain(
            [3, 4, 5] * pq.s, t_stop=6 * pq.s)], 1 * pq.ms, 4, n_surr=1,
                          spectrum='try')
        # Test negative minimum number of spikes
        self.assertRaises(AttributeError, spade.spade, [neo.SpikeTrain(
            [1, 2, 3] * pq.s, t_stop=5 * pq.s), neo.SpikeTrain(
            [3, 4, 5] * pq.s, t_stop=5 * pq.s)], 1 * pq.ms, 4, min_neu=-3)
        # Test negative number of surrogates
        self.assertRaises(AttributeError, spade.pvalue_spectrum, [
            neo.SpikeTrain([1, 2, 3] * pq.s, t_stop=5 * pq.s), neo.SpikeTrain(
                [3, 4, 5] * pq.s, t_stop=5 * pq.s)], 1 * pq.ms, 4, 3 * pq.ms,
                          n_surr=-3)
        # Test wrong correction parameter
        self.assertRaises(AttributeError, spade.test_signature_significance, (
            (2, 3, 0.2), (2, 4, 0.1)), 0.01, corr='try')
        # Test negative number of subset for stability
        self.assertRaises(AttributeError, spade.approximate_stability, (),
                          np.array([]), n_subsets=-3)

    def test_pattern_set_reduction(self):
        output_msip = spade.spade(self.patt_psr, self.binsize, self.winlen,
                                  n_subsets=self.n_subset,
                                  stability_thresh=self.stability_thresh,
                                  n_surr=self.n_surr, spectrum='3d#',
                                  alpha=self.alpha, psr_param=self.psr_param,
                                  output_format='patterns')['patterns']
        elements_msip = []
        occ_msip = []
        lags_msip = []
        # collecting spade output
        for out in output_msip:
            elements_msip.append(sorted(out['neurons']))
            occ_msip.append(list(out['times'].magnitude))
            lags_msip.append(list(out['lags'].magnitude))
        elements_msip = sorted(elements_msip, key=lambda d: len(d))
        occ_msip = sorted(occ_msip, key=lambda d: len(d))
        lags_msip = sorted(lags_msip, key=lambda d: len(d))
        # check neurons in the patterns
        assert_array_equal(elements_msip, [range(len(self.lags3) + 1)])
        # check the occurrences time of the patters
        assert_array_equal(len(occ_msip[0]), self.n_occ3)


def suite():
    suite = unittest.makeSuite(SpadeTestCase, 'test')
    return suite


if __name__ == "__main__":
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite())
