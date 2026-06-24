#!/usr/bin/env python3
from __future__ import annotations

import json
import random
import textwrap
from dataclasses import asdict, dataclass
from pathlib import Path


SAVE_PATH = Path(__file__).with_name("savegame.json")
WORLD_SEED = 71342


MATERIALS = {
    "amethyst": {
        "base": 18,
        "colors": ["cool violet", "wine purple", "deep lavender", "grayish violet"],
        "temper": "rewards saturation, but exposes color zoning in deeper cuts",
    },
    "citrine": {
        "base": 14,
        "colors": ["clear honey", "burnt gold", "pale amber", "dry orange"],
        "temper": "sells well when warm and clean, but loses strength when watery",
    },
    "garnet": {
        "base": 24,
        "colors": ["closed red", "dark wine", "black cherry", "brownish ruby"],
        "temper": "looks cheaper than it is when too dark, but sharp buyers pay for density",
    },
    "beryl": {
        "base": 31,
        "colors": ["sea green", "washed blue", "dry green", "nearly colorless"],
        "temper": "needs cleanliness and proportion; a small fracture hurts confidence",
    },
    "rutilated quartz": {
        "base": 20,
        "colors": ["clear with golden threads", "light smoky", "translucent straw", "warm colorless"],
        "temper": "accepts inclusions when they read as pattern, not accident",
    },
}


SHAPES = ["long", "blocky", "flat", "irregular", "pointed"]
CUTS = ["pear", "kite", "cabochon", "rectangle"]
LOCATION_ALIASES = {
    "mine": "mine",
    "mines": "mine",
    "workshop": "workshops",
    "workshops": "workshops",
    "market": "markets",
    "markets": "markets",
}


VENDORS = {
    "nora": {
        "name": "Nora Finch",
        "honesty": 0.87,
        "margin": 1.22,
        "voice": "speaks sparingly, wraps each rough in thin paper, and dislikes haste",
    },
    "ellis": {
        "name": "Ellis Ravine",
        "honesty": 0.52,
        "margin": 0.82,
        "voice": "laughs before answering and calls almost everything an opportunity",
    },
    "gray": {
        "name": "The Gray Brothers",
        "honesty": 0.68,
        "margin": 1.02,
        "voice": "sell as a pair, one too technical and the other too sentimental",
    },
}


CUTTERS = {
    "oliver": {
        "name": "Oliver Salt",
        "fee": 36,
        "rate": 2.2,
        "risk_control": 0.18,
        "finish": 0.72,
        "voice": "conservative, good at saving difficult material, and slow to promise impossible fire",
    },
    "iris": {
        "name": "Iris Ferron",
        "fee": 50,
        "rate": 2.8,
        "risk_control": 0.08,
        "finish": 0.91,
        "voice": "aggressive, excellent with long cuts, and unforgiving when the rough was chosen badly",
    },
}


MARKETS = {
    "jewelers": {
        "name": "The Jewelers' House",
        "taste": "wants transparency, symmetry, and very little romance",
        "transparency": 1.25,
        "saturation": 0.85,
        "story": 0.55,
        "fracture": 1.35,
    },
    "collectors": {
        "name": "The Collectors' Fair",
        "taste": "pays for origin, strangeness, and memorable character",
        "transparency": 0.75,
        "saturation": 1.05,
        "story": 1.35,
        "fracture": 0.65,
    },
    "amulets": {
        "name": "The Amulet Market",
        "taste": "prefers expressive color, suggestive shape, and a story that travels easily",
        "transparency": 0.65,
        "saturation": 1.28,
        "story": 1.15,
        "fracture": 0.85,
    },
}


@dataclass
class Stone:
    id: str
    material: str
    mass: float
    color: str
    transparency: float
    saturation: float
    zoning: float
    fracture: float
    shape: str
    story: float
    vendor: str
    bought_for: int = 0
    cut_cost: int = 0
    cut: str = ""
    cutter: str = ""
    broken: bool = False


@dataclass
class GameState:
    day: int
    money: int
    reputation: int
    location: str
    market_stones: list[Stone]
    inventory: list[Stone]
    journal: list[str]


def wrap(text: str) -> str:
    return textwrap.fill(text, width=88)


