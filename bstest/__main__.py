#!/usr/bin/env python3

import bstest
import bstest._utils as UTILS
import argparse
import pytest
import os

import logging

logger = logging.getLogger('bstest')
logger.setLevel('ERROR')


def parse_args():
    """Utility function for parsing bstest command line arguments

    Returns
    -------
    dict
        Dictionary of arguments and their values
    """

    parser = argparse.ArgumentParser(description='A utility for ' \
                        'leveraging bluesky and ophyd automation for EPICS device testing.')

    parser.add_argument('-p', '--prefix', 
                        help='Specifies the prefix for an existing IOC to test against.')

    parser.add_argument('-o', '--output',
                        help='Specifies the filename to output to. Default is stdout.')

    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Runs bstest test cases in verbose mode.')

    parser.add_argument('-d', '--debug', action='store_true',
                        help='Enables debug logging for bstest')

    parser.add_argument('-i', '--ignore-warnings', action='store_true',
                        help='Suppresses warnings generated by pytest')

    args = vars(parser.parse_args())
    return args


def validate_args(args):
    err_msg = None

    if args['prefix'] is not None and not UTILS.is_ioc_ready(args['prefix'], timeout=2):
        err_msg = f'Connection timeout to IOC w/ prefix {args["prefix"]}. ' \
                    'Are you sure it is running?'

    if args['output'] is not None:
        if not os.path.exists(args['output']) and not os.access(os.path.dirname(args['output']), os.W_OK):
            err_msg = f'Output path {args["output"]} does not exist, and cannot be created.'
        elif not os.access(args['output'], os.W_OK):
            err_msg = f'Output path {args["output"]} exists, but you ' \
                        'don\'t have permission to write to it'

    return (err_msg is None), err_msg
    

def get_welcome_text():
    """Returns a simple ascii header for cli utility
    
    Returns
    -------
    str
        A welcome message string, listing version and environment info.
    """

    out_txt =  f'+{"-" * 64}+\n'
    out_txt += f'+ bstest - Version: {bstest.__version__:<45}+\n'
    out_txt += f'+ {bstest.__copyright__:<63}+\n'
    out_txt += f'+ {UTILS.get_environment():<63}+\n'
    out_txt += f'+ {"This software comes with NO warranty!":<63}+\n'
    out_txt += f'+{"-" * 64}+\n'
    return out_txt


def main():
    """Main exectuion function for bstest
    """

    # Collect user arguments
    args = parse_args()
    
    # Input argument validation step
    args_valid, err_msg = validate_args(args)
    if not args_valid:
        bstest.write(f'ERROR - {err_msg}')
        exit(-1)

    
    bstest.EXTERNAL_PREFIX = args['prefix']
    if args['output'] is not None:
        bstest.OUTPUT_FP = open(args['output'], 'a')


    bstest.write(get_welcome_text())

    if bstest.EXTERNAL_PREFIX is not None:
        bstest.write(f'Running tests against IOC with prefix {bstest.EXTERNAL_PREFIX}...')
    else:
        bstest.write('Running tests against auto-generated ADSimDetector IOCs...')

        # Ensure docker is installed, and appropriate images available
        docker_status, msg = bstest.validate_docker()
        bstest.write(msg)
        
        if not docker_status:
            bstest.cleanup(error_code=-1)

    # Change to the bstest directory
    bstest_install_dir = os.path.dirname(os.path.abspath(bstest.__file__))
    cwd = os.getcwd()
    os.chdir(bstest_install_dir)

    # Run pytest main
    pytest.main([])
    os.chdir(cwd)

    bstest.cleanup()


if __name__ == '__main__':
    main()
