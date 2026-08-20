# pipeline — construction du jeu de données

Télécharge les zonages de protection, y attache les règles de bivouac, produit
un GeoJSON et un PMTiles uniques.

```sh
./fetch.sh              # 11 couches nationales -> data/*.geojson (~300 Mo, ~2 min)
./fetch_osm.sh          # refuges Vanoise depuis OSM
./zones_internes.py     # zonages internes aux parcs -> data/zones_internes.geojson
./build.py --pmtiles    # jointure -> out/bivouac.{geojson,pmtiles}

./build.py --demo       # self-check de la jointure
./test_regles.py        # validation des fiches de règles
```

`data/` et `out/` ne sont pas versionnés : ~670 Mo entièrement reproductibles.

## Où vivent les règles

| fichier | contenu |
|---|---|
| `rules/par-type.json` | la règle générique de chaque type de zonage, quand le site n'est pas documenté individuellement |
| `rules/parcs-nationaux.json` | les 11 cœurs de parc, un par un — chacun a son arrêté de directeur |
| `rules/reserves.json` | les sites vérifiés un par un, qui **surchargent** la règle de leur type |

La jointure se fait sur `id_mnhn`. Le champ `type` de chaque fiche de
`reserves.json` dit à quelle couche elle s'applique : un même `id_mnhn` peut
exister dans plusieurs couches superposées, et une fiche dont le `type` ne
correspond pas serait ignorée en silence — d'où l'assertion dans `--demo`.

## Sortie

`out/bivouac.geojson` — 7126 objets, un schéma unique. `out/bivouac.pmtiles` — 93 Mo, zoom 5–12.

| champ | contenu |
|---|---|
| `type` | `pn`, `pnr`, `n2000_sic`, `n2000_zps`, `rnn`, `rnr`, `rnc`, `apb`, `rb`, `site_classe`, `cdl`, `zone_interne`, `aire_bivouac` |
| `statut` | `interdit`, `interdit_sauf_exception`, `verifier_arrete`, `restreint_zones`, `regime_specifique`, `autorise_sous_conditions`, `renvoi_droit_commun` |
| `severite` | 0–5, pour styler et résoudre les superpositions |
| `resume` | la règle en une phrase |
| `regle_json` | la règle complète en JSON (champs atomiques ci-dessous) |
| `acte`, `fiche_inpn` | référence de l'acte juridique, fiche INPN du site |

`regle_json` contient des champs machine-lisibles plutôt que de la prose :

```json
{"statut":"restreint_zones",
 "tente":{"autorisee":true,"type":"legere_sans_station_debout","station_debout_autorisee":false,"autoportante_autorisee":null},
 "horaires":{"debut":"19:00","fin":"08:00"},
 "localisation":{"contrainte":"proximite_refuge_obligatoire","distance_min_acces_routier":null,"corridor_m":null,"refuge_obligatoire":true},
 "duree":{"nuits_max":1,"consecutif_meme_lieu":false},
 "cout":{"payant":true,"montant_eur":5,"unite":"emplacement","reservation_obligatoire":true},
 "feu":{"feu_ouvert":false,"rechaud_portatif":true},
 "saison":"1er juin – 30 septembre"}
```

Énums : `tente.type` ∈ {`aucune_restriction`, `legere_sans_station_debout`, `sans_tente_uniquement`, `interdite`} ·
`localisation.contrainte` ∈ {`libre`, `distance_acces`, `proximite_refuge_obligatoire`, `couloir_sentier`, `aires_designees`} ·
`horaires` accepte `HH:MM` ou `coucher_soleil`, `coucher_soleil-1h`, `lever_soleil+1h`, `tombee_nuit`, `lever_jour`.

