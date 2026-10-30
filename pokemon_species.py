#!/usr/bin/env python3

import argparse
import enum

from colorama import Fore, Style

import pokebase
from pokebase import cache

INDENT_STOP = " " * 2

class PokeType(enum.StrEnum):
    NORMAL = 'normal'
    ELECTRIC = 'electric'
    FAIRY = 'fairy'
    DARK = 'dark'
    STEEL = 'steel'
    PSYCHIC = 'psychic'
    WATER = 'water'
    ICE = 'ice'
    FLYING = 'flying'
    GRASS = 'grass'
    POISON = 'poison'
    FIGHTING = 'fighting'

TYPE_COLOR = {
    PokeType.NORMAL: "",
    PokeType.ELECTRIC: Fore.YELLOW,
    PokeType.FAIRY: Fore.MAGENTA + Style.BRIGHT,
    PokeType.DARK: Fore.MAGENTA + Style.DIM,
    PokeType.STEEL: Fore.WHITE + Style.DIM,
    PokeType.PSYCHIC: Fore.MAGENTA,
    PokeType.WATER: Fore.BLUE,
    PokeType.ICE: Fore.CYAN + Style.BRIGHT,
    PokeType.FLYING: Fore.CYAN,
    PokeType.GRASS: Fore.GREEN,
    PokeType.POISON: Fore.MAGENTA + Style.DIM,
    PokeType.FIGHTING: Fore.RED,
}

def type_string(_type: PokeType, color=True) -> str:
    if not color:
        return str(_type)
    return f"{TYPE_COLOR[_type]}{str(_type)}{Style.RESET_ALL}" 

def title(text, color=True):
    if not color:
        return text
    return f"{Style.BRIGHT}{text}{Style.RESET_ALL}"

def reflow_text(text):
    return text.replace('\n', ' ').replace('\u000c', ' ')

def fetch_english(field):
    return [entry for entry in field if entry.language.name == 'en']

class Move:
    def __init__(self, name: str, description: str, _type: PokeType):
        self.name: str = name
        self.description: str = description
        self.type: PokeType = _type

    def to_string(self, color: bool = True, indent_lvl: int = 0) -> str:
        indent = INDENT_STOP * indent_lvl
        lines = [
            f"{title(self.name, color)} ({type_string(self.type, color)})",
            self.description
        ]
        return '\n'.join(f"{indent}{l}" for l in lines)

    def __str__(self):
        return self.to_string(color=False)

    @classmethod
    def from_db(cls, key: str) -> Move:
        res = pokebase.APIResource('move', key)
        name = fetch_english(res.names)[0].name
        # The move descriptions don't add much, just take one of them
        description = reflow_text(fetch_english(res.flavor_text_entries)[-1].flavor_text)
        _type = PokeType(res.type.name)
        return cls(name, description, _type)

class PokemonSpecies:
    def __init__(self, name: str, genus: str, types: List[PokeType], descriptions: List[str], moves: List[Move]):
        self.name = name
        self.types = types
        self.descriptions = descriptions
        self.moves = moves
        self.genus = genus

    def to_string(self, color: bool = True, indent_lvl: int = 0):
        indent = INDENT_STOP * indent_lvl
        text =  [f"{title("POKEMON:", color)} {self.name} ({self.genus})"]
        text += [f"{title("DESCRIPTIONS:", color)}"]
        for desc in self.descriptions:
            text += [f" - {desc}"]
        text += [f"{title("EVOLUTION:", color)}"]
        text += [f"{title("TYPE:", color)} {', '.join(type_string(t, color) for t in self.types)}"]
        text += [title("MOVES:", color)]
        for m in self.moves:
            text += [m.to_string(color, indent_lvl=1), ""]
        return '\n'.join(f"{indent}{l}" for l in text)

    @staticmethod
    def _filter_db_moves_by_learn_method(moves, method: str) -> list[str]:
        filtered_moves = []
        for m in moves:
            learn_methods = set(vgd.move_learn_method.name for vgd in m.version_group_details)
            if method in learn_methods:
                filtered_moves += [m.move.name]
        return filtered_moves

    @classmethod
    def from_db(cls, key: str) -> PokemonSpecies:
        res = pokebase.APIResource('pokemon', key)
        name = fetch_english(res.species.names)[0].name
        descriptions = list(set(reflow_text(desc.flavor_text) for desc in fetch_english(res.species.flavor_text_entries)))
        types = [PokeType(t.type.name) for t in res.types]
        moves = [Move.from_db(k) for k in cls._filter_db_moves_by_learn_method(res.moves, 'level-up')]
        genus = reflow_text(fetch_english(res.species.genera)[0].genus)
        return cls(name, genus, types, descriptions, moves)


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
    p = PokemonSpecies.from_db(args.pokemon)
    print(p.to_string())

if __name__ == '__main__':
    main(parse_args())
