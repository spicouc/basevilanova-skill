# basevilanova — skill per a Hermes Agent

Equips, classificacions i calendaris del **CNF Base Vilanova** (futbol base de Vilanova i la Geltrú)
per a Hermes Agent. Respon a «quins partits té aquest cap de setmana el Base Vilanova?», «com va el
Cadet A femení?», «quan juga el sènior femení?» o «quins equips femenins té el club?».

## Instal·lació

```bash
hermes skills install spicouc/basevilanova-skill/basevilanova --category research
```

O manualment: copiar la carpeta `basevilanova/` dins `~/.hermes/skills/research/`.

## Ús

```bash
S=~/.hermes/skills/research/basevilanova/scripts/basevilanova.py

python3 $S equips                       # catàleg: totes les categories
python3 $S equips --categoria cadets
python3 $S cerca femeni                 # els 11 equips femenins del club
python3 $S equip cadet-a-femeni         # classificació + propers partits
python3 $S equip senior-femeni --resultats
python3 $S setmana                      # propers partits de tot el club
python3 $S --json equip s15a            # sortida JSON
```

Categories: `seniors`, `juvenils`, `cadets`, `infantils`, `alevi`, `benjami`, `prebenjami`,
`iniciacio`, `futbol-pc`.

## Requisits

- Python 3.8+ i **només biblioteca estàndard**. Cap `pip install`.
- Internet: web pública del club (dades de la Federació Catalana de Futbol incrustades a l'HTML).
- Caché a `~/.hermes/cache/basevilanova/` (30 min calendaris, 12 h catàleg).

## Contingut

```
basevilanova/
├── SKILL.md
└── scripts/
    └── basevilanova.py
```

## Nota

Aquesta skill cobreix el **CNF Base Vilanova** (cnfbasevilanova.cat). El **CF Vilanova** — el club de
Tercera Federació de la mateixa ciutat — és un altre club i no hi és cobert.

## Llicència

Codi i text lliures per fer-los servir i modificar. Les dades són del club i de la Federació
Catalana de Futbol.
