#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 24 10:31:30 2025

@author: dexter
"""
import threading
import os
import sys
import time
import logging

from datetime import datetime, timezone


from dotenv import load_dotenv
import numpy as np
sys.path.insert(0, '/home/dexter/Euler_Capital_codes/EC_studio/EC_API')

from flask import Flask, request
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


print(sys.path)

from EC_API.monitor import Monitor
from EC_API.connect import ConnectCQG

print(Monitor.__dict__)

load_dotenv()
host_name_realtime = os.environ.get("CQG_API_host_name_demo")
user_name_realtime = os.environ.get("CQG_API_data_demo_usrname")
password_realtime = os.environ.get("CQG_API_data_demo_pw")

disable_created_metrics()
app = Flask(__name__)
registry = CollectorRegistry()


resolveSymbolName1 = 'CLEN25'
resolveSymbolName2 = 'F.US.ZUC'
resolveSymbolName3 = 'QOQ25'
resolveSymbolName4 = 'ZUCN25'

logger = logging.getLogger(__name__)
logging.basicConfig(filename='./log/test_script.log', 
                    level=logging.INFO,
                    format="%(asctime) s%(levelname)s %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S")
symbol_list = ['QOc1', 'QOc2', 'QPc1', 'QPc2']

code_list = ['QOQ25', 'QOU25', 'QPM25','QPN25']
#symbol_list = ['QOQ25', 'QOU25']
SYM2CODE = {ele1:ele2 for ele1, ele2 in zip(symbol_list, code_list)}
CODE2SYM = {ele2:ele1 for ele1, ele2 in zip(symbol_list, code_list)}

#symbol_list = ['QOQ25', 'QPM25']
#symbol_list = ['QPM25']
C = ConnectCQG(host_name_realtime, user_name_realtime, password_realtime)
M = Monitor(C)
PRICE_SCALES = {'QOQ25': 1e-2, 
                'QOU25': 1e-2, 
                'QPM25': 1e-2, 
                'QPN25': 1e-2}

def func(resolveSymbolName, num="", sleep_time =1):
    C = ConnectCQG(host_name_realtime, user_name_realtime, password_realtime)

    M = Monitor(C)
    msg_id = 200
    contract_id = M._connection.resolve_symbol(resolveSymbolName, msg_id).contract_id
    msg_id+=1
    while True:
        msg_id+=1
        print(f"===={num}=========")
        _, price, volume = M.track_real_time_inst(contract_id,msg_id)
        #logger.info(f'{price}')
        print(f'{resolveSymbolName} price: {price}, {volume}')
        time.sleep(sleep_time)

    return

def func2(resolveSymbolName, num="", sleep_time =1):
    C = ConnectCQG(host_name_realtime, user_name_realtime, password_realtime)

    M = Monitor(C)
    msg_id = 200
    contract_id = M._connection.resolve_symbol(resolveSymbolName, msg_id).contract_id
    #msg_id+=1
    while True:
        msg_id+=1
        output = M.track_real_time_inst(contract_id, msg_id, 3)
        print('output', output)
# =============================================================================
#     while True:
#         msg_id+=1
#         print(f"===={num}=========")
#         _, price, volume = M.track_real_time_inst(contract_id,msg_id)
#         #logger.info(f'{price}')
#         print(f'{resolveSymbolName} price: {price}, {volume}')
#         time.sleep(sleep_time)
# 
# =============================================================================
    return


CONTRACT_IDS = {f'{sym}': M._connection.resolve_symbol(sym, 1).contract_id 
                for sym in code_list}
CONTRACT_METADATA ={f'{sym}':M._connection.resolve_symbol(sym, 1)
                    for sym in code_list}     
#contract_metadata1 = server_msg1.information_reports[0].symbol_resolution_report.contract_metadata
print('CONTRACT_IDS', CONTRACT_IDS)
#print("CONTRACT_METADATA", CONTRACT_METADATA)
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


def strategypayload():
    # To be finished with SQL
    
    # Save display data
    strategy_data = {'lot_size': 1,
                    "TE_price": 50010,
                    "TP_price": 70300,
                    "SL_price": 19020,
                    "signal": "Buy",
                    "entry_status": True,
                    "exit_status": False,
                    "sl_status": True}
    return strategy_data

DEFAULT_KWARGS = {'default_val_dict': {f'{sym}': {'timestamp': np.nan,
                                      'price': np.nan,
                                      'volume': np.nan} 
                                       for sym in code_list}}

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
        contract_id = CONTRACT_IDS[symbol_name]
        #print(f"======={symbol_name}, {contract_id}=======")
        d_timestamp = kwargs['default_val_dict'][symbol_name]['timestamp']
        d_price = kwargs['default_val_dict'][symbol_name]['price']
        d_volume = kwargs['default_val_dict'][symbol_name]['volume']
        # Get the live-data
        timestamp, price, volume = M.request_real_time(contract_id,
                                                       default_timestamp=d_timestamp,
                                                       default_price=d_price,
                                                       default_volume=d_volume)

        M.reset_tracker(contract_id) # Reset the tracker
        
        # save it for the next
        #timestamp, price, volume = M.track_real_time_inst(contract_id, msg_id)
        #print(symbol_name, contract_id, timestamp, price, volume)

        #logger.info(str(server_msg))
        #print('msg_id',msg_id)
        if type(volume) == float|int:
            volume_float = [volume]
        elif type(volume) != float|int:
            volume_float = [int(char) for char in str(volume) if char.isdigit()]
            if len(volume_float) == 0:
                volume_float = [0]
    
            #print("volume", volume,volume_float, type(volume))
    
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
                            'timestamp': timestamp,
                            'volume': volume_float[0], 
                            'lot_size': lot_size,
                            'TE_price': TE_price,
                            'TP_price': TP_price,
                            'SL_price': SL_price,
                            'entry_status': entry_status, 
                            'exit_status': exit_status, 
                            'sl_status': sl_status, 
                            'PNL': PNL, 
                            'signal': signal}
        
        master_metrics_val_dict[symbol_name] = metric_val_dict

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
        for key in metrics_obj_dict[CODE2SYM[symbol_name]]['gauge']: 
            #print(key, metric_val_dict[key], type(metric_val_dict[key]))
            metrics_obj_dict[CODE2SYM[symbol_name]]['gauge'][key].set(
                metric_val_dict[symbol_name][key])
            
        # second load the enum objects
        for key in metrics_obj_dict[CODE2SYM[symbol_name]]['enum']: 
            metrics_obj_dict[CODE2SYM[symbol_name]]['enum'][key].state(
                metric_val_dict[symbol_name][key])
    return


def main_loop(port, sym_list:list[str], update_rate: float |int=1):
    # update_rate is the waiting time each loop in seconds 
    # Setup and initilisation
    
    # Setup master metric objects
    #master_metrics_obj_dict = {'sym': setup_metrics_obj(sym) for sym in sym_list}\
    master_metrics_obj_dict = {f'{CODE2SYM[sym]}': setup_metrics_obj(CODE2SYM[sym])
                               for sym in sym_list}
    
    # Initial buffer values 
    master_metrics_val_buffer_dict = {f'{sym}': {'timestamp': np.nan,
                                                 'price': np.nan,
                                                 'volume': np.nan} 
                                                  for sym in sym_list}

    #print(master_metrics_obj_dict, master_metrics_val_dict)
    msg_id = 200
# =============================================================================
#     master_metrics_val_dict = collect_metrics(M, sym_list, msg_id)
#     print("master_metrics_val_dict", master_metrics_val_dict)
#     # Main Loop of the app
# =============================================================================
   # os.system(f"curl -i -XPOST localhost:9010/-/reload")

    t_end = time.time() + 5
    while True:
        # ...
                
        UTC_now_dt = datetime.now(timezone.utc)
        # POSIX timestamp in milliseconds
        UTC_now_timestamp = datetime.now(timezone.utc).timestamp() * 1000 
        
        # Start the loop if it is 03:30 UTC
        # Delete the TSDB data when the time is between 00:00 -> 03:00 UTC
        # (This can only be done when the port is active)
        # if UTC_now_dt.time() < xxx :
        # os.system(f"curl -X POST -g 'http://localhost:{port}/api/v1/admin/tsdb/delete_series?match[]={instance="sbcode.net:9010"}'")

        if time.time() > t_end:
            #print('time',time.time(), t_end)
            msg_id +=1
            print(M.msg_id)
            #print("initial_input", master_metrics_val_dict[sym])
            master_metrics_val_dict = collect_metrics(M, sym_list,
                                                      default_val_dict=
                                                      master_metrics_val_buffer_dict)
            master_metrics_val_buffer_dict = master_metrics_val_dict
            print(master_metrics_val_dict)
            set_metrics_values(sym_list, 
                               master_metrics_obj_dict, # with sym_list as keys
                               master_metrics_val_dict)

            # Record the metrics value in a master dict as the default value 
            # of the next loop
            #break
        #time.sleep(update_rate)
        #i +=1
    return

def run_multithread():
    #print(host_name_realtime, user_name_realtime, password_realtime)

    metrics_thread1 = threading.Thread(target=func, #daemon=True, 
                                       args = (resolveSymbolName1,),
                                       kwargs={'num':'Thread_1',
                                               'sleep_time':3})
    
    metrics_thread2 = threading.Thread(target=func, daemon=True, 
                                       args = (resolveSymbolName2,),
                                       kwargs={'num':'Thread_2',
                                               'sleep_time':1})
    
    metrics_thread3 = threading.Thread(target = func2, 
                                       args =  (resolveSymbolName3,),
                                       kwargs={'num':'Thread_3',
                                               'sleep_time':1})
    metrics_thread1.start()
    metrics_thread2.start()
    metrics_thread3.start()

def run_singlethread_multiassets():
# =============================================================================
#     metrics_thread1 = threading.Thread(target=func2,
#                                       args = (resolveSymbolName3,),
#                                       kwargs={'num':'Thread_1',
#                                               'sleep_time':3})
# =============================================================================
    main_loop(symbol_list)
    #metrics_thread1 = threading.Thread(target= main_loop,
    #                                   args = (symbol_list,))

    #metrics_thread1.start()

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
    port = os.environ.get("PORT") #int(os.getenv('PORT', '8000'))
    print(f'Starting HTTP server on port {port}')
    
    metrics_thread = threading.Thread(target=main_loop, 
                                      args = (port, code_list,), 
                                      daemon=True)
    metrics_thread.start()

    try:
        app.run(host='0.0.0.0', port=port, debug=True)

    #try:
    #    #func(resolveSymbolName1)
    #    run_singlethread_multiassets()
    except Exception as e:
        print(f'Server failed to start: {e}')
        exit(1)
