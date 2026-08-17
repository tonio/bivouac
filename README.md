# Règles de bivouac en France par territoire

Géométries des zonages de protection + règles de bivouac associées, jointes par identifiant.

```sh
./fetch.sh              # 11 couches nationales -> data/*.geojson (~300 Mo, ~2 min)
./fetch_osm.sh          # refuges Vanoise depuis OSM
./zones_internes.py     # zonages internes aux parcs -> data/zones_internes.geojson
./build.py --pmtiles    # jointure -> out/bivouac.{geojson,pmtiles}
./build.py --demo       # self-check de la jointure
```

Attribution et licences : **[SOURCES.md](SOURCES.md)** — à lire avant publication,
le jeu final est à traiter comme de l'ODbL.

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

## Les 11 parcs nationaux, cœur de parc

| Parc | Bivouac | Horaires | Tente | Où | Coût |
|---|---|---|---|---|---|
| **Écrins** | oui | 19h–9h | pas de station debout | >1h de marche, **ou** près de 3 refuges nommés | gratuit |
| **Mercantour** | oui | 19h–9h | non autoportante | >1h de marche ; Merveilles/Fontanalba : 2 aires | gratuit |
| **Pyrénées** | oui | 19h–9h | petite tente | >1h de marche ; Néouvielle : aires Orédon/Aubert | gratuit |
| **Vanoise** | restreint | **19h–8h** | pas de station debout | **aires de refuges gardés uniquement** | **5 €/emplacement, résa obligatoire** |
| **Cévennes** | restreint | 19h–9h | légère **ou sans tente** | **≤50 m d'un GR/GRP**, hors 10 tronçons interdits | gratuit |
| **Forêts** | oui | **coucher −1h → lever +1h** | petite tente | à proximité des voies et sentiers | gratuit |
| **Réunion** | restreint | coucher → matinée | **hamac admis** | libre sauf 5 zones interdites | gratuit |
| **Guadeloupe** | oui | tombée nuit → lever jour | pas de station debout | >1h de marche | gratuit |
| **Guyane** | régime spécifique | — | hamac | autorisation requise selon zone | selon zone |
| **Calanques** | **interdit** | — | interdite | — | — |
| **Port-Cros** | **interdit** | — | interdite | — | — |

Partout : **1 nuit**, feu au sol interdit, réchaud portatif toléré (sauf Calanques, où le réchaud gaz est aussi interdit).
Sanction usuelle 68 €/personne (contravention de 3e classe, C. env. art. R331-64).

**Aire d'adhésion** (`FR34000xx`) : aucune réglementation « cœur », retour au droit commun.

## Autres zonages

| Type | Statut | Pourquoi |
|---|---|---|
| Site classé (2657) | **à vérifier** | R111-33 interdit le « camping pratiqué isolément », **sauf dérogation** — et vise le camping, pas le bivouac. Ne pas lire comme une interdiction de bivouaquer (voir plus bas) |
| Conservatoire du littoral (814) | **interdit** | C. env. L322-1 + interdiction de camper sur les rivages |
| RNN / RNR / RNC (388) | interdit sauf exception | Un décret ou une délibération par site. **Jusqu'à 1 500 €** (L332-25). 3 réserves vérifiées individuellement dans `rules/reserves.json` |
| Réserve biologique ONF (285) | interdit sauf exception | RBI quasi systématiquement fermée ; RBD variable |
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

### Réserves vérifiées site par site

`rules/reserves.json` surcharge la règle générique du type, trop restrictive pour plusieurs réserves.

| Réserve | Régime réel |
|---|---|
| **Hauts de Chartreuse** | Bivouac **autorisé** coucher→lever, 1 nuit. Hors juillet-août : tente légère admise. **1er juil – 31 août : tente interdite** (arrêté préfectoral du 16/07/2024, 9 communes), belle étoile toujours permise |
| **Néouvielle** | Uniquement aux aires d'Orédon et d'Aubert, 19h–9h, gratuit sans réservation |
| **Hauts Plateaux du Vercors** | Arrêté interpréfectoral, conditions à vérifier |

3 réserves sur 388 : l'absence d'une réserve ici ne confirme pas l'interdiction, elle signale qu'elle n'a pas
été vérifiée.

