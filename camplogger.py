# -*- coding: utf-8 -*-

import argparse
import obd
import time
import datetime
import memcache

mc = memcache.Client(['127.0.0.1:11211'], debug=0)

parser = argparse.ArgumentParser()
parser.add_argument('--serial', default='/dev/rfcomm0', help='Path to the serial device to use')
parser.add_argument('--debug', default=False, help='Debug flag')
parser.add_argument('--errCnt', default=5, help='Limit of read errors before connection reset')
parser.add_argument('--readDelay', default=1, help='Perid between read operations')
parser.add_argument('--connDelay', default=10, help='Perid between connection status check')
parser.add_argument('--obdLim', default=5, help='Limit of processed OBD commands')
args = parser.parse_args()

if args.debug: 
    obd.logger.setLevel(obd.logging.DEBUG)

commands = [
    obd.commands.RPM,
    obd.commands.SPEED,
    obd.commands.COOLANT_TEMP,
    obd.commands.FUEL_LEVEL,
    obd.commands.DISTANCE_SINCE_DTC_CLEAR
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
        
        while True:
	    pauseFlg = mc.get('OBD_PAUSE')
            if pauseFlg:
                break
            cnt = 0
            for i in range(0, args.obdLim):
                result =  conn.query(commands[i], force=True)
                if result is not None and result.value is not None:
                    mc.set(commands[i].name, int(result.value.m))
                else:
                    cnt += 1 
            if cnt == args.obdLim:
                break
            mc.set('OBD_TIME', str(datetime.datetime.utcnow()))
            time.sleep(args.readDelay)

        time.sleep(args.connDelay)


try: 
    monitor()
except KeyboardInterrupt:
    print 'End of program'
