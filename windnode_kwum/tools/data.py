import logging
logger = logging.getLogger('windnode_kwum')
from windnode_kwum.tools import config

import os
import requests
import pandas as pd


def oep_get_data(schema, table, columns=[], conditions=[], order=''):
    """Retrieve data from Open Energy Platform (OEP) / Database

    Parameters
    ----------
    schema : :obj:`str`
        Database schema
    table : :obj:`str`
        Database table
    columns : :obj:`list` of :obj:`str`
        Table columns
    conditions : :obj:`list` of :obj:`str`
        Conditions to be applied on query
    order : :obj:`str`
        Column which data is sorted by (ascending)

    Returns
    -------
    :pandas:`pandas.DataFrame<dataframe>`
        Requested data
    """

    oep_url = config.get('data', 'oep_url')

    if not schema or not table:
        raise ValueError('Schema or table not specified.')

    columns = '&'.join('column='+col for col in columns)

    if conditions:
        conditions = '&' + '&'.join('where='+cond for cond in conditions)
    else:
        conditions = ''

    if order:
        order = '&order_by=' + order
    else:
        order = ''

    url = oep_url +\
          '/api/v0/schema/' +\
          schema +\
          '/tables/' +\
          table +\
          '/rows/?' + \
          columns +\
          conditions +\
          order

    result = requests.get(url)
    status = str(result.status_code)

    logger.info('Response from OEP: ' + status + ', elapsed time: ' + str(result.elapsed))
    if status != '200':
        logger.exception('Something went wrong during data retrieval from OEP: ')

    return pd.DataFrame(result.json())


def oemof_nodes_from_excel(scenario_file,
                           #data_file,
                           header_lines=0):
    """Import scenario data from Excel file

    Parameters
    ----------
    scenario_file : :obj:`str`
        Path to scenario Excel file
    data_file : :obj:`str`
        Path to data Excel file
    header_lines : :obj:`int`
        Header lines in Excel file to be skipped

    Returns
    -------
    :obj:`dict`
        Imported nodes data
    """
    # excel file does not exist
    if not scenario_file or not os.path.isfile(scenario_file):
        logger.exception('Scenario Excel file {} not found.'
                         .format(scenario_file))
#    if not data_file or not os.path.isfile(data_file):
#        logger.exception('Data Excel file {} not found.'
#                         .format(data_file))

    xls_s = pd.ExcelFile(scenario_file)
#    xls_d = pd.ExcelFile(data_file)

    # read scenario data
    nodes_data = {'buses': xls_s.parse('buses', header=header_lines),
                  'chp': xls_s.parse('chp', header=header_lines),
                  'chp_trans': xls_s.parse('chp_trans', header=header_lines),
                  'commodity_sources': xls_s.parse('commodity_sources', header=header_lines),
                  'transformers': xls_s.parse('transformers', header=header_lines),
                  'renewables': xls_s.parse('renewables', header=header_lines),
                  'demand': xls_s.parse('demand', header=header_lines),
                  'storages': xls_s.parse('storages', header=header_lines),
                  'powerlines': xls_s.parse('powerlines', header=header_lines),
                  'timeseries': xls_s.parse('time_series', header=header_lines)
                  }

    # set datetime index
    nodes_data['timeseries'].set_index('timestamp', inplace=True)
    nodes_data['timeseries'].index = pd.to_datetime(nodes_data['timeseries'].index)

    # read further (non-public) data from data file
#    timeseries_d = xls_d.parse('time_series', header=header_lines)
#    timeseries_d.set_index('timestamp', inplace=True)
#    timeseries_d.index = pd.to_datetime(timeseries_d.index)

    # join datasets
    # ONLY JOIN OF TIMESERIES IS IMPLEMENTED RIGHT NOW
#    if not nodes_data['timeseries'].index.equals(timeseries_d.index):
#        msg = 'Timesteps of timeseries from scenario file and data file do not match!'
#        logger.error(msg)
#        raise ValueError(msg)
#    else:
#        nodes_data['timeseries'] = pd.merge(nodes_data['timeseries'],
#                                            timeseries_d,
#                                            how='left',
#                                            right_index=True,
#                                            left_index=True)

    logger.info('Data from Excel file {} imported.'
                .format(scenario_file))
#    logger.info('Data from Excel file {} imported.'
#                .format(data_file))
    return nodes_data
