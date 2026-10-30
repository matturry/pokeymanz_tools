#!/usr/bin/env python3

import argparse


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('pokemon')
    return parser.parse_args()


def main(args):
    print(args.pokemon)

if __name__ == '__main__':
    main(parse_args())
