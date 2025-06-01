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
sys.path.insert(0, '/home/dexter/Euler_Capital_codes/EC_API')
print(sys.path)

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
symbol_list = ['QON25', 'QOQ25', 'QPM25', 'QPN25']
C = ConnectCQG(host_name, user_name, password)
M = Monitor(C)
CONTRACT_IDS = {f'{sym}': M._connection.resolve_symbol(sym, 1).contract_id 
                for sym in symbol_list}
PRICE_SCALES = {'QON25': 1e-2, 
                'QOQ25': 1e-2, 
                'QPM25': 1e-2, 
                'QPN25': 1e-2}

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
    
# =============================================================================
#     metrics_obj_dict =  {'price': PriceGauage, 
#                          'volume': VolumeGauge,
#                          'lot_size': LotSizeGauge,
#                          'TE_price': TEPriceGauge,
#                          'TP_price': TPPriceGauge,
#                          'SL_price': SLPriceGague,
#                          'entry_status': EntryStatusGauge, 
#                          'exit_status': ExitStatusGauge, 
#                          'sl_status': SLStatusGauge, 
#                          'PNL': PNLGauge, }
# =============================================================================
                         #'signal': SignalEnum,}
                         #'table_info': TableInfo}
    
    return metrics_obj_dict


def collect_metrics(monitor: Monitor, 
                    symbol_name: str, msg_id: int):
    # collect inforamtion 
    #contract_id = monitor._connection.resolve_symbol(symbol_name, 1).contract_id
    contract_id = CONTRACT_IDS[symbol_name]
    # Get the live-data
    timestamp, price, volume = M.track_real_time_inst(contract_id, msg_id)
    
    # Get information from Strategy
    # Payload information Read this from a class 
    lot_size = 1
    TE_price = 50010
    TP_price = 70300
    SL_price = 19020
    
    # scrapper for the status of our position 
    entry_status = True
    exit_status = False
    sl_status = True
    
    signal = "Buy"
    PNL = (price-TE_price)*lot_size

    # Load them for output
    metric_val_dict = {'price': price*PRICE_SCALES[symbol_name], 
                        'timestamp': timestamp,
                        'volume': float(volume),
                        'lot_size': lot_size,
                        'TE_price': TE_price,
                        'TP_price': TP_price,
                        'SL_price': SL_price,
                        'entry_status': entry_status, 
                        'exit_status': exit_status, 
                        'sl_status': sl_status, 
                        'PNL': PNL, 
                        'signal': signal}
    
    return metric_val_dict

def set_metrics_values(symbol_name: str, 
                       metrics_obj_dict: dict,
                       metric_val_dict: dict):
    # This function matches the metric_obj with the metric value
    # This method assume the key of metric_val_dict matches the ones in
    # metrics_obj_dict
    
    # First load the guage objects
    for key in metrics_obj_dict['gauge']: 
        #print(key, metric_val_dict[key], type(metric_val_dict[key]))
        metrics_obj_dict['gauge'][key].set(metric_val_dict[key])
        
    # second load the enum objects
    for key in metrics_obj_dict['enum']: 
        metrics_obj_dict['enum'][key].state(metric_val_dict[key])

    return

def main_loop(sym_list:list[str], update_rate: float |int=1):
    # update_rate is the waiting time each loop in seconds 
    # Setup and initilisation
    
    # Setup master metric objects
    master_metrics_obj_dict = {f'{sym}': setup_metrics_obj(sym) for sym in sym_list}
    
    msg_id = 200
    
    # Main Loop of the app
    while True:
        msg_id +=1
        for sym in sym_list:
           metric_val_dict = collect_metrics(M, sym, msg_id)
           #set_metrics_values(sym, master_metrics_obj_dict[sym], metric_val_dict)
           
        time.sleep(update_rate)
    return



@app.route('/metrics')
def metrics():
    """ Exposes application metrics in a Prometheus-compatible format. """

    return generate_latest(registry), 200, {'Content-Type': CONTENT_TYPE_LATEST}

@app.route('/')
def hello():
    delay = random.uniform(1, 5)  # Random delay between 1 and 5 seconds
    time.sleep(delay)

    return 'Hello world!'


if __name__ == '__main__':
    port = os.environ.get("PORT") #int(os.getenv('PORT', '8000'))
    print(f'Starting HTTP server on port {port}')
    
    metrics_thread = threading.Thread(target=main_loop, args = (symbol_list,), 
                                      daemon=True)
    metrics_thread.start()

    try:
        app.run(host='0.0.0.0', port=port, debug=True)
        
    except Exception as e:
        print(f'Server failed to start: {e}')
        exit(1)
