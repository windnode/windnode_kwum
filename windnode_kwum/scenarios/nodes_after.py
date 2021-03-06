import oemof.solph as solph
import oemof
from glob import glob
import os

#from windnode_kwum.scenarios.costs_TS import costs_sum
from windnode_kwum.tools import config
import oemof.outputlib as outputlib
from oemof.outputlib import processing, views
scenario_name = 'reference_scenario_curtailment'
import matplotlib.pyplot as plt
import pandas as pd
import csv
import pdb
# get results_path
path = os.path.join(config.get_data_root_dir(),
                    config.get('user_dirs',
                               'results_dir'))

esys = solph.EnergySystem()
file = scenario_name + '.oemof'
esys.restore(dpath=path,
             filename=file)

results = esys.results
#print('results:', results)


busList = [item for item in esys.nodes if isinstance(item, oemof.solph.network.Bus)]
busColorObject = {}
for bus in busList:
    busColorObject[bus.label] = '#cd3333'


# Find the current file path for reference_scenario_curtailment.py
dirpath = os.getcwd()



####################################################

import logging

import math

logger = logging.getLogger('windnode_kwum')

import oemof.solph as solph
import pandas as pd
import os
from dateutil.parser import parse

from windnode_kwum.tools import config

from windnode_kwum.tools.data import oemof_nodes_from_excel
from windnode_kwum.tools.config import get_data_root_dir

from windnode_kwum.scenarios.reference_scenario_curtailment import executeMain
"""Create nodes (oemof objects) from node dict

Parameters
----------
nd : :obj:`dict`
    Nodes data
datetime_index :
    Datetime index

Returns
-------
nodes : `obj`:dict of :class:`nodes <oemof.network.Node>`
"""


# # build dict nodes and parameters from column names
# ts = {col: dict([tuple(col.split('.'))])
#       for col in nd['timeseries'].columns.values}


cfg = {
    'data_path': os.path.join(os.path.dirname(__file__), 'data'),
    'date_from': '2016-02-01 00:00:00',
    'date_to': '2016-03-01 00:00:00',
    'freq': '60min',
    'scenario_file': 'no_flex.xlsx',
    'data_file': 'reference_scenario_curtailment_data.xlsx',
    'results_path': os.path.join(config.get_data_root_dir(),
                                 config.get('user_dirs',
                                            'results_dir')),
    'solver': 'cbc',
    'verbose': True,
    'dump': False}



# read nodes data
nd = oemof_nodes_from_excel(
    scenario_file=os.path.join(cfg['data_path'],
                               cfg['scenario_file']),
    data_file=os.path.join(get_data_root_dir(),
                           config.get('user_dirs', 'data_dir'),
                           cfg['data_file'])
)

# Create time index
datetime_index = pd.date_range(start=cfg['date_from'],
                               end=cfg['date_to'],
                               freq=cfg['freq'])


nodes = []
v_c = {}

# Create Bus objects from buses table
busd = {}

for i, b in nd['buses'].iterrows():
    if b['active']:
        bus = solph.Bus(label=b['label'])
        nodes.append(bus)

        busd[b['label']] = bus
        if b['excess']:
            nodes.append(
                solph.Sink(label=b['label'] + '_excess',
                           inputs={busd[b['label']]: solph.Flow(
                               variable_costs=b['excess costs'])})
            )
        if b['shortage']:
            nodes.append(
                solph.Source(label=b['label'] + '_shortage',
                             outputs={busd[b['label']]: solph.Flow(
                                 variable_costs=b['shortage costs'])})
                )

# Create Source objects from table 'commodity sources'
for i, cs in nd['commodity_sources'].iterrows():
    if cs['active']:
        # set static outflow values from the commodity sources tab in the excel file
        outflow_args = {'nominal_value': cs['capacity'],
                        'variable_costs': cs['variable_costs']}

        # get time series for node and parameter
        # Parameters pre-set in outflow_args will be overwritten if a time series is available
        for col in nd['timeseries'].columns.values:
            if col.split('.')[0] == cs['label']:
                outflow_args[col.split('.')[1]] = nd['timeseries'][col][datetime_index]

        print(cs['label'], outflow_args)

        nodes.append(
            solph.Source(label=cs['label'],
                         outputs={busd[cs['to']]: solph.Flow(**outflow_args)})
        )

# Create Source objects with fixed time series from 'renewables' table
for i, re in nd['renewables'].iterrows():
    if re['active']:
        # set static outflow values
        outflow_args = {'nominal_value': re['capacity'],
                        'fixed': True}
        # get time series for node and parameter
        for col in nd['timeseries'].columns.values:
            if col.split('.')[0] == re['label']:
                outflow_args[col.split('.')[1]] = nd['timeseries'][col][datetime_index]

        print(re['label'], outflow_args)

        # create
        nodes.append(
            solph.Source(label=re['label'],
                         outputs={busd[re['to']]: solph.Flow(**outflow_args)})
        )

# Create Sink objects with fixed time series from 'demand' table
for i, de in nd['demand'].iterrows():
    if de['active']:
        # set static inflow values
        inflow_args = {'nominal_value': de['nominal value'],
                       'fixed': de['fixed']}

        # look for the fixed variable_costs fixture in demand table
        if not math.isnan(de['variable_costs']):
            inflow_args['variable_costs'] = de['variable_costs']

        # get time series for node and parameter
        for col in nd['timeseries'].columns.values:
            if col.split('.')[0] == de['label']:
                inflow_args[col.split('.')[1]] = nd['timeseries'][col][datetime_index]

        print(de['label'], inflow_args)


        # create
        nodes.append(
            solph.Sink(label=de['label'],
                       inputs={busd[de['from']]: solph.Flow(**inflow_args)})
        )

