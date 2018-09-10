#!/usr/bin/env python3
import signal
import sys
import time
import argparse
from ipaddress import ip_address
from power_ctrl import sp8h
from power_ctrl import aw2401

class power_ctrl_cliparser(argparse.ArgumentParser):
    """
    override the default behavior of the error method
    """

    def error(self, message):
        sys.stderr.write('error: %s\n' %message)
        self.print_help()
        sys.exit(2)

def main():
    """
    A CLI parser to control power switch.
    """

    o_sp8h = sp8h()

    def signal_handler(sig, frame):
        sys.stdout.write('You pressed Ctrl+C!')
        o_sp8h.logout()
        sys.stdout.write('\nLogout sp8h.')
        o_sp8h.disconnect()
        sys.stdout.write('\nDisconnect sp8h.\n')
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    parser = power_ctrl_cliparser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    subparsers = parser.add_subparsers(title='Support devices', dest='device', help="device")

    #sp8h command
    sp8h_parser = subparsers.add_parser('sp8h', help="Target is a SP8H device.", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    sp8h_parser.add_argument('--device-ip'      , '-i', type=ip_address , help="Device ip address", required=True)
    sp8h_parser.add_argument('--user'           , '-U', type=str        , help="Username for login SP8H", default='admin')
    sp8h_parser.add_argument('--passwd'         , '-P', type=str        , help="Password for login SP8H", default='admin')
    sp8h_parser.add_argument('--machine-id'     , '-m', type=int        , help="Select machine id", nargs='+', choices=range(1,5), required=True)
    sp8h_parser.add_argument('--power-id'       , '-p', type=int        , help="Select power id", nargs='+', choices=range(1,9))
    sp8h_parser.add_argument('--power-status'   , '-s', type=str        , help="Set power status", choices=['on', 'off', 'reset'])
    sp8h_parser.add_argument('--get-status'     , '-g', help="Get power status", action="store_true")
    sp8h_parser.add_argument('--interval'       , '-I', type=int        , help="Interval time(ms) for each operation", default=700)
    sp8h_parser.add_argument('--retry'          , '-r', type=int        , help="Number of retry", default=0)
    sp8h_parser.add_argument('--retry-interval' , '-t', type=int        , help="Retry interval time(s)", default=5)
    sp8h_parser.add_argument('--verbose'        , '-v', help="Increase output verbosity", action="store_true")

    #aw2401 command
    aw2401_parser = subparsers.add_parser('aw2401', help="Target is an AW2401 device.", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    aw2401_parser.add_argument('--device-ip'    , '-i', type=ip_address , help="Device ip address", required=True)
    aw2401_parser.add_argument('--power-id'     , '-p', type=int        , help="Select power id", nargs='+', choices=range(1,5))
    aw2401_parser.add_argument('--power-status' , '-s', type=str        , help="Set power status", choices=['on', 'off'])
    aw2401_parser.add_argument('--get-status'   , '-g', help="Get power status", action="store_true")
    aw2401_parser.add_argument('--verbose'      , '-v', help="Increase output verbosity", action="store_true")

    #print(parser.parse_args())
    args = parser.parse_args()

    #for debug
    #print(args)
    if not args.device:
        parser.error('the following arguments are required: sp8h or aw2401')

    if (not args.power_id and not args.power_status) and (not args.get_status):
        parser.error('the following arguments are required: --power-id/-p and --power_status/-s or --get_status/-g')

    # delete duplicate item
    if args.power_id and hasattr(args, 'power_id'):
        args.power_id = sorted(set(args.power_id), key=args.power_id.index)
        #print(args.power_id)

    # delete duplicate item
    if hasattr(args, 'machine_id'):
        args.machine_id = sorted(set(args.machine_id), key=args.machine_id.index)
        #print(args.machine_id)

    if args.verbose:
        sys.stdout.write('\nPower control utility support sp8h and aw2401.\n\n')

    if args.device == 'sp8h':

        if args.verbose:
            sys.stdout.write('Device sp8h:\n')
            sys.stdout.write('  IP: {}, user: {}, password: {}\n'.format((args.device_ip), (args.user), (args.passwd)))
            sys.stdout.write('  interval: {}(ms), retry: {}, retry_interval: {}(s)\n'.format((args.interval), (args.retry), (args.retry_interval)))

        retry_list = []

        if args.interval < 700:
            parser.error('Interval did not less than 700ms')

        o_sp8h.target_url = str(args.device_ip)
        o_sp8h.user = args.user
        o_sp8h.passwd = args.passwd
        o_sp8h.connect()
        if o_sp8h.login() == None:
            if args.verbose:
                sys.stdout.write('\nLogin sp8h success.\n\n')
            if args.power_id and args.power_status:
                if args.verbose:
                    sys.stdout.write('Set power status for SP8H:\n')

                for mid in args.machine_id:
                    retry_count = args.retry
                    for pid in args.power_id:
                        if args.verbose:
                            sys.stdout.write('  Machine: {}, power_id: {}, status: {:>3s}\n'.format((mid), (pid), (args.power_status)))
                        # Delay for set power starus.
                        time.sleep(args.interval/1000)
                        o_sp8h.switch(mid, pid, 1 if args.power_status == 'on' else 2 if args.power_status == 'off' else 3)

                    # Read back the power status to make sure the setting successful.
                    # Delay for get power starus.
                    time.sleep(1.2)
                    status_data = o_sp8h.get_status(mid)

                    for pid in args.power_id:
                        idx = 1
                        for status in status_data:
                            if idx == pid:
                                if status[0] is not ('1' if args.power_status == 'on' else '0'):
                                    #sys.stdout.write('    Power control fail, power_id: {}, status: {:>3s}\n'.format((idx), 'off' if status[0] is '0' else 'on'))
                                    retry_list.append(pid)
                            idx=idx+1

                    if args.verbose:
                        if retry_list:
                            sys.stdout.write('\nFail to set power status for SP8H:\n')
                            for pid in retry_list:
                                sys.stdout.write('  Machine: {}, power_id: {}, status: {:>3s}\n'.format((mid), (pid), (args.power_status)))

                    while retry_list and retry_count > 0:
                        retry_count=retry_count-1
                        # Delay for each retry cycle.
                        time.sleep(args.retry_interval)
                        for pid in retry_list:
                            # Delay for set power starus.
                            time.sleep(args.interval/1000)
                            o_sp8h.switch(mid, pid, 1 if args.power_status == 'on' else 2 if args.power_status == 'off' else 3)

                        # Read back the power status to make sure the setting successful.
                        # Delay for get power starus.
                        time.sleep(1.2)
                        status_data = o_sp8h.get_status(mid)

                        for pid in retry_list:
                            if len(status_data):
                                idx = 1
                                for status in status_data:
                                    if idx == pid:
                                        if status[0] is ('1' if args.power_status == 'on' else '0'):
                                            sys.stdout.write('    Retry power control success, power_id: {}, status: {:>3s}\n'.format((idx), 'off' if status[0] is '0' else 'on'))
                                            retry_list.remove(pid)
                                        else:
                                            sys.stdout.write('    Retry power control fail, power_id: {}, status: {:>3s}\n'.format((idx), 'off' if status[0] is '0' else 'on'))

                                    idx=idx+1
                            else:
                                sys.stdout.write('    Fail to get power status!\n')

                    sys.stdout.write('\n')
                #End for loop

            if args.get_status:
                sys.stdout.write('Get power status from SP8H:\n')
                for mid in args.machine_id:
                    sys.stdout.write('  Machine {}:\n'.format((mid)))
                    # Delay for get power starus.
                    time.sleep(2.0)
                    status_data = o_sp8h.get_status(mid)
                    if len(status_data):
                        i = 1
                        for status in status_data:
                            sys.stdout.write('    Power_id: {}, status: {:>3s}\n'.format((i), 'off' if status[0] is '0' else 'on'))
                            i=i+1
                    else:
                            sys.stdout.write('    Fail to get power status!\n')


        o_sp8h.logout()
        if args.verbose:
            sys.stdout.write('\nLogout sp8h.')

        o_sp8h.disconnect()
        if args.verbose:
            sys.stdout.write('\nDisconnect sp8h.\n')

        return

    if args.device == 'aw2401':
        o_aw2401 = aw2401()
        o_aw2401.target_url = str(args.device_ip)
        o_aw2401.connect()

        if args.power_id and args.power_status:
            if args.verbose:
                sys.stdout.write('\nSet power status for AW2401:\n')
                for pid in args.power_id:
                    sys.stdout.write('  Power_id:{}, status: {:>3s}\n'.format(pid, args.power_status))

            o_aw2401.switch(args.power_id, 1 if args.power_status == 'on' else 0)

        if args.get_status:
            #sys.stdout.write(o_aw2401.get_status())
            i = 1
            sys.stdout.write('\nGet power status from AW2401:\n')
            for status in o_aw2401.get_status():
                sys.stdout.write('  Power_id:{}, status: {:>3s}\n'.format(i, status))
                i=i+1

        o_aw2401.disconnect()

    return

if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt):
        sys.stdout.write("\nQuitting.\n")
