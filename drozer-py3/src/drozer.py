#!/usr/bin/env python3

import sys

Commands = {    'agent': 'create custom drozer Agents',
                'console': 'start the drozer Console',
                'exploit': 'generate an exploit to deploy drozer',
                'module': 'manage drozer modules',
                'payload': 'generate payloads to deploy drozer',
                'server': 'start a drozer Server',
                'ssl': 'manage drozer SSL key material' }
    
def print_usage():
    print("usage: drozer [COMMAND]")
    print()
    print("Run `drozer [COMMAND] --help` for more usage information.")
    print()
    print("Commands:")
    for command in Commands:
        print("  %15s  %s" % (command, Commands[command]))
    print()


if len(sys.argv) > 1:
    if sys.argv[1] in Commands:
        __import__("drozer.cli.%s" % (sys.argv[1]))
    else:
        print("unknown command:", sys.argv[1])
        print_usage()
else:
    print_usage()
