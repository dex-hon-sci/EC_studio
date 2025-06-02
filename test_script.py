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

from dotenv import load_dotenv

sys.path.insert(0, '/home/dexter/Euler_Capital_codes/EC_studio/EC_API')

print(sys.path)

from EC_API.monitor import Monitor
from EC_API.connect import ConnectCQG

print(Monitor.__dict__)

load_dotenv()
host_name_realtime = os.environ.get("CQG_API_host_name_demo")
user_name_realtime = os.environ.get("CQG_API_data_demo_usrname")
password_realtime = os.environ.get("CQG_API_data_demo_pw")

resolveSymbolName1 = 'CLEN25'
resolveSymbolName2 = 'F.US.ZUC'
resolveSymbolName3 = 'QOQ25'
resolveSymbolName4 = 'ZUCN25'

logger = logging.getLogger(__name__)
logging.basicConfig(filename='./log/test_script.log', 
                    level=logging.INFO,
                    format="%(asctime) s%(levelname)s %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S")

symbol_list = ['QOQ25', 'QOU25', 'QPM25','QPN25']
#symbol_list = ['QOQ25']
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


CONTRACT_IDS = {f'{sym}':M._connection.resolve_symbol(sym, 1).contract_id 
                for sym in symbol_list}

def strategypayload():
    # To be finished with SQL
    
    # Save display data
    strategy_data = {'lot': 1,
                    "TE_price": 50010,
                    "TP_price": 70300,
                    "SL_price": 19020,
                    "signal": "Buy",
                    "entry_status": True,
                    "exit_status": False,
                    "sl_status": True}
    return strategy_data

DEFAULT_KWARGS = {'initial_dt':404,
                  'initial_price':404,
                  'initial_volume':404}

def collect_metrics(monitor: Monitor, 
                    symbol_name_list: list[str], 
                    msg_id: int, **kwargs):
    # Collect metrics based on a list of symbol
    # It loop through this list to get the live market data
    default_kwargs = DEFAULT_KWARGS
    kwargs = dict(default_kwargs,**kwargs)

    master_metrics_val_dict = {}
    for symbol_name in symbol_name_list:
        # collect inforamtion 
        #contract_id = monitor._connection.resolve_symbol(symbol_name, 1).contract_id
        contract_id = CONTRACT_IDS[symbol_name]
        print(symbol_name, contract_id)
        # Get the live-data
        timestamp, price, volume = M.request_real_time(contract_id, msg_id)
                                                          #kwargs['initial_dt'],
                                                          #kwargs['initial_price'],
                                                          #kwargs['initial_volume'])
        msg_id += 1
        print('msg_id',msg_id)
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
        
        lot = strategy_data['lot']
        TE_price = strategy_data['TE_price']
        TP_price = strategy_data['TP_price']
        SL_price = strategy_data['SL_price']
        signal = strategy_data['signal']
    
        # scrapper for the status of our position (get from payload DB Shellpile)
        entry_status = strategy_data['entry_status']
        exit_status = strategy_data['exit_status']
        sl_status = strategy_data['sl_status']
        
        # Derived quantity
        PNL = (price-TE_price)*lot
    
        # Load them for output
        metric_val_dict = {'price': price*PRICE_SCALES[symbol_name], 
                            'timestamp': timestamp,
                            'volume': volume_float[0], 
                            'TE_price': TE_price,
                            'TP_price': TP_price,
                            'SL_price': SL_price,
                            'entry_status': entry_status, 
                            'exit_status': exit_status, 
                            'sl_status': sl_status, 
                            'PNL_gauge': PNL, 
                            'signal_enum': signal}
        
        master_metrics_val_dict[symbol_name] = metric_val_dict

    print('final msg_id', msg_id)
    return msg_id, master_metrics_val_dict

def main_loop(sym_list:list[str], update_rate: float |int=1):
    # update_rate is the waiting time each loop in seconds 
    # Setup and initilisation
    
    # Setup master metric objects
    #master_metrics_obj_dict = {'sym': setup_metrics_obj(sym) for sym in sym_list}
    
    msg_id = 200
    master_metrics_val_dict = {f'{sym}': {'timestamp': 404,
                                          'price': 404,
                                          'volume':404} for sym in sym_list}
# =============================================================================
#     master_metrics_val_dict = collect_metrics(M, sym_list, msg_id)
#     print("master_metrics_val_dict", master_metrics_val_dict)
#     # Main Loop of the app
# =============================================================================
    t_end = time.time() + 5
    while True:
        # ...
        if time.time() > t_end:
            print('time',time.time(), t_end)
            msg_id +=1
            print(msg_id)
            #print("initial_input", master_metrics_val_dict[sym])
            msg_id, master_metrics_val_dict = collect_metrics(M, sym_list, msg_id)
                                              #initial_dt= master_metrics_val_dict[sym]['timestamp'],
                                              #initial_price = master_metrics_val_dict[sym]['price'],
                                              #initial_volume= master_metrics_val_dict[sym]['volume'])
            print(master_metrics_val_dict)
            #set_metrics_values(sym, master_metrics_obj_dict[sym], metric_val_dict)
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
    metrics_thread1 = threading.Thread(target= main_loop,
                                       args = (symbol_list,))

    metrics_thread1.start()

    return 

if __name__ == '__main__':
    
    try:
        #func(resolveSymbolName1)
        run_singlethread_multiassets()
    except Exception as e:
        print(f'Server failed to start: {e}')
        exit(1)