def say(text: str = "") -> None:
    if not text:
        print()
        return
    print(wrap(text))


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def band(value: float, low: str, mid: str, high: str) -> str:
    if value < 0.34:
        return low
    if value < 0.67:
        return mid
    return high


def article_for(text: str) -> str:
    return "an" if text[:1].lower() in {"a", "e", "i", "o", "u"} else "a"


def stable_rng(*parts: object) -> random.Random:
    text = ":".join(str(part) for part in parts)
    seed = WORLD_SEED
    for char in text:
        seed = ((seed * 33) + ord(char)) % 2_147_483_647
    return random.Random(seed)


def raw_value(stone: Stone) -> float:
    material = MATERIALS[stone.material]
    clarity = 0.55 + stone.transparency * 0.75
    color = 0.62 + stone.saturation * 0.78
    fracture = 1.0 - stone.fracture * 0.48
    story = 0.82 + stone.story * 0.34
    zoning = 1.0 - max(0, stone.zoning - 0.58) * 0.24
    return stone.mass * material["base"] * clarity * color * fracture * story * zoning


def asking_price(stone: Stone) -> int:
    vendor = VENDORS[stone.vendor]
    rng = stable_rng("price", stone.id)
    noise = rng.uniform(0.9, 1.12)
    return max(8, round(raw_value(stone) * vendor["margin"] * noise))


def describe_stone(stone: Stone, for_inventory: bool = False) -> str:
    vendor = VENDORS[stone.vendor]
    rng = stable_rng("desc", stone.id, "owned" if for_inventory else "market")
    honesty = 1.0 if for_inventory else vendor["honesty"]

    perceived_transparency = clamp(stone.transparency + rng.uniform(-0.16, 0.16) * (1.1 - honesty))
    perceived_saturation = clamp(stone.saturation + rng.uniform(-0.18, 0.18) * (1.1 - honesty))
    perceived_fracture = clamp(stone.fracture + rng.uniform(-0.22, 0.18) * (1.1 - honesty))
    perceived_zoning = clamp(stone.zoning + rng.uniform(-0.20, 0.20) * (1.1 - honesty))

    transparency = band(
        perceived_transparency,
        "cuts the light short before it crosses the piece",
        "lets light through with some internal haze",
        "holds light inside with good cleanliness",
    )
    saturation = band(
        perceived_saturation,
        "a restrained color, almost shy",
        "a present color, but not loud",
        "an intense color, the kind that stays in memory",
    )
    fracture = band(
        perceived_fracture,
        "shows no obvious fracture to the naked eye",
        "carries an internal line that asks for attention",
        "has a fracture that may dictate the cut",
    )
    zoning = band(
        perceived_zoning,
        "a fairly even tone",
        "a shift in tone from one end to the other",
        "strong color zones, beautiful or dangerous depending on the cut",
    )

    article = article_for(stone.shape).capitalize()
    intro = f"{stone.id}. {article} {stone.shape} piece of rough {stone.material}, {stone.mass:.1f} g."
    body = (
        f"The color is {stone.color}: {saturation}. The piece {transparency}. "
        f"It has {zoning}. It {fracture}."
    )
    if for_inventory:
        tail = "Now that the stone is in your hand, the description feels less like a promise and more like a concrete problem."
    else:
        tail = f"{vendor['name']} asks {asking_price(stone)} coins and {vendor['voice']}."
    return " ".join([intro, body, tail])


def cut_affinity(stone: Stone, cut: str) -> float:
    score = 0.0
    if cut == "pear":
        score += 0.18 if stone.shape in {"long", "pointed"} else -0.05
        score += 0.08 if stone.saturation > 0.55 else 0
    elif cut == "kite":
        score += 0.15 if stone.shape in {"long", "irregular"} else -0.04
        score += 0.08 if stone.zoning > 0.50 else 0
    elif cut == "cabochon":
        score += 0.16 if stone.transparency < 0.52 or stone.fracture > 0.45 else -0.06
        score += 0.06 if stone.story > 0.55 else 0
    elif cut == "rectangle":
        score += 0.18 if stone.shape == "blocky" else -0.08
        score += 0.12 if stone.transparency > 0.62 else -0.04
    return score