Un champ à `null` signifie « aucune source ne le fixe », pas « zéro » : voir
[Ce que null veut dire](#ce-que-null-veut-dire).

## Les 11 parcs nationaux, cœur de parc

| Parc | Bivouac | Horaires | Tente | Où | Coût |
|---|---|---|---|---|---|
| **Écrins** | oui | 19h–9h | pas de station debout | >1h de marche des limites **et** des parkings/routes en cœur ; sauf Pré de la Chaumette et abords du refuge de l'Olan | gratuit |
| **Mercantour** | oui | 19h–9h | non autoportante | >1h de marche ; Merveilles/Fontanalbe : 2 aires | gratuit |
| **Pyrénées** | oui | 19h–9h | petite tente | >1h de marche ; Néouvielle : aires Orédon/Aubert | gratuit |
| **Vanoise** | restreint | **19h–8h** | pas de station debout | **aires de refuges gardés uniquement** | **~5 €/emplacement, résa obligatoire** (tarif fixé par délibération du CA, non par arrêté — à confirmer au refuge) |
| **Cévennes** | restreint | 19h–9h | légère **ou sans tente** | **≤50 m d'un GR/GRP**, hors 10 tronçons interdits | gratuit |
| **Forêts** | oui | **coucher −1h → lever +1h** | petite tente | à proximité des voies et sentiers | gratuit |
| **Réunion** | restreint | coucher → matinée | **hamac admis** | libre sauf 5 zones interdites | gratuit |
| **Guadeloupe** | restreint | tombée nuit → lever jour | pas de station debout | **campement : 5 abris nommés** ; îlets interdits sauf Pâques/Pentecôte ; bivouac libre ailleurs en cœur | gratuit |
| **Guyane** | régime spécifique | — | hamac | autorisation requise selon zone (ZAR, ZDUC) | selon zone |
| **Calanques** | **interdit** | — | interdite | dérogation du directeur possible en droit | — |
| **Port-Cros** | **interdit** | — | interdite | dérogation du directeur possible en droit | — |

Partout : **1 nuit**, feu au sol interdit, réchaud portatif toléré (sauf Calanques, où le réchaud gaz est aussi interdit).
Sanction usuelle 68 €/personne (contravention de 3e classe, C. env. art. R331-64).

**Aire d'adhésion** (`FR34000xx`) : aucune réglementation « cœur », retour au droit commun.

## Autres zonages

| Type | Statut | Pourquoi |
|---|---|---|
| Site classé (2657) | **à vérifier** | R111-33 interdit le « camping pratiqué isolément », **sauf dérogation** — et vise le camping, pas le bivouac. Ne pas lire comme une interdiction de bivouaquer (voir plus bas) |
| Conservatoire du littoral (814) | **interdit** | Aucun texte national ne l'interdit nommément : l'interdiction devient verbalisable via un **arrêté municipal ou préfectoral** (L322-10-2, **135 €**, 4e classe) |
| RNN / RNR / RNC (388) | interdit sauf exception | Un décret ou une délibération par site. Bivouac : **3e classe, 68 €** (R332-70, qui vise expressément le bivouac) — pas les 9 000 € de L332-25, qui suppose une atteinte notable |
| Réserve biologique ONF (285) | interdit sauf exception | RBI quasi systématiquement fermée ; RBD variable. 4e classe, 750 € (C. for. R261-1) |
| APPB (1103) | **à vérifier** | Un arrêté préfectoral par site, opposable. Souvent saisonnier (nidification). Jusqu'à 750 € |
| PNR (59) | droit commun | **Un PNR n'a pas de pouvoir de police** — sa charte n'est pas opposable aux visiteurs |
| Natura 2000 ZPS + SIC (1762) | droit commun | Outil de gestion contractuelle, **n'interdit rien** en soi |

Piège principal : Natura 2000 et PNR couvrent d'énormes surfaces **sans rien interdire**. Les afficher comme
contraignants ferait croire à des interdictions inexistantes. La sévérité réelle vient des réserves et des APPB.

### Le cas des sites classés

Un site classé n'interdit pas de bivouaquer. Le texte applicable (C. urb. R111-33 2°) dit :

> Le camping pratiqué isolément ainsi que la création de terrains de camping sont interdits […] dans les sites
> classés ou en instance de classement […], **sauf dérogation** accordée par les autorités compétentes.

Deux limites : la dérogation est prévue par le texte lui-même, et la notion visée est le **camping**, pas le
bivouac. Une tente montée le soir et démontée au matin relève du bivouac ; installée à demeure, elle devient du
camping. Beaucoup de hauts lieux de la randonnée sont classés — cirque de Gavarnie, gorges du Verdon, massif du
Mont-Blanc — et le bivouac y est pratiqué et toléré. Le classement protège contre l'altération du site, il ne
crée pas d'interdiction de dormir dehors.

D'où le statut `verifier_arrete` et non `interdit`. Le risque réel vient du **cumul** (un site classé recouvre
souvent une réserve ou un cœur de parc, qui eux réglementent) et des arrêtés municipaux sur les sites fréquentés.

Les ~4500 **sites inscrits** relèvent d'un régime distinct (R111-33 1°, sans dérogation prévue) et ne sont
**pas** dans ce jeu de données — la couche `patrinat_sc` ne contient que les ~2700 sites classés.

### Sites vérifiés un par un

`rules/reserves.json` surcharge la règle générique du type, trop restrictive pour beaucoup de sites.

