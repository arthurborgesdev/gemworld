# Gemworld

An early text-only prototype about buying, cutting, and selling gemstones.

You never see the stone. You read descriptions, listen to sellers, choose cuts, compare markets, and learn to distrust your own imagination.

## How to Play

Run:

```bash
python3 gemworld.py
```

The game saves automatically to `savegame.json`.

## Useful Commands

- `help`
- `status`
- `places`
- `go mine`
- `go workshops`
- `go markets`
- `look`
- `inspect P01`
- `buy P01`
- `inventory`
- `cut P01 iris pear`
- `sell P01 jewelers`
- `journal`
- `save`
- `quit`

## Prototype Core

Each stone has hidden properties, such as material, mass, transparency, saturation, color zoning, fractures, shape, and narrative value. The player does not see those numbers directly. The game turns those properties into partial descriptions.

Vendors have margins and reliability levels. Cutters have cost, finish quality, and risk control. Markets value different things. The same stone can be excellent for one buyer and mediocre for another.

## How to Expand

`gemworld.py` is structured so the prototype can grow through data:

- Add materials in `MATERIALS`.
- Add vendors in `VENDORS`.
- Add cutters in `CUTTERS`.
- Add buyers in `MARKETS`.
- Add cuts in `CUTS` and adjust `cut_affinity`.
- Adjust descriptions in `describe_stone`.
- Adjust the economy in `raw_value`, `finished_value`, `asking_price`, and `sell`.

The natural next step is to move the data into JSON or YAML once the content grows.
