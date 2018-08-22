#!/usr/bin/env python3
"""
Scripts for creating mock data for carbon/grafana for Tendrl.

based on: https://github.com/cloudbehl/carbon-random
"""

import argparse
import datetime
import logging
import sys
from pprint import pformat

import yaml

import usmqe_cmdg.carbon_client


# configure logging
logging.basicConfig(level=logging.DEBUG, \
        format='#%(levelname)-7s: %(message)s')
logging.getLogger().setLevel(logging.WARNING)
LOGGER = logging.getLogger("usmqe_cmdg")
LOGGER.setLevel(logging.INFO)

def parse_args(args=None, namespace=None):
    """
    Parse command line arguments.
    """
    parser = argparse.ArgumentParser( \
        description="Generate mock data for carbon (grafana) for Tendrl", \
        formatter_class=argparse.RawDescriptionHelpFormatter, \
        epilog="Example:\n" \
            "  List all available metrics: \n" \
            "  # ./usmqe_carbon_mock_data_generator.py -s server.example.com list\n\n" \
            "  List all available metrics containing 'used_capacity' string: \n" \
            "  # ./usmqe_carbon_mock_data_generator.py -s server.example.com list -f 'used_capacity'\n\n" \
            "  List all available metrics containing 'utilization'\n" \
            "  but not containing 'inode' and 'thin_pool':\n" \
            "  # ./usmqe_carbon_mock_data_generator.py -s server.example.com list \\\n" \
            "       -f 'utilization !inode !thin_pool'\n\n" \
            "  Generate data from 2018-07-01 till now based on configuration file:\n" \
            "  # ./usmqe_carbon_mock_data_generator.py -s server.example.com  generate \\\n" \
            "       --since 2018-07-01 -c example_config.yml\n" \
        )
    parser.add_argument( \
        "-s", "--server", metavar='HOSTNAME',
        required=False, default="localhost",
        help="Hostname/IP address of carbon and grafana server. " \
            "(default: localhost)")
    parser.add_argument( \
        "--carbon-port", metavar='PORT',
        required=False, default=2003, type=int,
        help="carbon port (default: 2003)")
    parser.add_argument( \
        "--grafana-port", metavar='PORT',
        required=False, default=3000, type=int,
        help="grafana port (default: 3000)")
    parser.add_argument( \
        "-f", "--filter", metavar='FILTER', default="",
        help="Space separated list of words for filtering the list of metrics. " \
            "Multiple words in the filter are combined with logical AND. " \
            "Exclamation mark before the word means negative filter for that word." \
            "(Note: enclose the filter in apostrophes, to avoid exclamation mark expansion in Bash.)")
    _since_default = datetime.datetime.now().strftime("%Y-%m-%dT00:00:00")
    parser.add_argument( \
        "--since", metavar='DATETIME', type=valid_date, \
        default=_since_default, \
        help="Start date in the YYYY-MM-DD[THH[:MM[:SS]]] format. " \
            "Default: today 0am (%s)" % _since_default)
    _until_default = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    parser.add_argument( \
        "--until", metavar='DATETIME', type=valid_date,
        default=_until_default, \
        help="End date in the YYYY-MM-DD[THH[:MM[:SS]]] format. " \
            "Default: now (%s)" % _until_default)
    parser.add_argument( \
        "--interval", metavar='INTERVAL',
        required=False, default=60, type=int,
        help="Metrics interval in seconds. (default 60s)")
    parser.add_argument( \
        "-d", "--debug", action="store_true", default=False,
        help="More verbose output.")

    actions = ['list', 'generate']
    parser.add_argument( \
        "action", metavar="ACTION", \
        choices=actions, \
        help="Specify desired action: %s" % actions)

    parser.add_argument( \
        "-c", "--config", metavar="CONFIGFILE", \
        default="", \
        help="Configuration in yaml format for the data generation.")

    args = parser.parse_args(args=args, namespace=namespace)
    return args


