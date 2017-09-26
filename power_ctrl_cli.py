#!/usr/bin/env python3
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

    parser = power_ctrl_cliparser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    subparsers = parser.add_subparsers(title='Support devices', dest='device', help="device")

    #sp8h command
    sp8h_parser = subparsers.add_parser('sp8h', help="Target is a SP8H device.", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    sp8h_parser.add_argument('--device-ip'      , '-i', type=ip_address , help="Device ip address", required=True)
    sp8h_parser.add_argument('--user'           , '-U', type=str        , help="Username for login SP8H", default='admin')
    sp8h_parser.add_argument('--passwd'         , '-P', type=str        , help="Password for login SP8H", default='admin')
    sp8h_parser.add_argument('--machine-id'     , '-m', type=int        , help="Select machine id", nargs='+', choices=range(1,5), required=True)
    sp8h_parser.add_argument('--power-id'       , '-p', type=int        , help="Select power id", nargs='+', choices=range(1,9), required=True)
    sp8h_parser.add_argument('--power-status'   , '-s', type=str        , help="Set power status", choices=['on', 'off'], required=True)
    sp8h_parser.add_argument('--verbose'        , '-v', help="Increase output verbosity", action="store_true")

    #aw2401 command
    aw2401_parser = subparsers.add_parser('aw2401', help="Target is an AW2401 device.", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    aw2401_parser.add_argument('--device-ip'    , '-i', type=ip_address , help="Device ip address", required=True)
    aw2401_parser.add_argument('--power-id'     , '-p', type=int        , help="Select power id", nargs='+', choices=range(1,5), required=True)
    aw2401_parser.add_argument('--power-status' , '-s', type=str        , help="Set power status", choices=['on', 'off'], required=True)
    aw2401_parser.add_argument('--verbose'      , '-v', help="Increase output verbosity", action="store_true")

    #print(parser.parse_args())
    args = parser.parse_args()

    #for debug
    #print(args)
    if not args.device:
        parser.print_help()

    # delete duplicate item
    if hasattr(args, 'power_id'):
        args.power_id = sorted(set(args.power_id), key=args.power_id.index)
        #print(args.power_id)

    # delete duplicate item
    if hasattr(args, 'machine_id'):
        args.machine_id = sorted(set(args.machine_id), key=args.machine_id.index)
        #print(args.machine_id)

    if args.device == 'sp8h':
        o_sp8h = sp8h()
        o_sp8h.target_url = str(args.device_ip)
        o_sp8h.user = args.user
        o_sp8h.passwd = args.passwd
        o_sp8h.connect()
        if o_sp8h.login() == None:
            for mid in args.machine_id:
                for pid in args.power_id:
                    if args.verbose:
                        sys.stdout.write('Power {:>3s}, machine: {}, power_id: {}\n'.format((args.power_status), (mid), (pid)))
                    time.sleep(0.3)
                    o_sp8h.switch(mid, pid, 1 if args.power_status == 'on' else 2)

            o_sp8h.logout()

        o_sp8h.disconnect()

        return

    if args.device == 'aw2401':
        o_aw2401 = aw2401()
        o_aw2401.target_url = str(args.device_ip)
        o_aw2401.connect()
        if args.verbose:
            for pid in args.power_id:
                sys.stdout.write('Power {:>3s}, power_id: {}\n'.format(args.power_status, pid))

        o_aw2401.switch(args.power_id, 1 if args.power_status == 'on' else 0)
        time.sleep(0.3)
        o_aw2401.disconnect()

    return

if __name__ == "__main__":
    main()