| Site | Régime réel |
|---|---|
| **Hauts de Chartreuse** | Bivouac **autorisé** coucher→lever, 1 nuit. Hors juillet-août : tente légère admise. **1er juil – 31 août : tente interdite** (arrêté préfectoral du 16/07/2024, 9 communes), belle étoile toujours permise |
| **Néouvielle** | Uniquement aux aires d'Orédon et d'Aubert, 19h–9h. Régime permanent depuis l'**AP n°65-2025-07-04-00005** du 04/07/2025 |
| **Hauts Plateaux du Vercors** | **17h–9h**, 1 nuit, « si possible aux abords des 7 cabanes-abris ». Campement (tente laissée montée en journée) interdit. Feu interdit en extérieur toute l'année — AP interpréfectoral du 28/12/2016 |
| **Gorges de l'Ardèche** | Interdit sauf **2 aires nommées par le décret** — Gaud et Gournier, 500 personnes chacune, **1 nuit**, titre d'accès obligatoire sous peine d'expulsion. 9,50 à 16,50 €/personne |
| **Ristolas - Mont-Viso** | 18h–9h toute l'année, 1 nuit/site, à **moins de 20 m** des sentiers balisés (confinement, pas éloignement), >500 m du refuge du Viso |
| **Grande Sassière** | 1er juin – 31 août, 19h–7h, **un seul replat** en rive gauche du barrage. L'arrêté de 1973 exempte la tente sans station debout de l'interdiction de campement |
| **Ballons Comtois** | **Interdit** hors du refuge de la Grande Goutte — aucune exemption pour la tente basse (art. 24 du décret) |
| **Py**, **Mantet**, **Nohèdes**, **Prats-de-Mollo** | Campement interdit, bivouac **autorisé par le décret** autour des refuges et le long du GR 10 (ou des sentiers balisés). **Aucun horaire réglementaire** |
| **Sixt-Fer-à-Cheval / Passy** | 19h–9h, placement libre, **réservation gratuite mais obligatoire** de juin à septembre. Aucun arrêté préfectoral n'existe : le cadre est celui du gestionnaire |
| **Haute Chaîne du Jura** | 19h–9h, 1 nuitée/site, ≤20 m des sentiers. **Tout abri interdit, tarp compris** — le plus strict du corpus (AP du 16/10/2017) |
| **Aiguilles Rouges**, **Carlaveyron**, **Vallon de Bérard** | AP **DDT-2026-0472** du 04/06/2026 — réservation gratuite mais **obligatoire**, jauges par secteur (Cheserys 30 tentes, Brévent 25, Arlevé 15, lac Cornu 15) |
| **Contamines-Montjoie** | AP **DDT-2026-0474** du 04/06/2026 — 2 aires (Pont de la Rollaz 40 tentes, La Balme 50). **Aucune réservation dans le texte**, contrairement à ce qu'affirment plusieurs sources |

57 sites — 28 RNN, 7 RNC, 9 RNR, 5 APPB, 4 réserves biologiques, 4 sites classés — dont 44 en fiabilité haute
(texte réglementaire lu). L'absence d'un site ici ne confirme pas l'interdiction, elle signale qu'il n'a pas
été vérifié.

## Zonages internes aux parcs

La réglementation *à l'intérieur* d'un cœur de parc, absente des couches nationales.
36 objets géoréférencés, `type` = `zone_interne` ou `aire_bivouac`.

| Source | Contenu | Précision géo |
|---|---|---|
| **Cévennes** (11 polygones) | Tronçons de GR/GRP où le bivouac est interdit — l'exception à la tolérance le long des sentiers (art. 2 de l'arrêté) | Polygones officiels (Geotrek, ODbL) |
| **Vanoise** (25 points) | 23 refuges avec aire de bivouac + 2 explicitement sans (Col de la Vanoise, Péclet-Polset) | Position du refuge via OSM, **pas le contour de l'aire** |

Nuance des Cévennes que le corpus texte masquait : le parc formule la règle comme
une **interdiction générale avec exception le long des GR/GRP**, pas comme une
autorisation restreinte. Même résultat pratique, base juridique inverse.

5 des refuges Vanoise sont **hors cœur** (Orgère, Plaisance, Rosuel, Vallonbrun,
Entre le Lac) : le champ `en_coeur` les distingue, la réglementation « cœur » ne
s'y applique pas.

D'autres secteurs sont documentés **en texte seulement**, faute de géométrie
publiée : ils vivent dans le champ `secteurs_documentes` des fiches de parc
(Écrins 7, Réunion 5, Mercantour 2, Pyrénées 2, Forêts 2, Calanques 1).
Commune et vallon sont donnés, pas de coordonnées — les inventer serait pire
que l'absence.

## Ce que null veut dire

