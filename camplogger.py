# -*- coding: utf-8 -*-

import argparse
import obd
import time
import datetime
import memcache

mc = memcache.Client(['127.0.0.1:11211'], debug=0)

parser = argparse.ArgumentParser()
parser.add_argument('--serial', default='/dev/rfcomm0', help='Path to the serial device to use')
parser.add_argument('--debug', default=False, type=bool, help='Debug flag',)
parser.add_argument('--errCnt', default=5, type=int, help='Limit of read errors before connection reset')
parser.add_argument('--readDelay', default=1, type=int, help='Perid between read operations')
parser.add_argument('--connDelay', default=10, type=int, help='Perid between connection status check')
parser.add_argument('--obdLim', default=5, type=int, help='Limit of processed OBD commands')
args = parser.parse_args()

if args.debug: 
    obd.logger.setLevel(obd.logging.DEBUG)

commands = [
    obd.commands.RPM,
    obd.commands.SPEED,
    obd.commands.ENGINE_LOAD,
    obd.commands.INTAKE_PRESSURE,
    obd.commands.FUEL_RATE,
]

commands_slow = [
    obd.commands.COOLANT_TEMP,
    obd.commands.OIL_TEMP,
    obd.commands.INTAKE_TEMP,
    obd.commands.FUEL_LEVEL,
    obd.commands.DISTANCE_SINCE_DTC_CLEAR,
]

def monitor():
    while True:
        try:
            pauseFlg = mc.get('OBD_PAUSE')
            if not pauseFlg:
                conn = obd.OBD(args.serial, start_low_power=False)
        except KeyboardInterrupt:
            raise
        except:
            time.sleep(args.connDelay)
            continue
        
	cnt_slow = 0
	cnt_slow_len = len(commands_slow)
        while True:
            pauseFlg = mc.get('OBD_PAUSE')
            if pauseFlg:
                break
            cnt_err = 0
	    timestmp = datetime.datetime.now()
            for i in range(0, len(commands)):
                result =  conn.query(commands[i], force=True)
                if result is not None and result.value is not None:
                    mc.set(commands[i].name, int(result.value.m * (1 if commands[i].name != 'FUEL_RATE' else 100)))
                else:
                    cnt_err += 1
            result =  conn.query(commands_slow[cnt_slow], force=True)
            if result is not None and result.value is not None:
            	mc.set(commands_slow[cnt_slow].name, result.value.m)
            else:
                cnt_err += 1
	    total = (datetime.datetime.now()-timestmp).total_seconds() 
            if cnt_err >= args.errCnt:
                print 'Break !!!!!!!!!!'
                break
	    cnt_slow = (cnt_slow + 1) % cnt_slow_len	
            mc.set('OBD_TIME', str(datetime.datetime.utcnow()))
            mc.set('OBD_RESP', total)
            time.sleep(args.readDelay-total if total < args.readDelay else 0)

        time.sleep(args.connDelay)


try:
    monitor()
except KeyboardInterrupt:
    print 'End of program'
