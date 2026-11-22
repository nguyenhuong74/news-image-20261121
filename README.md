# The World in One Page — Saturday 21 November 2026

A newspaper front page drawn as a single 1024x1024 PNG, summing up the
world news of Saturday 21 November 2026. Built for the make.fun
competition `news-image-20261121`.

## What is on the page

- **Lead story — Ukraine.** A double-tap ballistic strike on Kryvyi Rih,
  President Zelenskyy's hometown, killed a seven-year-old boy and a
  20-year-old woman and wounded 60 people, six of them children, as a
  second missile hit while rescuers were still at work. The lead
  illustration shows the city at dusk: stars, a moon, lit windows, and
  two missile trails arcing down to impact bursts.
- **Mexico.** FBI Top 10 fugitive Fausto Isidro Meza Flores — "El Chapo
  Isidro" — seized in Guasave with US help; 11 people died in the
  fighting.
- **Climate / COP31.** Talks in Antalya ran into overtime with no deal;
  the draft text is still silent on fossil fuels.
- **Markets.** The Nasdaq fell 5.28% on Friday, erasing its 2026 gains;
  Nvidia dropped 14%.
- **Washington.** President Trump weighs new strikes on Iran as Israel
  presses him to move quickly.
- **Europe.** The EU approved 1 billion euros of military support for
  Ukraine as Moscow rejected a peace deal.
- **By the numbers.** 60 wounded in Kryvyi Rih, 11 killed in Sinaloa,
  5.28% — the Nasdaq's Friday fall.
- **In brief.** Nigeria: a boat capsizes on the way to a funeral, killing
  24. Peru: a magnitude 6.7 earthquake strikes the Junin region. South
  Africa: Phumzile Mlambo-Ngcuka, ex-deputy president, dies at 71.

## How it works

`main.py` is pure Python 3 with only the standard library (`math`, `os`,
`struct`, `zlib`). It contains:

- its own 5x7 bitmap font, drawn by hand, covering A–Z, 0–9 and common
  punctuation (including a euro sign);
- small drawing helpers — rectangles, lines, circles, triangles,
  polylines and wrapped text — on top of a flat RGB bytearray canvas;
- its own PNG encoder (filter type 0 scanlines, zlib compression,
  hand-built IHDR/IDAT/IEND chunks).

There is no network access, no clock and no randomness, so every run
produces byte-identical output.

## How to run it

```sh
MAKEFUN_OUTPUT_DIR=out python3 main.py
```

This writes `out/entry.png` (1024x1024, under 1 MiB). When
`MAKEFUN_OUTPUT_DIR` is not set, the image is written to
`/output/entry.png`.

## License

MIT — see `LICENSE`.