def finished_value(stone: Stone, market_key: str) -> int:
    market = MARKETS[market_key]
    base = raw_value(stone)
    if not stone.cut:
        return round(base * 0.62)

    finish = CUTTERS[stone.cutter]["finish"] if stone.cutter else 0.66
    cut_bonus = 1.0 + cut_affinity(stone, stone.cut) + finish * 0.22
    market_fit = (
        stone.transparency * market["transparency"]
        + stone.saturation * market["saturation"]
        + stone.story * market["story"]
        - stone.fracture * market["fracture"]
    )
    market_fit = 0.72 + clamp(market_fit / 2.9) * 0.72
    break_penalty = 0.46 if stone.broken else 1.0
    return max(4, round(base * cut_bonus * market_fit * break_penalty))


def initial_state() -> GameState:
    rng = random.Random(WORLD_SEED)
    stones: list[Stone] = []
    vendor_keys = list(VENDORS)
    material_keys = list(MATERIALS)
    for index in range(1, 13):
        material = rng.choice(material_keys)
        data = MATERIALS[material]
        stone = Stone(
            id=f"P{index:02d}",
            material=material,
            mass=round(rng.uniform(4.8, 23.5), 1),
            color=rng.choice(data["colors"]),
            transparency=clamp(rng.betavariate(2.2, 2.0)),
            saturation=clamp(rng.betavariate(2.0, 2.1)),
            zoning=clamp(rng.betavariate(1.7, 2.6)),
            fracture=clamp(rng.betavariate(1.4, 3.0)),
            shape=rng.choice(SHAPES),
            story=clamp(rng.betavariate(1.8, 2.2)),
            vendor=rng.choice(vendor_keys),
        )
        stones.append(stone)
    return GameState(
        day=1,
        money=650,
        reputation=0,
        location="mine",
        market_stones=stones,
        inventory=[],
        journal=[
            "You arrived with 650 coins, an empty notebook, and a decision not to trust anyone's eyes."
        ],
    )


def state_to_json(state: GameState) -> dict:
    return asdict(state)


def state_from_json(data: dict) -> GameState:
    state = GameState(
        day=data["day"],
        money=data["money"],
        reputation=data["reputation"],
        location=data["location"],
        market_stones=[Stone(**item) for item in data["market_stones"]],
        inventory=[Stone(**item) for item in data["inventory"]],
        journal=list(data["journal"]),
    )
    if state.location not in {"mine", "workshops", "markets"}:
        return initial_state()
    stones = state.market_stones + state.inventory
    if any(stone.vendor not in VENDORS for stone in stones):
        return initial_state()
    if any(stone.cutter and stone.cutter not in CUTTERS for stone in stones):
        return initial_state()
    if any(stone.cut and stone.cut not in CUTS for stone in stones):
        return initial_state()
    return state


def save(state: GameState) -> None:
    SAVE_PATH.write_text(json.dumps(state_to_json(state), indent=2), encoding="utf-8")


def load_or_new() -> GameState:
    if SAVE_PATH.exists():
        return state_from_json(json.loads(SAVE_PATH.read_text(encoding="utf-8")))
    return initial_state()


def find_stone(stones: list[Stone], stone_id: str) -> Stone | None:
    wanted = stone_id.upper()
    return next((stone for stone in stones if stone.id.upper() == wanted), None)


def print_intro() -> None:
    say("Gemworld")
    say()
    say(
        "You never see the stone. You read descriptions, listen to interested people, write down suspicions, and decide what risk is worth."
    )
    say("Type 'help' for commands. Type 'save' to save the game.")
    say()


def show_help() -> None:
    say("Main commands:")
    for line in [
        "status: show money, reputation, and current place.",
        "places: describe the available places.",
        "go mine, go workshops, or go markets: move to another place.",
        "look: list what is available where you are.",
        "inspect P01: read the description of a stone for sale or in your inventory.",
        "buy P01: buy a stone at the mine.",
        "inventory: list your stones.",
        "cut P01 iris pear: send a stone to a cutter and choose the cut.",
        "sell P01 jewelers: sell a stone to a market.",
        "journal: reread recent events.",
        "new: erase the current save and restart.",
        "quit: save and exit.",
    ]:
        say(line)


def show_status(state: GameState) -> None:
    say(f"Day {state.day}. You have {state.money} coins, reputation {state.reputation}, and you are at {state.location}.")


