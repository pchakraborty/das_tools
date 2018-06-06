#!/usr/bin/env python
"""Unit tests for ecfseteup.py"""

# import shutil
# import filecmp
# import glob
# from datetime import datetime
# import ecfsetup
# import subprocess as sp

import unittest
import os
import sys
import ncdiag as ncd
import matplotlib.pyplot as plt

class TestNcdiag(unittest.TestCase):
    """
    TODO: add docstring
    """

    def setUp(self):
        this_file = os.path.abspath(__file__)
        self.this_dir = os.path.dirname(this_file)
        sys.path.append(os.path.dirname(self.this_dir))

    def test_ncdiag_obs(self):
        """
        TODO: add docstring
        """
        filename = os.path.join(
            self.this_dir,
            "input",
            "f517_fp.diag_conv_ps_mrg.20180220_12z.nc4")
        obs = ncd.Obs(filename, verbose=True)
        varlist = ["omf", "oma", "amb"]
        for myvar in varlist:
            print("Plot all O-Fs for all used obs")
            plt.plot(obs.get_var(myvar))
            plt.title(myvar)
            plt.show()

    def test_ncdiag_obs_template(self):
        """
        TODO: add docstring
        """
        filetmpl = os.path.join(
            self.this_dir,
            "input",
            "f517_fp.diag_conv_ps_mrg.$yyyy$mm${dd}_${hh}z.nc4")

        obs_tmpl = ncd.ObsTemplate(
            filetmpl,
            datetime_interval=(2018022012, 2018022100),
            verbose=True)
        print("Retrieve data from multiple files by a template and plot...")
        # plot 1
        plt.plot(obs_tmpl.get_var("omf"))
        plt.title("O-F - no masking")
        plt.show()
        # plot 2
        mask_expr = "(used==1)"
        plt.plot(obs_tmpl.get_var("omf", mask_expr=mask_expr))
        plt.title("O-F - with masking {}".format(mask_expr))
        plt.show()
        
    def tearDown(self):
        pass


if __name__ == "__main__":
    unittest.main()