## Zonages internes aux parcs

La réglementation *à l'intérieur* d'un cœur de parc, absente des couches nationales.
36 objets, `type` = `zone_interne` ou `aire_bivouac`.

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

## Limites

- **Arrêtés préfectoraux incendie** — souvent le facteur le plus contraignant en été (fermeture totale de massifs), non géoréférencés nationalement, à consulter par préfecture.
- **Arrêtés municipaux** — ~35 000 communes peuvent interdire le camping (C. urb. R111-34). Aucune base nationale : exhaustivité impossible.
- **APPB** — les 1103 arrêtés ne sont pas consolidés nationalement ; `acte` et `fiche_inpn` donnent la piste, la lecture reste manuelle.
- **Zonages internes des autres parcs** — Écrins (abords Muzelle/Lauvitel), Mercantour (Merveilles/Fontanalba), Pyrénées (aires Orédon/Aubert), Réunion (5 zones fermées) restent **décrits en texte**. Vérifié : ces parcs ne publient pas ces zonages en vecteur (Écrins en Geotrek v1 sans API v2, Cartothèque Cévennes avec WFS désactivé — seul le dépôt GitHub du parc expose les données). Digitalisation manuelle requise si tu les veux.
- Règles vérifiées le **2026-08-17**. Les arrêtés de directeur changent d'une saison à l'autre.
- L'INPN (`inpn.mnhn.fr`) était inaccessible (cyberattaque MNHN) — les données passent par la Géoplateforme IGN, qui sert les mêmes couches PatriNat.

## Sources

Détail complet, licences et texte d'attribution à afficher : **[SOURCES.md](SOURCES.md)**.

Géométries : [Géoplateforme IGN](https://data.geopf.fr/wfs/ows), couches `patrinat_*` (PatriNat/OFB/MNHN), Licence Ouverte 2.0 · [data.gouv.fr](https://www.data.gouv.fr/datasets/contours-des-11-parcs-nationaux-de-france) · zonages internes : [Parc national des Cévennes](https://github.com/PnCevennes/data_reglementation) (ODbL) et [OpenStreetMap](https://www.openstreetmap.org/copyright) (ODbL)

Arrêtés en texte intégral : [AIDA/INERIS](https://aida.ineris.fr/) — [Écrins n°192/2013](https://www.ecrins-parcnational.fr/sites/ecrins-parcnational.com/files/fiche_doc/9678/14-06-192ardir-reglementationbivouac.pdf) · [Cévennes n°20140007](https://aida.ineris.fr/reglementation/arrete-ndeg-20140007-200114-reglementant-bivouac-coeur-parc-national-cevennes) · [Mercantour n°2018-07](https://aida.ineris.fr/reglementation/arrete-ndeg-2018-07-010618-reglementant-pratique-bivouac-coeur-parc-national) · [Vanoise 09/07/2015](https://aida.ineris.fr/reglementation/arrete-090715-concernant-bivouac-coeur-parc-national-vanoise)

Sites officiels : [portail des parcs nationaux](https://www.parcsnationaux.fr/fr/des-decouvertes/visiter-et-semerveiller/la-reglementation-et-les-conseils/le-bivouac) · [Vanoise](https://www.vanoise-parcnational.fr/fr/des-decouvertes/sejourner-dans-le-parc/lart-du-bivouac-responsable-en-vanoise) · [Pyrénées](https://www.pyrenees-parcnational.fr/fr/des-decouvertes/sejourner-dans-le-parc-national/ou-dormir-en-montagne/bivouac) · [Cévennes](https://www.cevennes-parcnational.fr/fr/le-parc-national-des-cevennes/la-reglementation-du-coeur/les-regles-pour-tous) · [Réunion](https://www.reunion-parcnational.fr/fr/le-parc-national-de-la-reunion/reglementation/bivouac-en-coeur-de-parc-national) · [Forêts](https://www.forets-parcnational.fr/fr/parc-national-de-forets/la-reglementation-du-coeur) · [Calanques](https://www.calanques-parcnational.fr/fr/actualites/camping-sauvage-et-bivouac-rappel-des-reglementations-et-des-bons-gestes)

> Données d'aide à la préparation, sans valeur juridique. Vérifier auprès du gestionnaire avant de partir.