def show_locations() -> None:
    say("Dry Creek Mine: vendors offer fresh rough, good and bad mixed together.")
    say("Low Street Workshops: cutters turn hypotheses into consequences.")
    say("Old Bridge Markets: different buyers see different values in the same stone.")


def look(state: GameState) -> None:
    if state.location == "mine":
        say("At the mine, wrapped stones, low voices, and practiced indifference fill the shade.")
        for key, vendor in VENDORS.items():
            stones = [stone.id for stone in state.market_stones if stone.vendor == key]
            if stones:
                verb = "have" if vendor["name"].startswith("The ") else "has"
                say(f"{vendor['name']} {verb} {', '.join(stones)}.")
        say("Use 'inspect P01' to read a stone and 'buy P01' if you accept the price.")
    elif state.location == "workshops":
        say("The workshops smell of water, mineral dust, and heated metal.")
        for key, cutter in CUTTERS.items():
            say(f"{key}: {cutter['name']}, {cutter['voice']}. Charges {cutter['fee']} coins plus {cutter['rate']:.1f} per gram.")
        say("Available cuts: " + ", ".join(CUTS) + ".")
    elif state.location == "markets":
        say("At Old Bridge, one buyer calls a flaw what another buyer calls a soul.")
        for key, market in MARKETS.items():
            say(f"{key}: {market['name']}, {market['taste']}.")


def examine(state: GameState, stone_id: str) -> None:
    stone = find_stone(state.inventory, stone_id)
    if stone:
        say(describe_stone(stone, for_inventory=True))
        if stone.cut:
            condition = "fragmented" if stone.broken else "whole"
            say(f"It was cut as a {stone.cut} by {CUTTERS[stone.cutter]['name']} and remains {condition}.")
        return
    stone = find_stone(state.market_stones, stone_id)
    if stone:
        say(describe_stone(stone))
        return
    say("You cannot find that stone.")


def buy(state: GameState, stone_id: str) -> None:
    stone = find_stone(state.market_stones, stone_id)
    if not stone:
        say("That stone is not for sale.")
        return
    price = asking_price(stone)
    if price > state.money:
        say(f"The price is {price} coins. You do not have that much right now.")
        return
    state.money -= price
    stone.bought_for = price
    state.market_stones.remove(stone)
    state.inventory.append(stone)
    state.journal.append(f"You bought {stone.id}, {stone.material}, from {VENDORS[stone.vendor]['name']} for {price} coins.")
    say(f"You bought {stone.id} for {price} coins. The stone now weighs more in your hand than in your purse.")


def inventory(state: GameState) -> None:
    if not state.inventory:
        say("Your stone cloth is empty.")
        return
    for stone in state.inventory:
        cut = f", cut as a {stone.cut}" if stone.cut else ", still rough"
        costs = []
        if stone.bought_for:
            costs.append(f"purchase {stone.bought_for}")
        if stone.cut_cost:
            costs.append(f"cutting {stone.cut_cost}")
        cost = f" Costs: {', '.join(costs)} coins." if costs else ""
        say(f"{stone.id}: {stone.material}, {stone.mass:.1f} g{cut}.{cost}")


def cut_stone(state: GameState, stone_id: str, cutter_key: str, cut: str) -> None:
    stone = find_stone(state.inventory, stone_id)
    if not stone:
        say("That stone is not in your inventory.")
        return
    if stone.cut:
        say("That stone has already been cut. This prototype has no recutting yet.")
        return
    if cutter_key not in CUTTERS:
        say("Unknown cutter. Use 'look' in the workshops to see the names.")
        return
    if cut not in CUTS:
        say("Unknown cut. Available cuts are: " + ", ".join(CUTS) + ".")
        return

    cutter = CUTTERS[cutter_key]
    cost = round(cutter["fee"] + stone.mass * cutter["rate"])
    if cost > state.money:
        say(f"{cutter['name']} would charge {cost} coins. You do not have that much right now.")
        return

    state.money -= cost
    stone.cut_cost += cost
    rng = stable_rng("cut", state.day, stone.id, cutter_key, cut)
    affinity = cut_affinity(stone, cut)
    break_chance = clamp(0.08 + stone.fracture * 0.32 + max(0, -affinity) * 0.55 - cutter["risk_control"])
    loss = clamp(0.18 + max(0, -affinity) * 0.22 + rng.uniform(-0.03, 0.08), 0.12, 0.48)

    stone.cut = cut
    stone.cutter = cutter_key
    if rng.random() < break_chance:
        stone.broken = True
        stone.mass = round(stone.mass * (1.0 - loss - rng.uniform(0.12, 0.22)), 1)
        state.reputation -= 1
        result = (
            f"{cutter['name']} charged {cost} coins, but {stone.id} opened where you feared it would. "
            f"The stone survived as a {cut}, but fragmented."
        )
    else:
        stone.mass = round(stone.mass * (1.0 - loss), 1)
        state.reputation += 1 if affinity > 0.08 else 0
        loss_word = "acceptable" if loss < 0.30 else "painful"
        result = (
            f"{cutter['name']} charged {cost} coins and delivered {stone.id} as a {cut}. "
            f"The mass loss felt {loss_word}, but now there is a stone you can sell."
        )
    state.day += 1
    state.journal.append(result)
    say(result)