Une règle de bivouac se lit autant par ses trous que par ses valeurs. Un champ à
`null` veut dire « aucun acte ne le fixe », et le `detail` adjacent dit pourquoi.
Deux pièges qui ont produit des `null` délibérés :

- **Les horaires recopiés.** Le « 19h–9h » omniprésent est le régime des **parcs
  nationaux**. Il est recopié à tort sur des réserves qui n'ont aucun horaire
  réglementaire — démontré pour Mantet, dont la source parle de « limites du
  parc ». Là où aucun acte ne fixe d'horaire, `horaires.debut`/`fin` sont `null`.
- **Les valeurs par défaut plausibles.** `duree.nuits_max` à `null` plutôt qu'à
  `1` quand aucune source ne le dit. Un `1` inventé est indistinguable d'un `1`
  lu dans un décret.

Corollaire : ne jamais reprendre un montant d'amende ou un horaire trouvé sur un
blog ou un site de randonnée sans le vérifier sur Légifrance ou chez le
gestionnaire. Le dépôt a porté « 1 500 € (L332-25) » dans 6 endroits avant
vérification : la bonne référence est R332-70 (3e classe, 68 €), et L332-25 est
en réalité 9 000 € avec un seuil d'« atteinte non négligeable ».

## Retrouver un acte

- **AIDA/INERIS** (`aida.ineris.fr`) plutôt que Légifrance pour les décrets de
  création : souvent le texte intégral en HTML là où Légifrance ne rend que
  l'en-tête. Chercher par nom ou par référence NOR (champ `acte` de la couche).
- **Les arrêtés préfectoraux et municipaux sont presque tous des PDF scannés**
  (images, sans couche texte). `pdftotext -layout` ou `pdftoppm` en PNG puis
  lecture image.
- **Les fiches INPN sont rendues en JavaScript** : vides côté serveur, et l'API
  renvoie 401. Le champ `fiche_inpn` reste utile pour un humain, pas pour un
  script.
- **Les gestionnaires publient parfois mieux que l'État** : tableau synoptique en
  annexe du plan de gestion, page « réglementation », recueil des actes de
  l'établissement. Certains dispositifs ont même une API (les réserves de
  Haute-Savoie servent zonage, jauges et règlement en JSON).

## Limites

- **Arrêtés préfectoraux incendie** — souvent le facteur le plus contraignant en été (fermeture totale de massifs), non géoréférencés nationalement, à consulter par préfecture.
- **Arrêtés municipaux** — ~35 000 communes peuvent interdire le camping (C. urb. R111-34). Aucune base nationale : exhaustivité impossible. 6 arrêtés sont documentés en texte dans `par-type.json` (Chichilianne, 5 communes du Queyras).
- **APPB** — les 1103 arrêtés ne sont pas consolidés nationalement ; `acte` et `fiche_inpn` donnent la piste, la lecture reste manuelle. Une typologie par familles (falaise/rapaces, zones humides, galliformes, grottes, frayères) est dans `par-type.json`.
- **Zonages internes non vectorisés** — voir ci-dessus. Ces parcs ne publient pas ces zonages en vecteur (Écrins en Geotrek v1 sans API v2, Cartothèque Cévennes avec WFS désactivé). Digitalisation manuelle requise.
- **Régimes volatils** — Piton de la Fournaise (arrêtés ORSEC révisés à chaque phase éruptive), sentiers fermés de La Réunion, accès aux massifs des Bouches-du-Rhône (recalculé *quotidiennement* du 1er juin au 30 septembre). Ne pas encoder un état : pointer vers l'acte en cours.
- Règles vérifiées le **2026-08-20**. Les arrêtés de directeur changent d'une saison à l'autre : deux ont été trouvés abrogés pendant cette vérification (Vanoise 2015, Écrins 192/2013).
- L'INPN (`inpn.mnhn.fr`) était inaccessible (cyberattaque MNHN) — les données passent par la Géoplateforme IGN, qui sert les mêmes couches PatriNat.

## Tests

Pas de framework, deux scripts autonomes :

```sh
./build.py --demo     # la jointure : statuts, champs atomiques, cas Chartreuse
./test_regles.py      # les fiches : énums, sources, cohérence des id_mnhn
```

`test_regles.py` vérifie ce que le schéma ne peut pas exprimer seul — qu'une
fiche a au moins une source, que son `type` correspond à une couche réelle, et
qu'aucune sanction ne réintroduit l'erreur L332-25. Les contrôles qui ont besoin
de `data/` sont sautés si les couches ne sont pas téléchargées, pour que la CI
tourne sans les 300 Mo.

## Sources

Attribution, licences et texte à afficher : **[../SOURCES.md](../SOURCES.md)**.
