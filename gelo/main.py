# -*- coding: utf-8 -*-
"""Gelo: a podcast chapter metadata gathering tool"""
import argparse

def main():
    """The main function for Gelo, which parses args and starts everything up.
    Uses argparse on the argument list, try --help"""

    parser = argparse.ArgumentParser(prog='gelo')
    parser.add_argument('show',
                        help='the slug and episode number of the show, like fnt-192')
    parser.add_argument('-c',
                        '--config',
                        default='gelo.ini',
                        type=open,
                        help='alternate configuration file')
    parser.parse_args()

    print("Sorry, this doesn't do anything yet.")
