# -*- coding: utf-8 -*-
import gelo
import argparse
import configparser
import os

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
    args = parser.parse_args()
    # Parse the configuration file
    config_file = configparser.ConfigParser()
    config_file.read_file(args.config)
    # Create the Gelo Configuration
    config = gelo.Configuration(config_file, args)
    # Call Gelo's main function
    gelo.main(config)


if __name__ == "__main__":
    main()