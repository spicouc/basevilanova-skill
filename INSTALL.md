# Instal·lació de la skill `basevilanova`

Equips, classificacions i calendaris del CNF Base Vilanova per a Hermes Agent.

## Opció A — Des del repositori (recomanada)

```bash
hermes skills install spicouc/basevilanova-skill/basevilanova --category research
```

## Opció B — Manual

1. Copia la carpeta `basevilanova` al directori de skills de Hermes:

```bash
mkdir -p ~/.hermes/skills/research
cp -r basevilanova ~/.hermes/skills/research/
```

2. Comprova que funciona:

```bash
hermes skills list | grep basevilanova
python3 ~/.hermes/skills/research/basevilanova/scripts/basevilanova.py setmana
```

3. Si tens el gateway obert, fes `/reload-skills`.

## Ús

```bash
S=~/.hermes/skills/research/basevilanova/scripts/basevilanova.py
python3 $S equips
python3 $S cerca femeni
python3 $S equip cadet-a-femeni --resultats
python3 $S setmana --dies 15
```

O simplement pregunta-li a Hermes: «què juga el Base Vilanova aquest cap de setmana?» i la skill es
carrega sola.

## Requisits

- Python 3.8+ i només biblioteca estàndard (`urllib`, `json`, `re`, `html`). Cap `pip install`.
- Connexió a internet: llegeix cnfbasevilanova.cat (dades de la FCF incrustades a l'HTML).
- La primera consulta del catàleg triga ~5-10 s (9 pàgines de 3-4 MB); després queda a la caché
  (`~/.hermes/cache/basevilanova/`) i és instantani.

## Llicència

Codi i text lliures. Les dades són del club i de la Federació Catalana de Futbol.
