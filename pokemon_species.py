#!/usr/bin/env python3

import argparse
import dataclasses
import enum

from colorama import Fore, Style

from helpers.db import PokeDB, filter_by_language

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
    ROCK = 'rock'
    GROUND = 'ground'
    GHOST = 'ghost'
    DRAGON = 'dragon'
    BUG = 'bug'
    FIRE = 'fire'

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
    PokeType.ROCK: Fore.RED + Style.DIM,
    PokeType.GROUND: Fore.GREEN + Style.DIM,
    PokeType.GHOST: Fore.BLUE + Style.DIM,
    PokeType.DRAGON: Fore.YELLOW + Style.BRIGHT,
    PokeType.BUG: Fore.GREEN + Style.BRIGHT,
    PokeType.FIRE: Fore.RED + Style.BRIGHT,
}

def type_string(_type: PokeType, color=True) -> str:
    if not color:
        return str(_type)
    return f"{TYPE_COLOR[_type]}{str(_type)}{Style.RESET_ALL}" 

def title(text, color=True):
    if not color:
        return text
    return f"{Style.BRIGHT}{text}{Style.RESET_ALL}"


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
    def from_db(cls, name: str) -> Move:
        res = PokeDB.move.find_by_key(name)
        name = filter_by_language(res.names)[0].name
        # The move descriptions don't add much, just take one of them
        description = filter_by_language(res.flavor_text_entries)[-1].flavor_text
        _type = PokeType(res.type.name)
        return cls(name, description, _type)

@dataclasses.dataclass
class EvolutionNode:
    _species: str
    evolves_from: EvolutionNode|None
    evolves_to: List[EvolutionNode]
    triggered_by: str|None = None
    trigger_item: str|None = None
    held_item: str|None = None
    time_of_day: str|None = None
    held_item: str|None = None
    time_of_day: str|None = None
    location: str|None = None
    known_move_type: PokeType|None = None

    def find_evolution(self, species):
        if self._species == species:
            return self
        for c in self.evolves_to:
            n = c.find_evolution(species)
            if n:
                return n
        return None

    def __str__(self):
        trig_str = self.triggered_by
        if self.trigger_item:
            trig_str += f" Item: {self.trigger_item}"
        if self.held_item:
            trig_str += f" Held Item: {self.held_item}"
        if self.time_of_day:
            trig_str += f" Time Of Day: {self.time_of_day}"
        if self.location:
            trig_str += f" Location: {self.location}"
        if self.known_move_type:
            trig_str += f" Known Move Type: {self.known_move_type}"
        return f"{self.species.name} ({trig_str})"

    @property
    def species(self):
        return PokemonSpecies.from_db(self._species)

    @classmethod
    def tree_from_chain(cls, chain, ev_from=None, **trigger_info):
        node = cls(chain.species.name,
                   evolves_from=ev_from,
                   evolves_to=[],
                   **trigger_info)
        node.evolves_to = []
        for ev in chain.evolves_to:
            ev_details = ev.evolution_details[-1]
            triggers = {
                "triggered_by": filter_by_language(ev_details.trigger.names, "en")[0].name
            }
            if ev_details.item:
                triggers["trigger_item"] = filter_by_language(ev_details.item.names, "en")[0].name
            if ev_details.held_item:
                triggers["trigger_item"] = filter_by_language(ev_details.held_item.names, "en")[0].name
            if ev_details.time_of_day:
                triggers["time_of_day"] = ev_details.time_of_day
            if ev_details.location:
                triggers["location"] = filter_by_language(ev_details.location.names, "en")[0].name
            if ev_details.known_move_type:
                triggers["known_move_type"] = PokeType(ev_details.known_move_type.name)

            node.evolves_to += [EvolutionNode.tree_from_chain(ev, node, **triggers)]
        return node

class PokemonSpecies:
    def __init__(self, name: str, genus: str, types: List[PokeType], descriptions: List[str],
                 moves: List[Move], evolves_from: str|None = None, evolves_to: List[str]|None = None):
        self.name = name
        self.types = types
        self.descriptions = descriptions
        self.moves = moves
        self.genus = genus
        self.evolves_from = evolves_from
        self.evolves_to = evolves_to if evolves_to is not None else []

    def to_string(self, color: bool = True, indent_lvl: int = 0):
        indent = INDENT_STOP * indent_lvl
        text =  [f"{title("POKEMON:", color)} {self.name} ({self.genus})"]
        text += [f"{title("DESCRIPTIONS:", color)}"]
        for desc in self.descriptions:
            text += [f" - {desc}"]
        text += [f"{title("EVOLVED FROM:", color)} {self.evolves_from}"]
        text += [f"{title("EVOLVES_TO:", color)}"]
        for s in self.evolves_to.evolves_to:
            text += [f" - {str(s)}"]
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
    def from_db(cls, pokemon: str) -> PokemonSpecies:
        res = PokeDB.pokemon.find_by_key(pokemon)
        name = filter_by_language(res.species.names, 'en')[0].name

        descriptions = list(set(
            desc.flavor_text for desc in filter_by_language(res.species.flavor_text_entries, 'en')
        ))
        types = [PokeType(t.type.name) for t in res.types]
        moves = [Move.from_db(k) for k in cls._filter_db_moves_by_learn_method(res.moves, 'level-up')]
        genus = filter_by_language(res.species.genera, 'en')[0].genus
        evolves_from = None
        if res.species.evolves_from_species:
            evolves_from = filter_by_language(res.species.evolves_from_species.names, 'en').pop().name
        evolution_tree = EvolutionNode.tree_from_chain(res.species.evolution_chain.chain)
        ev_node = evolution_tree.find_evolution(pokemon)
        return cls(name, genus, types, descriptions, moves, evolves_from, ev_node)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('pokemon')
    return parser.parse_args()

def main(args):
    p = PokemonSpecies.from_db(args.pokemon)
    print(p.to_string())

if __name__ == '__main__':
    main(parse_args())
