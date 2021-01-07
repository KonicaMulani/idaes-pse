##############################################################################
# Institute for the Design of Advanced Energy Systems Process Systems
# Engineering Framework (IDAES PSE Framework) Copyright (c) 2018-2020, by the
# software owners: The Regents of the University of California, through
# Lawrence Berkeley National Laboratory,  National Technology & Engineering
# Solutions of Sandia, LLC, Carnegie Mellon University, West Virginia
# University Research Corporation, et al. All rights reserved.
#
# Please see the files COPYRIGHT.txt and LICENSE.txt for full copyright and
# license information, respectively. Both files are also available online
# at the URL "https://github.com/IDAES/idaes-pse".
##############################################################################
import sys
import os
sys.path.append(os.path.abspath('..')) # current folder is ~/tests
import numpy as np
import pandas as pd
import pytest
from pytest import approx
from mock import patch
from idaes.apps.uncertainty_propagation.uncertainties import quantify_propagate_uncertainty, propagate_uncertainty, get_sensitivity
from pyomo.opt import SolverFactory
from pyomo.environ import *
import pyomo.contrib.parmest.parmest as parmest

ipopt_available = SolverFactory('ipopt').available()
kaug_available = SolverFactory('k_aug').available()
dotsens_available = SolverFactory('dot_sens').available()

