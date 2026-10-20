---
name: basevilanova
description: "Consultar equips, classificacions i calendaris del CNF Base Vilanova (futbol base de Vilanova i la Geltrú): quins equips té el club, com va el Cadet A femení, quan juga el sènior femení, quins partits hi ha aquest cap de setmana. Carrega-la sempre que demanin «els partits del Base Vilanova», «el femení del base», «el cadet/aleví/infantil», «la classificació de l'equip X» o «què juga aquest cap de setmana» referit a aquest club."
version: 1.0.0
author: Trankisen
tags: [futbol, futbol-base, vilanova, penedes, calendari, classificacio, catala]
related_skills: [lafurapenedes]
---

# CNF Base Vilanova — equips, classificacions i calendaris

El **Club Nou de Futbol Base Vilanova 2015** (Vilanova i la Geltrú) té ~60 equips de futbol base
(iniciació → sèniors, masculí i femení). La seva web publica, per a cada equip, la classificació i
el calendari amb dades de la **Federació Catalana de Futbol** incrustades a l'HTML.

**⚠️ No és el CF Vilanova.** El CF Vilanova (Tercera Federació) és un altre club de la mateixa
ciutat. Aquesta skill només cobreix el **CNF Base Vilanova** (cnfbasevilanova.cat).

## Ús

```bash
S=~/.hermes/skills/research/basevilanova/scripts/basevilanova.py

python3 $S equips                       # catàleg complet (categoria · slug · nom · lliga)
python3 $S equips --categoria cadets    # només una categoria
python3 $S cerca femeni                 # tots els equips femenins del club
python3 $S equip cadet-a-femeni         # classificació + propers partits
python3 $S equip senior-femeni --resultats
python3 $S setmana                      # propers partits de TOT el club (8 dies)
python3 $S setmana --dies 15
python3 $S --json equip cadet-a-femeni  # sortida JSON (per integrar)
```

Categories: `seniors`, `juvenils`, `cadets`, `infantils`, `alevi`, `benjami`, `prebenjami`,
`iniciacio`, `futbol-pc`.

## Què retorna

- **equips**: `categoria`, `slug`, `nom`, `lliga`, `nota`. Els equips amb `slug` buit (mostrat com a
  `-`) **no tenen fitxa** al web (p. ex. «Cadet B femení», «Aleví S12E»): existeixen però la
  Federació no en publica classificació.
- **equip**: `nom`, `lliga`, `equip_fcf` (el nom federatiu, p. ex. `BASE VILANOVA 2015, CLUB NOU FUTBOL A`),
  `classificacio[]` (pos, pj, g, e, p, gf, gc, dg, punts, `propi`), `partits[]` (jornada, local,
  visitant, marca, hora, data, camp, `descansa`, `propi`).
- **setmana**: competició, seu (a casa/fora), equip, rival, data, hora i camp de cada partit.

## Trampes conegudes

1. **El calendari d'un equip inclou TOTS els partits del grup.** Per això el camp `propi` existeix:
   marca les files de l'equip (ressaltades al web). Filtra sempre per `propi` abans de respondre;
   si no, respondràs amb partits d'altres clubs.
2. **Els noms del club es repeteixen** (`BASE VILANOVA 2015, CLUB NOU FUTBOL A/B/C`) en grups
   diferents. L'`equip_fcf` de cada fitxa és el bo: no endevinis la lletra pel nom de l'equip.
3. **El club NO publica plantilles.** Ni noms ni dorsals: és política explícita del club. Si et
   demanen la plantilla, digues-ho i ofereix les vies (oficina del club, entrenador/delegat).
4. **Un equip pot descansar** aquella jornada: surt una fila `descansa: true` (amb la data heretada
   del cap de setmana del grup).
5. **Les dades no són en directe**: el web porta un «Actualitzat: …» de la Federació que pot anar
   unes hores endarrerit. Si l'usuari pregunta per un partit d'avui, comprova la data/hora i
   avisa que la font és la FCF.
6. **L'hora dels partits futurs** ve al camp `hora` (format `HH:MM`); en els jugats, la `marca` és el
   resultat (`2–1`).
7. **La primera fila de la classificació** de vegades és un equip amb `PJ 0` (equip afegit al grup
   que encara no ha jugat): no vol dir que vagi primer.Ordena mentalment pels punts.

## Com donar la resposta

1. Executa l'script amb l'equip o la categoria demanada (si no en diu cap, `setmana` per al club).
2. Dona **primer el que és urgent**: el pròxim partit (dia, hora, camp, casa/fora, rival) i després
   la classificació resumida (posició, punts, ratxa).
3. Als partits, tradueix el nom federatiu a un nom llegible (`BASE VILANOVA 2015, CLUB NOU FUTBOL A`
   → «Base Vilanova»).
4. Escriu els noms dels rivals en minúscula quan sigui possible («Monjos», «Martorell») — el web els
   posa tot en majúscules.
5. Respon en català i sense bolcar tota la taula si són 13-15 equips: posició pròpia + els 3 de dalt
   i els 3 de baix.

## Rendiment

- Cada pàgina de categoria pesa ~3-4 MB (HTML del Next.js del club). El catàleg complet són 9
  pàgines i la primera vegada triga ~5-10 s.
- Tot queda a `~/.hermes/cache/basevilanova/` (30 min per a calendaris, 12 h per al catàleg):
  les consultes següents són instantànies. `--no-cache` només per depurar.

## Verificació

Un `setmana` normal torna entre 8 i 25 partits segons el cap de setmana. Si surt 0, pot ser que el
club encara no hagi publicat la jornada: prova `--dies 20` abans de dir que no hi ha res.
