# bivouac — où peut-on dormir dehors en France, et sous quelles règles

Le bivouac en France n'est interdit ni autorisé « en général » : il dépend du
zonage sous vos pieds, et chaque zonage a son propre texte. Un même vallon peut
être à la fois site classé, Natura 2000, parc naturel régional et réserve
naturelle — trois de ces quatre couches n'interdisent rien, la quatrième peut
tout interdire.

Ce dépôt réunit **les géométries des zonages de protection** et **les règles de
bivouac qui s'y appliquent**, jointes par identifiant, dans un schéma unique et
machine-lisible.

**Carte : https://tonio.github.io/bivouac/**

## Ce que le projet cherche à faire

Répondre à « puis-je dormir ici ? » avec la règle réelle et sa référence, plutôt
qu'avec une recommandation générique.

Concrètement, cela veut dire préférer un fait daté et sourcé — « tente interdite
du 1er juillet au 31 août par l'arrêté préfectoral du 16/07/2024, la belle étoile
reste permise » — à un « renseignez-vous auprès du gestionnaire ». Les règles sont
stockées en champs atomiques (horaires, type de tente, nombre de nuits, distance,
saison, coût) et non en prose, pour rester exploitables.

Deux conséquences assumées :

- **Un zonage écologique n'est pas un zonage réglementaire.** Natura 2000 et les
  PNR couvrent d'immenses surfaces sans rien interdire. Les afficher comme
  contraignants ferait croire à des interdictions inexistantes.
- **Le silence n'est pas une interdiction.** Quand aucun acte ne fixe d'horaire ou
  de durée, le champ vaut `null` avec la raison, jamais une valeur plausible
  inventée.

## Organisation

| dossier | rôle |
|---|---|
| [`pipeline/`](pipeline/README.md) | téléchargement des zonages, règles de bivouac, jointure, génération du GeoJSON et du PMTiles |
| [`app/`](app/README.md) | la carte de consultation (Vue 3 + MapLibre), et son déploiement |
| [`SOURCES.md`](SOURCES.md) | attribution, licences, texte à afficher — **à lire avant toute publication** |

```sh
cd pipeline && ./fetch.sh && ./fetch_osm.sh && ./zones_internes.py && ./build.py --pmtiles
cd app && yarn install && yarn dev
```

Le détail — schéma des champs, règles par type de zonage, méthode de
vérification — est dans le README de chaque dossier.

## Couverture

13 types de zonages, ~7100 objets géoréférencés : les 11 parcs nationaux
(cœur et aire d'adhésion), réserves naturelles nationales, régionales et de
Corse, réserves biologiques ONF, arrêtés de protection de biotope, sites classés,
terrains du Conservatoire du littoral, parcs naturels régionaux, Natura 2000, et
36 zonages internes aux parcs.

Les règles génériques par type couvrent tout le jeu. **57 sites** sont en plus
vérifiés un par un contre leur décret ou leur arrêté, et surchargent la règle de
leur type quand celle-ci est fausse pour eux — ce qui est fréquent : « interdit
sauf exception » est faux pour une bonne partie des réserves, dont plusieurs
autorisent explicitement le bivouac.

## Limites juridiques

**Ces données n'ont aucune valeur juridique.** Elles aident à préparer une sortie ;
elles ne remplacent pas la consultation du gestionnaire ni celle de l'acte.

Ce qui n'y est pas, et qui peut pourtant interdire :

- **Les arrêtés municipaux.** ~35 000 communes peuvent interdire le camping par
  arrêté motivé (C. urb. R111-34). Il n'existe aucune base nationale :
  l'exhaustivité est structurellement impossible.
- **Les arrêtés préfectoraux incendie.** Souvent le facteur le plus contraignant
  de l'été — fermeture totale de massifs par vent fort — et non géoréférencés
  nationalement. Dans les Bouches-du-Rhône, l'accès est recalculé *chaque jour*.
- **Les 1103 arrêtés de protection de biotope**, non consolidés nationalement :
  le jeu de données donne la référence de l'acte, sa lecture reste manuelle.
- **Les sites inscrits** (~4500), régime distinct des sites classés, absents des
  couches sources.

Ce qui y est mais peut avoir changé : les arrêtés de directeur de parc sont
révisés d'une saison à l'autre. Pendant la dernière vérification, deux arrêtés
cités par ce dépôt se sont révélés abrogés. Chaque fiche porte donc un champ
`fiabilite` et ses sources, pour que vous puissiez remonter au texte.

Enfin, **bivouac et camping ne sont pas la même notion** en droit. Plusieurs
textes n'interdisent que le second : une tente montée le soir et démontée au
matin ne relève pas du même régime qu'une installation à demeure. Un site classé,
par exemple, n'interdit pas de dormir dehors.

En cas de doute sur place, la règle la plus contraignante des zonages superposés
s'applique — c'est ce que la carte affiche en premier.

## Licence

Les données sources sont sous Licence Ouverte 2.0 et ODbL selon les couches ; le
jeu final est à traiter comme de l'**ODbL** (partage à l'identique). Détail et
texte d'attribution : [SOURCES.md](SOURCES.md).

> Données d'aide à la préparation, sans valeur juridique.
> Vérifier auprès du gestionnaire avant de partir.