def valid_date(value):
    """
    Parse given value as various forms of date and return timestamp.
    """
    if value == "":
        return value
    if isinstance(value, datetime.date):
        _d = datetime.datetime.combine(value, datetime.datetime.min.time())
        return int(_d.replace(tzinfo=datetime.timezone.utc).timestamp())
    try:
        _d = datetime.datetime.strptime(value, "%H")
        _today = datetime.date.today()
        _d = _d.replace(year=_today.year, month=_today.month, day=_today.day)
        return int(_d.replace(tzinfo=datetime.timezone.utc).timestamp())
    except ValueError:
        pass
    try:
        _d = datetime.datetime.strptime(value, "%H:%M:%S")
        _today = datetime.date.today()
        _d = _d.replace(year=_today.year, month=_today.month, day=_today.day)
        return int(_d.replace(tzinfo=datetime.timezone.utc).timestamp())
    except ValueError:
        pass
    try:
        _d = datetime.datetime.strptime(value, "%H:%M")
        _today = datetime.date.today()
        _d = _d.replace(year=_today.year, month=_today.month, day=_today.day)
        return int(_d.replace(tzinfo=datetime.timezone.utc).timestamp())
    except ValueError:
        pass
    try:
        return int(datetime.datetime.strptime(value, "%Y-%m-%d").replace( \
                tzinfo=datetime.timezone.utc).timestamp())
    except ValueError:
        pass
    try:
        return int(datetime.datetime.strptime(value, "%Y-%m-%dT%H").replace( \
                tzinfo=datetime.timezone.utc).timestamp())
    except ValueError:
        pass
    try:
        return int(datetime.datetime.strptime(value, "%Y-%m-%dT%H:%M").replace( \
                tzinfo=datetime.timezone.utc).timestamp())
    except ValueError:
        pass
    try:
        return int(datetime.datetime.strptime(value, "%Y-%m-%dT%H:%M:%S").replace( \
                tzinfo=datetime.timezone.utc).timestamp())
    except ValueError:
        pass
    msg = "Not a valid date: '{0}'.".format(value)
    raise argparse.ArgumentTypeError(msg)


def main():
    """
    Main method.
    """
    # parse command line arguments
    args = parse_args()
    if args.debug:
        LOGGER.setLevel(logging.DEBUG)

    cc = usmqe_cmdg.carbon_client.CarbonClient(server=args.server, \
            carbon_port=args.carbon_port, grafana_port=args.grafana_port)

    if args.action == "list":
        metrics = cc.list_metrics(args.filter)
        for metric in metrics:
            print(metric)

    if args.action == "generate":

        if not args.config:
            LOGGER.error("Configuration file (-c/--config) have to be specified for data generation.")
            sys.exit(1)
        # check configuration file type
        if not args.config.lower().endswith(("yaml", "yml")):
            LOGGER.error("Unknown configuration file type: '%s', required: 'yml' or 'yaml'.", \
                    args.config.split('.')[-1])
            sys.exit(1)

        try:
            # load configuration from file
            with open(args.config) as cfg_file:
                cfg_set = yaml.load(cfg_file)
        except (PermissionError, FileNotFoundError, yaml.YAMLError) as err:
            LOGGER.error(err)
            sys.exit(1)

        for cfg in cfg_set:
            # parse since date (or update it from command line args)
            if "since" in cfg:
                cfg["since"] = valid_date(cfg["since"])
            else:
                cfg["since"] = args.since

            # parse until date (or update it from command line args)
            if "until" in cfg:
                cfg["until"] = valid_date(cfg["until"])
            else:
                cfg["until"] = args.until

            # check update time period
            if cfg["since"] > cfg["until"]:
                LOGGER.error("Since date should be before until date (since: %s - until: %s)", \
                        datetime.datetime.utcfromtimestamp( \
                            cfg["since"]).strftime("%Y-%m-%d %H:%M:%S"), \
                        datetime.datetime.utcfromtimestamp( \
                            cfg["until"]).strftime("%Y-%m-%d %H:%M:%S"))
                sys.exit(1)

            # update "interval" from command line args, if not set in configuration
            if "interval" not in cfg:
                cfg["interval"] = args.interval

            # generate metrics
            LOGGER.info("Config set: %s", pformat(cfg))
            cc.generate_metrics(cfg)

if __name__ == '__main__':
    main()

# vim:tabstop=4:shiftwidth=4:softtabstop=4:
