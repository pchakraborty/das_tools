"""TODO: Add module docstring"""
import os
from collections import OrderedDict
from functools import reduce
import numpy as np
import netCDF4 as nc4
import gmao_tools as gt
import yaml

class Obs():
    """
    Add class docstring
    """
    def __init__(self, filename, mask_expr=None, verbose=False):
        self.filename = filename
        self._verbose = verbose
        self._mask_expr = mask_expr
        # Dict mapping short to long names
        this_dir = os.path.dirname(os.path.realpath(__file__))
        with open(os.path.join(this_dir, "short_to_long_names.yaml"), "r") as fin:
            self._short_to_long = yaml.safe_load(fin)
        # List of derived variables with dependecies
        self._derived_vars = {
            "amb":        {"func": Obs._subtract, "deps": ["omf", "oma"]},
            "sigo_input": {"func": Obs._whatchamacallit, "deps": ["Errinv_Input"]},
            "sigo_final": {"func": Obs._whatchamacallit, "deps": ["Errinv_Final"]},
            "sigo":       {"func": Obs._whatchamacallit, "deps": ["Errinv_Final"]}
        }

    def get_var(self, var_name, mask_expr=None):
        """
        Retrieve variable var_name, masked by the expression mask_expr.
        Here, mask_expr is a string of the form: "(used==1)"
        """
        if var_name in self._derived_vars:
            if self._verbose:
                print(self._derived_vars[var_name])
            deps = self._derived_vars[var_name]["deps"]
            function2call = self._derived_vars[var_name]["func"]
            data = OrderedDict()
            for myvar in deps: # cannot use comprehension w/ OrderedDict
                data[myvar] = self._get_single_var(myvar, mask_expr)
            return function2call(data)
        else:
            return self._get_single_var(var_name, mask_expr)

    @staticmethod
    def _subtract(data):
        """
        data is an OrderedDict of the form
        {key0: some numpy.ndarray object, key1: another numpy.ndarray object}
        return data[key0] - data[key1]
        """
        if not isinstance(data, OrderedDict):
            raise ValueError("Input data is of type {}, not OrderedDict".format(type(data)))
        if len(data) != 2:
            raise ValueError("Expected exactly 2 entries")
        data_values = list(data.values())
        return data_values[0] - data_values[1]

    @staticmethod
    def _whatchamacallit(data):
        """data is an OrderedDict containing a single key whose value is a numpy.ndarray"""
        if not isinstance(data, OrderedDict):
            raise ValueError("Input data is of type {}, not OrderedDict".format(type(data)))
        if len(data) != 1:
            raise ValueError("Expected a single entry in this OrderedDict")
        vardata = data[next(iter(data))]
        val = 1./vardata
        mask = val > 9999.
        val[mask] = -9999.9
        return val

    @staticmethod
    def _check_mask_expr_format(mask_expr):
        # mask_expr needs to be in the format (somestring==somevalue)
        if not mask_expr.startswith("(") or \
           not mask_expr.endswith(")") or \
           "==" not in mask_expr:
            raise ValueError(
                "mask expr \"%s\" is not of the form %s"
                % (mask_expr, "(some_string==some_value)"
                  )
            )

    def _parse_mask_expr(self, mask_expr):
        Obs._check_mask_expr_format(mask_expr)
        mask_name, mask_value = mask_expr[
            mask_expr.find("(")+1:mask_expr.find(")")
        ].split("==")
        if self._verbose:
            print("mask: {} => {}, {}".format(mask_expr, mask_name, mask_value))
        return (mask_name, mask_value)

    def _get_long_name(self, short_var_name):
        long_var_name = short_var_name
        if short_var_name in self._short_to_long:
            long_var_name = self._short_to_long[short_var_name]
        return long_var_name

    def _get_single_var(self, var_name, mask_expr):
        if not mask_expr:
            mask_expr = self._mask_expr
        var_name_long = self._get_long_name(var_name)
        with nc4.Dataset(self.filename, "r") as fin:
            mydata = fin.variables[var_name_long][:]
            if mask_expr:
                (mask_name, mask_value) = self._parse_mask_expr(mask_expr)
                mask_name_long = self._get_long_name(mask_name)
                mask = fin.variables[mask_name_long][:] == float(mask_value)
                mydata = mydata[mask]
        return mydata

class ObsTemplate():

    def __init__(self, filename_tmpl, datetime_interval=None, verbose=False):
        self._filename_tmpl = filename_tmpl
        self._verbose = verbose
        self._datetime_interval = datetime_interval

    def get_var(self, var_name, datetime_interval=None, datetime_list=None, hr_inc=6, mask_expr=None):
        ndates = self._get_ndates(datetime_interval, datetime_list, hr_inc)
        dt_list = gt.ndate_to_dt(ndates) # string to datetime objects
        if self._verbose:
            print("date/time list: {}".format(dt_list))
        data = np.array([])
        for idt in dt_list:
            filename = self._get_filename_from_tmpl(idt)
            obs = Obs(filename, mask_expr=mask_expr, verbose=self._verbose)
            data = np.append(data, obs.get_var(var_name), axis=0)
        return data

    def _get_ndates(self, datetime_interval, datetime_list, hr_inc):
        if (datetime_interval) and (not datetime_list):
            startdate, enddate = datetime_interval
            ndates = gt.get_ndate_timeseries(startdate, enddate, hr_inc=hr_inc)
        elif (not datetime_interval) and datetime_list:
            ndates = datetime_list
        elif (not datetime_interval) and (not datetime_list) and (self._datetime_interval):
            startdate, enddate = self._datetime_interval
            ndates = gt.get_ndate_timeseries(startdate, enddate, hr_inc=hr_inc)
        else:
            raise ValueError("Error in evaluating list of datetimes")
        return ndates

    def _get_filename_from_tmpl(self, dattim):
        from string import Template
        tmplt = Template(self._filename_tmpl)
        filename = tmplt.safe_substitute( # pchakrab: Shouldn't we use substitute?
            yyyy=dattim.strftime('%Y'),
            mm=dattim.strftime('%m'),
            dd=dattim.strftime('%d'),
            hh=dattim.strftime('%H')
        )
        if self._verbose:
            print('filename: {}'.format(filename))
        return filename