def sell(state: GameState, stone_id: str, market_key: str) -> None:
    stone = find_stone(state.inventory, stone_id)
    if not stone:
        say("That stone is not in your inventory.")
        return
    if market_key not in MARKETS:
        say("Unknown market. Use 'look' in the markets to see buyers.")
        return

    value = finished_value(stone, market_key)
    rng = stable_rng("sell", state.day, stone.id, market_key, state.reputation)
    offer = round(value * rng.uniform(0.88, 1.08) * (1.0 + max(-5, min(8, state.reputation)) * 0.015))
    market = MARKETS[market_key]
    state.money += offer
    state.inventory.remove(stone)
    total_cost = stone.bought_for + stone.cut_cost
    profit = offer - total_cost
    state.reputation += 1 if profit > 0 and stone.cut else -1 if profit < -40 else 0
    state.day += 1

    if profit >= 0:
        mood = f"You left with {profit} coins above the recorded total cost."
    else:
        mood = f"You lost {-profit} coins against the recorded total cost."
    result = f"{market['name']} paid {offer} coins for {stone.id}. {mood}"
    state.journal.append(result)
    say(result)


def show_journal(state: GameState) -> None:
    for entry in state.journal[-12:]:
        say(entry)


def new_game() -> GameState:
    if SAVE_PATH.exists():
        SAVE_PATH.unlink()
    state = initial_state()
    save(state)
    say("Game restarted.")
    return state


def handle(state: GameState, command: str) -> GameState | None:
    parts = command.strip().lower().split()
    if not parts:
        return state
    verb = parts[0]

    if verb in {"help", "?"}:
        show_help()
    elif verb == "status":
        show_status(state)
    elif verb == "places":
        show_locations()
    elif verb == "go" and len(parts) >= 2:
        destination = LOCATION_ALIASES.get(parts[1], "")
        if destination:
            state.location = destination
            say(f"You went to {destination}.")
            look(state)
        else:
            say("That place is not on the initial map.")
    elif verb == "look":
        look(state)
    elif verb == "inspect" and len(parts) >= 2:
        examine(state, parts[1])
    elif verb == "buy" and len(parts) >= 2:
        buy(state, parts[1])
    elif verb == "inventory":
        inventory(state)
    elif verb == "cut" and len(parts) >= 4:
        cut_stone(state, parts[1], parts[2], parts[3])
    elif verb == "sell" and len(parts) >= 3:
        sell(state, parts[1], parts[2])
    elif verb == "journal":
        show_journal(state)
    elif verb == "save":
        save(state)
        say("Game saved.")
    elif verb == "new":
        state = new_game()
    elif verb == "quit":
        save(state)
        say("Game saved. You close the notebook before anyone can read your margins.")
        return None
    else:
        say("Command not recognized. Type 'help'.")
    return state


def main() -> None:
    state = load_or_new()
    print_intro()
    look(state)
    while True:
        try:
            command = input("\n> ")
        except (EOFError, KeyboardInterrupt):
            print()
            save(state)
            say("Game saved.")
            break
        next_state = handle(state, command)
        if next_state is None:
            break
        state = next_state
        save(state)


if __name__ == "__main__":
    main()