# Create Transformer objects from 'transformers' table
for i, t in nd['transformers'].iterrows():
    if t['active']:
        # set static inflow values
        inflow_args = {'variable_costs': t['variable_costs']}
        outflow_args = {'nominal_value': t['capacity'],
                        'fixed': t['fixed']}
        # get time series for inflow of transformer
        # Parameters pre-set in outflow_args will be overwritten if a time series is available
        for col in nd['timeseries'].columns.values:
            if col.split('.')[0] == t['label']:
                outflow_args[col.split('.')[1]] = nd['timeseries'][col][datetime_index]
        for bus in busList:
            # get bus from results
            bus_results = views.node(results, bus.label)
            bus_results_flows = bus_results['sequences']
            #v_c[bus] = inflow_args['variable_costs']
            flow = pd.Series(bus_results_flows.iloc[:, 0])
            costs={}
            for i in flow.index:
                costs[i] = t['label'],inflow_args['variable_costs'] * flow[i]


            #costs[bus] = pd.DataFrame.from_dict(costs[bus], orient='index')
            #costs_df[bus] = pd.DataFrame.from_dict(costs, orient='index'
            #costs_sum[bus] = costs_df[bus].sum()

        pdb.set_trace()
        # create

        print(t['label'],inflow_args)
        print(t['label'],outflow_args)

        nodes.append(
            solph.Transformer(
                label=t['label'],
                inputs={busd[t['from']]: solph.Flow(**inflow_args)},
                outputs={busd[t['to']]: solph.Flow(**outflow_args)},
                conversion_factors={busd[t['to']]: t['efficiency']})
        )

# Create Storages objects from 'storages' tab; using GenericStorage component
for i, s in nd['storages'].iterrows():
    if s['active']:
        # set static inflow values
        inflow_args = {'variable_costs': s['input_costs'],
                       'nominal_value': s['nominal input value'],}
        outflow_args = {'variable_costs': s['output_costs'],
                        'nominal_value': s['nominal output value'],}
        # get time series for inflow of transformer
        # Parameters pre-set in outflow_args will be overwritten if a time series is available
        for col in ['batt.input_costs']:
        # for col in nd['timeseries'].columns.values:
            # print(nd['timeseries'].columns.values)
            # if col.split('.')[0] == s['label']:
            inflow_args[col.split('.')[1]] = nd['timeseries'][col][datetime_index]

        for col in ['batt.output_costs']:
            outflow_args[col.split('.')[1]] = nd['timeseries'][col][datetime_index]

        print(s['label'], inflow_args)
        print(s['label'], outflow_args)

        nodes.append(
            solph.components.GenericStorage(
                label=s['label'],
                inputs={busd[s['bus']]: solph.Flow(**inflow_args)},
                outputs={busd[s['bus']]: solph.Flow(**outflow_args)},
                nominal_capacity=s['nominal capacity'],
                capacity_loss=s['capacity loss'],
                initial_capacity=s['initial capacity'],
                capacity_max=s['capacity max'],
                capacity_min=s['capacity min'],
                inflow_conversion_factor=s['efficiency inflow'],
                outflow_conversion_factor=s['efficiency outflow'])
        )

# Create power lines between 2 buses from 'powerlines' tab
for i, p in nd['powerlines'].iterrows():
    if p['active']:
        nodes.append(
            solph.Transformer(
                label='powerline_' + p['bus_1'] + '_' + p['bus_2'],
                inputs={busd[p['bus_1']]: solph.Flow()},
                outputs={busd[p['bus_2']]: solph.Flow(nominal_value=p['capacity'])},
                conversion_factors={busd[p['bus_2']]: p['efficiency']})
        )
        nodes.append(
            solph.Transformer(
                label='powerline_' + p['bus_2'] + '_' + p['bus_1'],
                inputs={busd[p['bus_2']]: solph.Flow()},
                outputs={busd[p['bus_1']]: solph.Flow(nominal_value=p['capacity'])},
                conversion_factors={busd[p['bus_1']]: p['efficiency']})
        )

# Create a CHP plant objects from 'chp' tab; using GenericCHP component
for i, c in nd['chp'].iterrows():
    if c['active']:

        if len(datetime_index) == 0:
            msg = 'No datetime index provided (needed for CHP).'
            logger.error(msg)
            raise ValueError(msg)

        # TODO: Simple example, revise used values (copied from oemof example file)
        # TODO: Add time series to scenario if needed
        periods = len(datetime_index)
        nodes.append(
            solph.components.GenericCHP(label=c['label'],
                                        fuel_input={busd[c['from']]: solph.Flow(
                                            H_L_FG_share_max=[0.18 for p in range(0, periods)],
                                            H_L_FG_share_min=[0.41 for p in range(0, periods)])},
                                        electrical_output={busd[c['to_el']]: solph.Flow(
                                            P_max_woDH=[c['power max'] for p in range(0, periods)],
                                            P_min_woDH=[c['power min'] for p in range(0, periods)],
                                            Eta_el_max_woDH=[c['el efficiency max'] for p in range(0, periods)],
                                            Eta_el_min_woDH=[c['el efficiency min'] for p in range(0, periods)])},
                                        heat_output={busd[c['to_th']]: solph.Flow(
                                            Q_CW_min=[0 for p in range(0, periods)])},
                                        Beta=[0 for p in range(0, periods)],
                                        variable_costs=c['variable_costs'],
                                        back_pressure=c['back_pressure'])
        )
pdb.set_trace()

