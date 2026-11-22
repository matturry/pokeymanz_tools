#!/usr/bin/env python3
import argparse
import random

from flask import Flask, render_template

from helpers.generate_pokemon import process_pokemon, generate_pokemon

app = Flask(__name__)

@app.route("/")
def main():
    pokemon = generate_pokemon(app.config.pokemon_details)
    return render_template(
            "index.html",
            name=pokemon.species.name,
            description=random.choice(pokemon.species.descriptions),
            moves=pokemon.moves,
            sprite_url=f"static/{pokemon.species.sprite}",
            details={
                "Types": ", ".join(pokemon.species.types),
                "XP": pokemon.exp,
                "Toughness": f"{pokemon.toughness} ({pokemon.toughness_exp} XP)" ,
                "Weak": ", ".join(pokemon.species.weak) if pokemon.species.weak else "-",
                "Strong": ", ".join(pokemon.species.strong) if pokemon.species.strong else "-",
                "Immune": ", ".join(pokemon.species.immune) if pokemon.species.immune else "-",
    })

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('pokemon', help='A pokemon generation file')
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    app.config.pokemon_details = process_pokemon(args.pokemon)
    app.run()
