# -*- coding: utf-8 -*-
import os
from gelo import main, conf
import signal
import argparse
import configparser

GELO = main.Gelo()


def main():
    """Parse the command line arguments into a Gelo configuration."""
    # Construct the parser
    parser = argparse.ArgumentParser(prog='gelo')
    parser.add_argument('show',
                        help='the slug and episode number of the show, like'
                        ' fnt-192')
    parser.add_argument('-c',
                        '--config',
                        default=os.path.expandvars(
                            '$HOME/.config/gelo/gelo.ini'),
                        type=open,
                        help='path to configuration file')
    parser.add_argument('-p',
                        '--user-plugin-dir',
                        default='',
                        help='path to user plugins directory, overrides config'
                        ' file')
    parser.add_argument('-l',
                        '--log-level',
                        choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO',
                                 'DEBUG'],
                        default='CRITICAL',
                        help='the level of logging, one of: CRITICAL, '
                             'ERROR, WARNING, INFO, or DEBUG')
    args = parser.parse_args()
    # Parse the configuration file
    config_file = configparser.ConfigParser()
    config_file.read_file(args.config)
    # Create the Gelo Configuration
    config = conf.Configuration(config_file, args)
    # Add the handler to shut down Gelo
    signal.signal(signal.SIGINT, exit_handler)
    # Call Gelo's main function
    GELO.main(config)


def exit_handler(sig, frame):
    """Shut down and clean up Gelo when killed with CTRL-C"""
    GELO.shutdown()


if __name__ == "__main__":
    main()
