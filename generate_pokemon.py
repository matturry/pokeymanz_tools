#!/usr/bin/env python3

import argparse
import enum
import math
import random
import yaml

from pokemon_species import PokemonSpecies, SpeciesMove, title, type_string, INDENT_STOP


class Dice:
    def __init__(self, num_range, name, exp_cost):
        self.num_range = num_range
        self.name = name
        self.exp_cost = exp_cost
        self.next_dice = None
        self.prev_dice = None

    def __str__(self):
        return f"{self.name}"

    def set_next_lvl(self, dice):
        self.next_dice = dice
        dice.prev_dice = self


D4m1 = Dice((0,3), "1d4-1", 0)
D4   = Dice((1,4), "1d4", 1)
D6   = Dice((1,6), "1d6", 1)
D8   = Dice((1,8), "1d8", 1)
D10  = Dice((1,10), "1d10", 2)
D12  = Dice((1,12), "1d12", 2)

D4m1.set_next_lvl(D4)
D4.set_next_lvl(D6)
D6.set_next_lvl(D8)
D8.set_next_lvl(D10)


class PokemonMove:
    def __init__(self, move: SpeciesMove, exp: int, species: PokemonSpecies):
        self.move = move
        self.exp = exp
        self.species = species

    def dice(self, pokemon_types):
        dice = self.lowest_level(pokemon_types)
        exp = self.exp
        while exp > dice.exp_cost and dice.next_dice:
            exp -= dice.exp_cost
            dice = dice.next_dice
        return dice

    def to_string(self, color: bool=True, indent_lvl: int = 0):
        indent = INDENT_STOP * indent_lvl
        lines =  [f"{title(self.move.name, color)} ({type_string(self.move.type, color)})"]
        lines += [f"{title("LEVEL:", color)} {self.dice(self.species.types)} ({title("EXP:", color)} {self.exp})"]
        lines += [f"{title("DESCRIPTION:", color)}"]
        lines += [self.move.description]
        lines += [""]
        return '\n'.join(f"{indent}{line}" for line in lines)
    

    def __str__(self):
        return self.to_string(color=False)

    def lowest_level(self, pokemon_types):
        if self.move.type in pokemon_types:
            if len(pokemon_types) == 1:
                return D6
            else:
                assert len(pokemon_types) == 2
                return D4
        return D4m1
        
class Pokemon:
    def __init__(self, species, moves, toughness_exp):
        self.species = species
        self.moves = moves
        self.toughness_exp = toughness_exp

    @property
    def toughness(self):
        return int(2.5 + math.sqrt(2.25 + 2 * self.toughness_exp))

    def to_string(self, color:bool=True, indent_lvl:int=0):
        lines =  [f"{title("POKEMON:", color)} {self.species.name} ({self.species.genus})"]
        lines += [f"{title("DESCRIPTION:", color)} {random.choice(self.species.descriptions)}"]
        lines += [f"{title("TYPE:", color)} {', '.join(type_string(t, color) for t in self.species.types)}"]
        lines += [f"{title("TOUGHNESS:", color)} {self.toughness} ({title("EXP:", color)} {self.toughness_exp})"]
        lines += [title("MOVES:", color)]
        for m in self.moves:
            lines += [m.to_string(color, 1)]
        return '\n'.join(lines)

    def __str__(self):
        return self.to_string(color=False)

    @classmethod
    def generate_pokemon(cls, species, exp_points):
        toughness_exp = random.randint(0, exp_points)
        left_over_exp = exp_points - toughness_exp
        move_exp = [0] * 4
        for i in range(4):
            move_exp[i] = random.randint(0, left_over_exp)
            left_over_exp = left_over_exp - move_exp[i]
        moves = random.sample(species.moves, min(4, len(species.moves)))
        return Pokemon(species,
                       [PokemonMove(m, move_exp, species) for m, move_exp in zip(moves, move_exp)],
                       toughness_exp)

def process_pokemon(pokemon_file):
    with open(pokemon_file, 'r') as f:
        details = yaml.safe_load(f)
    pokemon = []
    cum_prob = 0
    for p_details in details:
        cum_prob += p_details['probability']
        assert cum_prob <= 1
        species = PokemonSpecies.from_db(p_details['species'])
        pokemon += [(species, (p_details['exp']['min'], p_details['exp']['max']), cum_prob)]
    return pokemon


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('pokemon', help='A pokemon generation file')
    return parser.parse_args()

def main(args):
    pokemon = process_pokemon(args.pokemon)
    try:
        while True:
            input("Press key to generate...")
            print()
            prob = random.random()
            for p in pokemon:
                if p[2] > prob:
                    break
            print(Pokemon.generate_pokemon(p[0], random.randint(*p[1])).to_string())
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    main(parse_args())