class TestUncertaintyPropagation:

    @pytest.mark.unit
    @pytest.mark.skipif(not ipopt_available, reason="The 'ipopt' command is not available")
    @pytest.mark.skipif(not ipopt_available, reason="The 'k_aug' command is not available")
    @pytest.mark.skipif(not ipopt_available, reason="The 'dot_sens' command is not available")
    def test_quantify_propagate_uncertainty1(self):
        from idaes.apps.uncertainty_propagation.examples.rooney_biegler import rooney_biegler_model,rooney_biegler_model_opt
        variable_name = ['asymptote', 'rate_constant']
        data = pd.DataFrame(data=[[1,8.3],[2,10.3],[3,19.0],
                                  [4,16.0],[5,15.6],[7,19.8]],
                            columns=['hour', 'y'])
        def SSE(model, data):
            expr = sum((data.y[i] - model.response_function[data.hour[i]])**2 for i in data.index)
            return expr
    
        obj, theta, cov, propagation_f, propagation_c =  quantify_propagate_uncertainty(rooney_biegler_model,rooney_biegler_model_opt, data, variable_name, SSE)

        assert obj == approx(4.331711213656886)
        assert theta[variable_name[0]] == approx(19.142575284617866)
        assert theta[variable_name[1]] == approx(0.53109137696521)
        assert cov == approx(np.array([[6.30579403, -0.4395341], [-0.4395341, 0.04193591]]))
        assert propagation_f['objective'] == approx(5.45439337747349)
        assert propagation_c == {}
        
        
    def test_quantify_propagate_uncertainty2(self):
        from idaes.apps.uncertainty_propagation.examples.rooney_biegler import rooney_biegler_model
        variable_name = ['asymptote', 'rate_constant']
        data = pd.DataFrame(data=[[1,8.3],[2,10.3],[3,19.0],
                                  [4,16.0],[5,15.6],[7,19.8]],
                            columns=['hour', 'y'])
        def SSE(model, data):
            expr = sum((data.y[i] - model.response_function[data.hour[i]])**2 for i in data.index)
            return expr
        model_uncertain= ConcreteModel()
        model_uncertain.asymptote = Var(initialize = 15)
        model_uncertain.rate_constant = Var(initialize = 0.5)
        model_uncertain.obj = Objective(expr = model_uncertain.asymptote*( 1 - exp(-model_uncertain.rate_constant*10  )  ), sense=minimize)

        obj, theta, cov, propagation_f, propagation_c =  quantify_propagate_uncertainty(rooney_biegler_model,model_uncertain, data, variable_name, SSE)

        assert obj == approx(4.331711213656886)
        assert theta[variable_name[0]] == approx(19.142575284617866)
        assert theta[variable_name[1]] == approx(0.53109137696521)
        assert cov == approx(np.array([[6.30579403, -0.4395341], [-0.4395341, 0.04193591]]))
        assert propagation_f['objective'] == approx(5.45439337747349)
        assert propagation_c == {}
    
    def test_propagate_uncertainty(self):
        from idaes.apps.uncertainty_propagation.examples.rooney_biegler import rooney_biegler_model
        variable_name = ['asymptote', 'rate_constant']
        data = pd.DataFrame(data=[[1,8.3],[2,10.3],[3,19.0],
                                  [4,16.0],[5,15.6],[7,19.8]],
                            columns=['hour', 'y'])
        def SSE(model, data):
            expr = sum((data.y[i] - model.response_function[data.hour[i]])**2 for i in data.index)
            return expr
        parmest_class = parmest.Estimator(rooney_biegler_model, data,variable_name,SSE)
        obj, theta, cov = parmest_class.theta_est(calc_cov=True)
        model_uncertain= ConcreteModel()
        model_uncertain.asymptote = Var(initialize = 15)
        model_uncertain.rate_constant = Var(initialize = 0.5)
        model_uncertain.obj = Objective(expr = model_uncertain.asymptote*( 1 - exp(-model_uncertain.rate_constant*10  )  ), sense=minimize)

        propagation_f, propagation_c =  propagate_uncertainty(model_uncertain, theta, cov, variable_name)

        assert propagation_f['objective'] == approx(5.45439337747349)
        assert propagation_c == {}
        
    def test_get_sensitivity(self):
        from idaes.apps.uncertainty_propagation.examples.rooney_biegler import rooney_biegler_model
        variable_name = ['asymptote', 'rate_constant']
        data = pd.DataFrame(data=[[1,8.3],[2,10.3],[3,19.0],
                                  [4,16.0],[5,15.6],[7,19.8]],
                            columns=['hour', 'y'])
        def SSE(model, data):
            expr = sum((data.y[i] - model.response_function[data.hour[i]])**2 for i in data.index)
            return expr
        parmest_class = parmest.Estimator(rooney_biegler_model, data,variable_name,SSE)
        obj, theta, cov = parmest_class.theta_est(calc_cov=True)
        model_uncertain= ConcreteModel()
        model_uncertain.asymptote = Var(initialize = 15)
        model_uncertain.rate_constant = Var(initialize = 0.5)
        model_uncertain.obj = Objective(expr = model_uncertain.asymptote*( 1 - exp(-model_uncertain.rate_constant*10  )  ), sense=minimize)
        theta= {'asymptote': 19.142575284617866, 'rate_constant': 0.53109137696521}
        for v in variable_name:
            getattr(model_uncertain, v).setlb(theta[v])
            getattr(model_uncertain, v).setub(theta[v])
        gradient_f, gradient_c, line_dic =  get_sensitivity(model_uncertain, variable_name)
        
        assert gradient_f == approx(np.array([0.99506259, 0.945148]))
        assert gradient_c == approx(np.array([[-1000, -1000, -1000]]))
        assert line_dic['asymptote'] == approx(1)
        assert line_dic['rate_constant'] == approx(2)
        
    
    @pytest.mark.unit
    @pytest.mark.skipif(not ipopt_available, reason="The 'ipopt' command is not available")
    @pytest.mark.skipif(not ipopt_available, reason="The 'k_aug' command is not available")
    @pytest.mark.skipif(not ipopt_available, reason="The 'dot_sens' command is not available")
    def test_quantify_propagate_uncertainty_NRTL(self):
        from idaes.apps.uncertainty_propagation.examples.NRTL_model_scripts import NRTL_model, NRTL_model_opt
        variable_name = ["fs.properties.tau['benzene','toluene']", "fs.properties.tau['toluene','benzene']"]
        current_path = os.path.dirname(os.path.realpath(__file__))
        data = pd.read_csv(os.path.join(current_path, 'BT_NRTL_dataset.csv'))
        def SSE(model, data):
            expr = ((float(data["vap_benzene"]) -
                     model.fs.flash.vap_outlet.mole_frac_comp[0, "benzene"])**2 +
                    (float(data["liq_benzene"]) -
                     model.fs.flash.liq_outlet.mole_frac_comp[0, "benzene"])**2)
            return expr*1E4
        obj, theta, cov, propagation_f, propagation_c =  quantify_propagate_uncertainty(NRTL_model,NRTL_model_opt, data, variable_name, SSE)

        assert obj == approx(0.004663348837044143)
        assert theta[variable_name[0]] == approx( 0.4781086784101746)
        assert theta[variable_name[1]] == approx( -0.40924465377598657)
        assert cov == approx(np.array([[0.00213426, -0.00163064], [-0.00163064, 0.00124591]]))
        assert propagation_f['objective'] == approx(0.00014)
        assert propagation_c['constraints 4'] == approx(0.000084)
        assert propagation_c['constraints 5'] == approx(0.00025)
        assert propagation_c['constraints 6'] == approx(0.00082)
        assert propagation_c['constraints 7'] == approx(0.00017)
        assert propagation_c['constraints 8'] == approx(0.00052)
        assert propagation_c['constraints 9'] == approx(0.00025)















    @pytest.mark.unit
    @pytest.mark.skipif(not ipopt_available, reason="The 'ipopt' command is not available")
    @pytest.mark.skipif(not ipopt_available, reason="The 'k_aug' command is not available")
    @pytest.mark.skipif(not ipopt_available, reason="The 'dot_sens' command is not available")
    def test_Exception1(self):
        from idaes.apps.uncertainty_propagation.examples.rooney_biegler import rooney_biegler_model,rooney_biegler_model_opt
        variable_name = ['asymptote', 'rate_constant']
        data = pd.DataFrame(data=[[1,8.3],[2,10.3],[3,19.0],
                                  [4,16.0],[5,15.6],[7,19.8]],
                            columns=['hour', 'y'])
        def SSE(model, data):
            expr = sum((data.y[i] - model.response_function[data.hour[i]])**2 for i in data.index)
            return expr
        tee = 1
        with pytest.raises(Exception):
            obj, theta, cov, propagation_f, propagation_c =  quantify_propagate_uncertainty(rooney_biegler_model,rooney_biegler_model_opt, data, variable_name, SSE,tee)


    @pytest.mark.unit
    @pytest.mark.skipif(not ipopt_available, reason="The 'ipopt' command is not available")
    @pytest.mark.skipif(not ipopt_available, reason="The 'k_aug' command is not available")
    @pytest.mark.skipif(not ipopt_available, reason="The 'dot_sens' command is not available")
    def test_Exception2(self):
        from idaes.apps.uncertainty_propagation.examples.rooney_biegler import rooney_biegler_model,rooney_biegler_model_opt
        variable_name = ['asymptote', 'rate_constant']
        data = pd.DataFrame(data=[[1,8.3],[2,10.3],[3,19.0],
                                  [4,16.0],[5,15.6],[7,19.8]],
                            columns=['hour', 'y'])
        def SSE(model, data):
            expr = sum((data.y[i] - model.response_function[data.hour[i]])**2 for i in data.index)
            return expr
        tee = False
        diagnostic_mode = 1
        with pytest.raises(Exception):
            obj, theta, cov, propagation_f, propagation_c =  quantify_propagate_uncertainty(rooney_biegler_model,rooney_biegler_model_opt, data, variable_name, SSE,tee,diagnostic_mode)


    @pytest.mark.unit
    @pytest.mark.skipif(not ipopt_available, reason="The 'ipopt' command is not available")
    @pytest.mark.skipif(not ipopt_available, reason="The 'k_aug' command is not available")
    @pytest.mark.skipif(not ipopt_available, reason="The 'dot_sens' command is not available")
    def test_Exception3(self):
        from idaes.apps.uncertainty_propagation.examples.rooney_biegler import rooney_biegler_model,rooney_biegler_model_opt
        variable_name = ['asymptote', 'rate_constant']
        data = pd.DataFrame(data=[[1,8.3],[2,10.3],[3,19.0],
                                  [4,16.0],[5,15.6],[7,19.8]],
                            columns=['hour', 'y'])
        def SSE(model, data):
            expr = sum((data.y[i] - model.response_function[data.hour[i]])**2 for i in data.index)
            return expr
        tee = False
        diagnostic_mode = False
        solver_options = [1e-8]
        with pytest.raises(Exception):
            obj, theta, cov, propagation_f, propagation_c =  quantify_propagate_uncertainty(rooney_biegler_model,rooney_biegler_model_opt, data, variable_name, SSE,tee,diagnostic_mode,solver_options)
