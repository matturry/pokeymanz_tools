#!/usr/bin/env python3

import argparse

from colorama import Fore, Style

import pokebase
from pokebase import cache


POKE_TYPE_COLOR = {
    'normal': '',
    'electric': Fore.YELLOW,
    'fairy': Fore.MAGENTA + Style.BRIGHT,
    'dark': Fore.MAGENTA + Style.DIM,
    'steel': Fore.WHITE + Style.DIM,
    'psychic': Fore.MAGENTA,
    'water': Fore.BLUE,
    'ice': Fore.CYAN + Style.BRIGHT,
    'flying': Fore.CYAN, 
    'grass': Fore.GREEN,
    'poison': Fore.MAGENTA + Style.DIM
}

def format_type(_type):
    return f"{POKE_TYPE_COLOR.get(_type, '')}{_type}{Style.RESET_ALL}"

def title(text):
    return f"{Style.BRIGHT}{text}{Style.RESET_ALL}"

def reflow_text(text):
    return text.replace('\n', ' ').replace('\u000c', ' ')

def fetch_english(field):
    return [entry for entry in field if entry.language.name == 'en']

def filter_moves_by_learn_method(moves, by):
    filtered_moves = []
    for move in moves:
        move_learn_methods = set(vgd.move_learn_method.name for vgd in move.version_group_details)
        if by in move_learn_methods:
            filtered_moves += [move]
    return filtered_moves

def display_move(move, indent_lvl=0):
    indent = " " * (2 * indent_lvl)
    move_output = [f"{indent}{title(fetch_english(move.names)[0].name)} ({format_type(move.type.name)})"]
    move_output += [f"{indent}{reflow_text(fetch_english(move.flavor_text_entries)[0].flavor_text)}"]
    return "\n".join(move_output) 

def display_pokemon(pokemon):
    text =  [f"{title("POKEMON:")} {pokemon.name} ({reflow_text(fetch_english(pokemon.species.genera)[0].genus)})"]
    text += [f"{title("DESCRIPTION:")} {reflow_text(fetch_english(pokemon.species.flavor_text_entries)[0].flavor_text)}"]
    text += [f"{title("TYPE:")} {', '.join(format_type(t.type.name) for t in pokemon.types)}"]
    text += [title("MOVES:")]
    for move in filter_moves_by_learn_method(pokemon.moves, 'level-up'):
        text += [display_move(move.move, indent_lvl=1), ""]
    return text

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('pokemon')
    parser.add_argument('--flush-cache', action='store_true')
    parser.add_argument('--cache-path', default='.cache')
    return parser.parse_args()

def main(args):
    cache.set_cache(args.cache_path)
    if args.flush_cache:
        cache.empty_cache()
    pokemon = pokebase.APIResource('pokemon', args.pokemon)
    print('\n'.join(display_pokemon(pokemon)))

if __name__ == '__main__':
    main(parse_args())
