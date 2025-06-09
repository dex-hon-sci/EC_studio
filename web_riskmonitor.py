#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Dec  7 01:15:44 2024

@author: dexter
"""
import time
import random
import threading
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv

import resource
import requests
#from prometheus_summary import Summary # Use this Summary class instead
from flask import Flask, request

import numpy as np
from prometheus_client import (CollectorRegistry, 
                               generate_latest, 
                               CONTENT_TYPE_LATEST,
                               platform_collector,
                               process_collector,
                               gc_collector,
                               Gauge, Info,
                               Histogram,
                               Counter,
                               Summary,Enum,
                               disable_created_metrics
                               )
import os
import sys
#sys.path.insert(0, '/home/dexter/Euler_Capital_codes/EC_API')
#print(sys.path)

from EC_API.monitor import Monitor
from EC_API.connect import ConnectCQG

logger = logging.getLogger(__name__)
logging.basicConfig(filename='./log/web_app.log', 
                    level=logging.INFO,
                    format="%(asctime) s%(levelname)s %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S")

host_name =  os.environ.get("CQG_API_host_name_demo")
user_name = os.environ.get("CQG_API_data_demo_usrname")
password = os.environ.get("CQG_API_data_demo_pw")

load_dotenv()
disable_created_metrics()

app = Flask(__name__)

registry = CollectorRegistry()
#symbol_list = ['QOc1', 'QOc2', 'QPc1', 'QPc2']
#code_list = ['QON25', 'QOQ25', 'QPM25', 'QPN25']

symbol_list = ['QOc1', 'QOc2']
code_list = ['QON25', 'QOQ25'] # write a code that get the latest contract

SYM2CODE = {ele1:ele2 for ele1, ele2 in zip(symbol_list, code_list)}
CODE2SYM = {ele2:ele1 for ele1, ele2 in zip(symbol_list, code_list)}

C = ConnectCQG(host_name, user_name, password)
M = Monitor(C)
CONTRACT_IDS = {f'{sym}': M._connection.resolve_symbol(sym, 1).contract_id 
                for sym in code_list}
CONTRACT_METADATA ={f'{sym}':M._connection.resolve_symbol(sym, 1)
                    for sym in code_list}     

PRICE_SCALES = {'QOc1': 1e-2, 
                'QOc2': 1e-2, 
                'QPc1': 1e-2, 
                'QPc2': 1e-2}

def strategypayload():
    # To be finished with SQL
    
    # Save display data
    strategy_data = {'lot_size': 0,
                    "TE_price": np.nan,
                    "TP_price": np.nan,
                    "SL_price": np.nan,
                    "signal": "Neutral",
                    "entry_status": False,
                    "exit_status": False,
                    "sl_status": False}
    return strategy_data

# Setup Metrics classes for Prometheus
# collect inforamtion (Loop through symbols)
# Post it on prometheus in the main loop
# 2 method : 1) go through the collect->post for each asset one-by-one.
#            2) collect metrics for each metrics then post them together

def setup_metrics_obj(symbol_name: str):
    # Setup Metrics classes for Prometheus
    PriceGauge = Gauge(f"{symbol_name}_price","USD", 
                        registry=registry)
    VolumeGauge = Gauge(f"{symbol_name}_volume","", 
                        registry=registry)
    LotSizeGauge = Gauge(f"{symbol_name}_quantity","lots",
                        registry=registry)
    TEPriceGauge = Gauge(f"{symbol_name}_target_entry","USD", 
                        registry=registry)
    TPPriceGauge = Gauge(f"{symbol_name}_target_exit","USD", 
                        registry=registry)
    SLPriceGague = Gauge(f"{symbol_name}_stop_loss","USD", 
                        registry=registry)
    EntryStatusGauge = Gauge(f"{symbol_name}_entry_status","", 
                        registry=registry)
    ExitStatusGauge = Gauge(f"{symbol_name}_exit_status","", 
                        registry=registry)
    SLStatusGauge = Gauge(f"{symbol_name}_stop_loss_status","", 
                        registry=registry)
    PNLGauge = Gauge(f"{symbol_name}_PNL","dollars", 
                        registry=registry)
    SignalEnum = Enum(f"{symbol_name}_signal","", 
                        registry=registry,
                        states=['Buy', 'Sell', 'Neutral'])
    TableInfo = Info(f"{symbol_name}_info","", registry=registry)
    
    metrics_obj_dict = {'gauge':{'price': PriceGauge, 
                                'volume': VolumeGauge,
                                'lot_size': LotSizeGauge,
                                'TE_price': TEPriceGauge,
                                'TP_price': TPPriceGauge,
                                'SL_price': SLPriceGague,
                                'entry_status': EntryStatusGauge, 
                                'exit_status': ExitStatusGauge, 
                                'sl_status': SLStatusGauge, 
                                'PNL': PNLGauge, },
                        'enum':{'signal':SignalEnum}}
    
    return metrics_obj_dict

DEFAULT_KWARGS = {'default_timestamp': np.nan,
                  'default_price': np.nan,
                  'default_volume': np.nan}

def collect_metrics(monitor: Monitor, 
                    symbol_name_list: list[str], 
                    **kwargs):
    # Collect metrics based on a list of symbol
    # It loop through this list to get the live market data
    default_kwargs = DEFAULT_KWARGS
    kwargs = dict(default_kwargs,**kwargs)

    master_metrics_val_dict = {}
    for symbol_name in symbol_name_list:
        # collect inforamtion 
        contract_id = CONTRACT_IDS[SYM2CODE[symbol_name]]
        print(f"======={symbol_name}, {contract_id}=======")
        # Get the live-data
        timestamp, price, volume = M.request_real_time(contract_id,
                                                       default_timestamp=
                                                       kwargs['default_timestamp'],
                                                       default_price=
                                                       kwargs['default_price'],
                                                       default_volume=
                                                       kwargs['default_volume'])
        # Reset the tracker for this symbol
        M.reset_tracker(contract_id) 
        # Test
        #timestamp, price, volume = random.randint(0,100000), random.randint(0,100000), random.randint(0,10)

        #timestamp, price, volume = M.track_real_time_inst(contract_id, msg_id)
        print(SYM2CODE[symbol_name], contract_id, timestamp, price, volume)

        #logger.info(str(server_msg))
        #print('msg_id',msg_id)
        if type(volume) == float|int:
            volume_float = [volume]
        elif type(volume) != float|int:
            volume_float = [int(char) for char in str(volume) if char.isdigit()]
            if len(volume_float) == 0:
                volume_float = [0]
    
        ############################################    
        # Get information from Strategy
        # Payload information Read this from a class 
        strategy_data = strategypayload()
        
        lot_size = strategy_data['lot_size']
        TE_price = strategy_data['TE_price']
        TP_price = strategy_data['TP_price']
        SL_price = strategy_data['SL_price']
        signal = strategy_data['signal']
    
        # scrapper for the status of our position (get from payload DB Shellpile)
        entry_status = strategy_data['entry_status']
        exit_status = strategy_data['exit_status']
        sl_status = strategy_data['sl_status']
        
        # Derived quantity
        PNL = (price-TE_price)*lot_size
    
        # Load them for output
        metric_val_dict = {'price': price*PRICE_SCALES[symbol_name], 
                           'lot_size': lot_size,
                            'timestamp': timestamp,
                            'volume': volume_float[0], 
                            'TE_price': TE_price,
                            'TP_price': TP_price,
                            'SL_price': SL_price,
                            'entry_status': entry_status, 
                            'exit_status': exit_status, 
                            'sl_status': sl_status, 
                            'PNL': PNL, 
                            'signal': signal}
        
        master_metrics_val_dict[SYM2CODE[symbol_name]] = metric_val_dict

    #print('final msg_id', msg_id)
    return master_metrics_val_dict


def set_metrics_values(symbol_name_list: str, 
                       metrics_obj_dict: dict,
                       metric_val_dict: dict):
    # This function matches the metric_obj with the metric value
    # This method assume the key of metric_val_dict matches the ones in
    # metrics_obj_dict
    
    for symbol_name in symbol_name_list:
        # First load the guage objects
        for key in metrics_obj_dict[symbol_name]['gauge']: 
            #print(key, metric_val_dict[key], type(metric_val_dict[key]))
            metrics_obj_dict[symbol_name]['gauge'][key].set(
                metric_val_dict[SYM2CODE[symbol_name]][key])
            
        # second load the enum objects
        for key in metrics_obj_dict[symbol_name]['enum']: 
            metrics_obj_dict[symbol_name]['enum'][key].state(
                metric_val_dict[SYM2CODE[symbol_name]][key])
    return

def main_loop(port, sym_list:list[str], update_rate: float |int=1):
    # update_rate is the waiting time each loop in seconds 
    # Setup and initilisation
    
    # Setup master metric objects
    master_metrics_obj_dict = {f'{sym}': setup_metrics_obj(sym) 
                               for sym in sym_list}
    
    master_metrics_val_dict = {f'{sym}': {'timestamp': np.nan,
                                          'price': np.nan,
                                          'volume': np.nan} 
                               for sym in sym_list}

    # Main Loop of the app
    t_end = time.time() + 5
    while True:
        # Reboot the loop when UTC time hit 00:00 (should be in a cron script)
        
        UTC_now_dt = datetime.now(timezone.utc)
        # POSIX timestamp in milliseconds
        UTC_now_timestamp = datetime.now(timezone.utc).timestamp() * 1000 
        
        # Start the loop if it is 03:30 UTC
        # Delete the TSDB data when the time is between 00:00 -> 03:00 UTC
        # (This can only be done when the port is active)
        # if UTC_now_dt.time() < xxx :
        # os.system(f"curl -X POST -g 'http://localhost:{port}/api/v1/admin/tsdb/delete_series?match[]={instance="sbcode.net:9010"}'")
        
        # Only collect data and post them on TSDB between 03:00 -> 11:59 UTC
        if time.time() > t_end:
            #print("initial_input", master_metrics_val_dict[sym])
            master_metrics_val_dict = collect_metrics(M, sym_list)
                                              
            #print(master_metrics_val_dict)
            # Post the metrics on Prometheus
            #set_metrics_values(sym_list, 
            #                   master_metrics_obj_dict, # with sym_list as keys
            #                   master_metrics_val_dict)
        #time.sleep(update_rate)
    return

@app.route('/metrics')
def metrics():
    """ Exposes application metrics in a Prometheus-compatible format. """

    return generate_latest(registry), 200, {'Content-Type': CONTENT_TYPE_LATEST}

@app.route('/')
def hello():
    #delay = random.uniform(1, 5)  # Random delay between 1 and 5 seconds
    #time.sleep(delay)

    return 'Hello world!'


if __name__ == '__main__':
    
    # Target: Input a list of symbols, Output plot in Grafana
    # Process Get the live-data from WebAPI, get the Strategy Payload from internal
    # server, post it through prometheus, plot them in Grafana
    port = os.environ.get("PORT") #int(os.getenv('PORT', '8000'))
    print(f'Starting HTTP server on port {port}')
    
    metrics_thread = threading.Thread(target=main_loop, 
                                      args = (port, symbol_list,), 
                                      daemon=True)
    metrics_thread.start()

    try:
        app.run(host='0.0.0.0', port=port, debug=True)
        
    except Exception as e:
        print(f'Server failed to start: {e}')
        exit(1)