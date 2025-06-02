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
#sys.path.append("/home/dexter/Euler_Capital_codes/EC_API") # Adds higher directory to python modules path.
#sys.path.append("/home/dexter/Euler_Capital_codes/EC_tools") # Adds higher directory to python modules path.

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


def normalize(arr, t_min, t_max):
    norm_arr = []
    diff = t_max - t_min
    diff_arr = max(arr) - min(arr)    
    for i in arr:
        temp = (((i - min(arr))*diff)/diff_arr) + t_min
        norm_arr.append(temp)
    return norm_arr

load_dotenv()
disable_created_metrics()

app = Flask(__name__)

registry = CollectorRegistry()

x = np.arange(0, 100000, 1000)
mu, sigma = 50000, 8000
y= (1/np.sqrt(2*np.pi*sigma**2))*np.exp((-1*(x-mu)**2)/(2*sigma**2))
z = (1/sum(normalize(y,0,1)))*np.array(normalize(y,0,1))

x_str = [str(ele) for ele in x]
z_str = [str(ele) for ele in z]

pdf_dict = {str(ele_x): float(ele_z) for ele_x, ele_z in zip(x,z)}

import json
pdf_js = json.dumps(pdf_dict)

def make_gauss_sample():
    y_sample = 0 
    return y_sample



def collect_metrics():

    symbol_name = 'QOM25'
    Q = f"{symbol_name}_asset_price"
    asset_price = Gauge(f"{symbol_name}_asset_price","dollars", 
                        registry=registry)
    lot_size = Gauge(f"{symbol_name}_Quantity","lots",
                        registry=registry)
    target_entry_price = Gauge(f"{symbol_name}_target_entry","dollars", 
                        registry=registry)
    target_exit_price = Gauge(f"{symbol_name}_target_exit","dollars", 
                        registry=registry)
    stop_loss_price = Gauge(f"{symbol_name}_stop_loss","dollars", 
                        registry=registry)
    entry_status = Gauge(f"{symbol_name}_entry_status","", 
                        registry=registry)
    exit_status = Gauge(f"{symbol_name}_exit_status","", 
                        registry=registry)
    sl_status = Gauge(f"{symbol_name}_stop_loss_status","", 
                        registry=registry)
    PNL_gauge = Gauge(f"{symbol_name}_PNL","dollars", 
                        registry=registry)
    signal_enum = Enum(f"{symbol_name}_signal","", 
                        registry=registry,
                        states=['Buy', 'Sell', 'Neutral'])
    
    table_info = Info(f"{symbol_name}_info","", registry=registry)
    #distro_histogram = Histogram("distro_hist", "", 
    #                             buckets=x,
    #                             registry=registry)
    
    #distro_histogram_2 = Histogram("distro_hist_2", "", 
    #                             registry=registry)
    #distro_info = Histogram("distro_hist", "", 
    #                             buckets=x,
    #                             registry=registry)


    resolveSymbolName = 'QOM25'
    
    lot = 1
    t_entry = 50010
    t_exit = 70300
    t_sl = 19020
    
    t_entry_status = True
    t_exit_status = False
    t_sl_status = True
    
    signal = "Buy"
    #y = (1/np.sqrt(2*np.pi*sigma**2))*np.exp((-1*(x-mu)**2)/(2*sigma**2))
    
    C = ConnectCQG(host_name, user_name, password)
    M = Monitor(C)
    contract_id = M._connection.resolve_symbol(resolveSymbolName, 1).contract_id
    table = {'A':'1', 'B':'2','C':'3'}
    i = 0
    msg_id = 1000
    
    
    initial_dt0, initial_price0 = M.track_real_time_inst(contract_id,msg_id)
    print('initial_dt0, initial_price0', initial_dt0, initial_price0)
    while True:
        msg_id +=1
        _, price,volume = M.track_real_time_inst(contract_id,msg_id, 
                                          initial_dt = initial_dt0, 
                                          initial_price= initial_price0)
        #price = random.randint(0,100000)
        qty = 1
        PNL =  (price-t_entry)*qty
        print(price)
        logger.info(f'{price}')

        asset_price.set(price)
        lot_size.set(lot)
        target_entry_price.set(t_entry)
        target_exit_price.set(t_exit)
        stop_loss_price.set(t_sl)
        entry_status.set(t_entry_status)
        exit_status.set(t_exit_status)
        sl_status.set(t_sl_status)
        PNL_gauge.set(PNL)
        signal_enum.state(signal)
        
        table_info.info(table)
        #y_sample = np.random.choice(x,p=z)
        #distro_histogram.observe(y_sample)
        
        #distro_histogram_2.observe(y_sample)
        time.sleep(1)
        i +=1

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


# =============================================================================
# @app.route('/pdf')
# def pdf():
#     
#     return pdf_js, 200
# =============================================================================

def run_main():
    return

if __name__ == '__main__':
    port = os.environ.get("PORT") #int(os.getenv('PORT', '8000'))
    print(f'Starting HTTP server on port {port}')
    
    metrics_thread = threading.Thread(target=collect_metrics, daemon=True)
    metrics_thread.start()

    try:
        app.run(host='0.0.0.0', port=port, debug=True)
        
    except Exception as e:
        print(f'Server failed to start: {e}')
        exit(1)
