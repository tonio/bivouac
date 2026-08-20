# Sources, licences et attribution

À lire avant publication. Deux régimes de licence se mélangent ici, et l'ODbL
impose des obligations concrètes, pas seulement une mention.

Chaque objet de `pipeline/out/bivouac.geojson` porte ses propres champs `source_nom`,
`source_url` et `source_licence` quand la source est spécifique (zones internes).
Pour les couches nationales, l'attribution est celle du tableau ci-dessous.

## Mention à afficher

Bloc minimal à placer dans le pied de page ou un panneau « Sources » accessible
depuis toutes les pages de carte :

```html
<p>
  Zonages de protection :
  <a href="https://data.geopf.fr/">Géoplateforme IGN</a> —
  données PatriNat (OFB / MNHN / CNRS), Licence Ouverte 2.0.
  Réglementation du cœur du Parc national des Cévennes :
  <a href="https://www.data.gouv.fr/datasets/reglementation-des-pratiques-de-la-randonnee-du-vtt-et-du-canyoning-dans-le-coeur-du-parc-national-des-cevennes/">Parc national des Cévennes</a>, ODbL.
  Position des refuges : © les contributeurs
  <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>, ODbL.
  Règles de bivouac compilées depuis les arrêtés des parcs nationaux
  (voir <a href="/sources">sources détaillées</a>).
  Données d'aide à la préparation, sans valeur juridique.
</p>
```

## Tableau des sources

| Données | Producteur | Licence | Attribution requise | URL |
|---|---|---|---|---|
| Parcs nationaux, PNR, Natura 2000, RNN/RNR/RNC, APPB, réserves biologiques, sites classés, Conservatoire du littoral | PatriNat (OFB / MNHN / CNRS), diffusé par IGN | **Licence Ouverte 2.0 (Etalab)** | Paternité : nommer le producteur et la date de mise à jour | [data.geopf.fr](https://data.geopf.fr/wfs/ows) |
| Tronçons de GR/GRP interdits au bivouac (Cévennes) | Parc national des Cévennes (export Geotrek) | **ODbL** | Paternité + partage à l'identique + maintien ouvert | [data.gouv.fr](https://www.data.gouv.fr/datasets/reglementation-des-pratiques-de-la-randonnee-du-vtt-et-du-canyoning-dans-le-coeur-du-parc-national-des-cevennes/) · [dépôt GitHub](https://github.com/PnCevennes/data_reglementation) |
| Position des refuges (Vanoise) | Contributeurs OpenStreetMap | **ODbL** | « © les contributeurs OpenStreetMap » + lien vers la licence | [openstreetmap.org/copyright](https://www.openstreetmap.org/copyright) |
| Contours des 11 parcs nationaux (source alternative) | Parcs nationaux de France | Licence Ouverte | Paternité | [data.gouv.fr](https://www.data.gouv.fr/datasets/contours-des-11-parcs-nationaux-de-france) |
| Textes des arrêtés | Parcs nationaux / AIDA-INERIS | Textes officiels, reproduction libre | Citer la référence de l'arrêté | voir ci-dessous |

### Ce que l'ODbL implique concrètement

Les données Cévennes et OSM sont en ODbL. Si tu publies un site :

1. **Attribution** — mention visible, avec lien vers la licence.
2. **Partage à l'identique** — si tu publies une *base dérivée* (ton
   `bivouac.geojson`, tes PMTiles en téléchargement), elle doit être offerte
   sous ODbL. Une carte qui affiche les données ne déclenche pas cette
   obligation ; proposer le fichier en téléchargement, oui.
3. **Pas de verrou technique** — pas de DRM sur les données redistribuées.

La Licence Ouverte n'impose que la paternité, sans réciprocité. Comme le jeu
final mélange les deux, **le plus contraignant gagne** pour l'ensemble
redistribué : traite `pipeline/out/bivouac.geojson` comme de l'ODbL.

## Arrêtés et textes réglementaires

Sources primaires effectivement lues pour construire `pipeline/rules/parcs-nationaux.json` :

| Parc | Acte | Source |
|---|---|---|
| Écrins | Arrêté n° 192/2013 du 04/06/2014 | [PDF du parc](https://www.ecrins-parcnational.fr/sites/ecrins-parcnational.com/files/fiche_doc/9678/14-06-192ardir-reglementationbivouac.pdf) · [AIDA](https://aida.ineris.fr/reglementation/arrete-ndeg-1922013-040614-relatif-bivouac-coeur-parc-national-ecrins) |
| Cévennes | Arrêté n° 20140007 du 20/01/2014 | [AIDA](https://aida.ineris.fr/reglementation/arrete-ndeg-20140007-200114-reglementant-bivouac-coeur-parc-national-cevennes) · [PDF du parc](https://www.cevennes-parcnational.fr/sites/cevennes-parcnational.fr/files/atoms/files/2014_arrete_n_20140007_du_20_janvier_2014_bivouac.pdf) |
| Mercantour | Arrêté n° 2018-07 du 01/06/2018 (abroge 2013-08) | [AIDA](https://aida.ineris.fr/reglementation/arrete-ndeg-2018-07-010618-reglementant-pratique-bivouac-coeur-parc-national) |
| Vanoise | Arrêté du 09/07/2015 | [AIDA](https://aida.ineris.fr/reglementation/arrete-090715-concernant-bivouac-coeur-parc-national-vanoise) |

Fiches officielles utilisées pour les parcs sans arrêté consolidé en ligne :
[portail des parcs nationaux](https://www.parcsnationaux.fr/fr/des-decouvertes/visiter-et-semerveiller/la-reglementation-et-les-conseils/le-bivouac) ·
[Vanoise](https://www.vanoise-parcnational.fr/fr/des-decouvertes/sejourner-dans-le-parc/lart-du-bivouac-responsable-en-vanoise) ·
[Pyrénées](https://www.pyrenees-parcnational.fr/fr/des-decouvertes/sejourner-dans-le-parc-national/ou-dormir-en-montagne/bivouac) ·
[Cévennes](https://www.cevennes-parcnational.fr/fr/le-parc-national-des-cevennes/la-reglementation-du-coeur/les-regles-pour-tous) ·
[Réunion](https://www.reunion-parcnational.fr/fr/le-parc-national-de-la-reunion/reglementation/bivouac-en-coeur-de-parc-national) ·
[Forêts](https://www.forets-parcnational.fr/fr/parc-national-de-forets/la-reglementation-du-coeur) ·
[Calanques](https://www.calanques-parcnational.fr/fr/actualites/camping-sauvage-et-bivouac-rappel-des-reglementations-et-des-bons-gestes) ·
[Mercantour](https://www.mercantour-parcnational.fr/fr/le-parc-national-du-mercantour/la-reglementation) ·
[Écrins](https://www.ecrins-parcnational.fr/) ·
[Port-Cros](https://www.portcros-parcnational.fr/) ·
[Guadeloupe](https://www.guadeloupe-parcnational.fr/) ·
[Guyane](https://www.parc-amazonien-guyane.fr/)

Codes cités : [Code de l'environnement](https://www.legifrance.gouv.fr/codes/texte_lc/LEGITEXT000006074220) (L331-1 et s., L332-1 et s., L341-1 et s., L414-1 et s., R331-62 et s.) ·
[Code de l'urbanisme](https://www.legifrance.gouv.fr/codes/texte_lc/LEGITEXT000006074075) (R111-32 à R111-35) ·
[Code forestier](https://www.legifrance.gouv.fr/codes/texte_lc/LEGITEXT000025244092) (L131-1 et s.)

## À faire si tu publies

- [ ] Bloc d'attribution visible sur toute page affichant la carte
- [ ] Page « Sources » reprenant ce fichier
- [ ] Si téléchargement des données : publier sous ODbL et le déclarer
- [ ] Date de dernière vérification affichée (**2026-08-17**) — les arrêtés changent
- [ ] Avertissement « sans valeur juridique, vérifier auprès du gestionnaire »
- [ ] Ne pas laisser croire que Natura 2000 ou un PNR interdit le bivouac (ils
      n'interdisent rien) — voir `pipeline/rules/par-type.json`
- [ ] Mentionner que les arrêtés préfectoraux incendie et municipaux ne sont
      **pas** dans les données, et qu'ils priment

## Polices

Les deux polices sont **auto-hébergées** dans `app/src/polices/` (fichiers woff2
récupérés depuis fonts.gstatic.com), et non chargées depuis Google Fonts : une
dépendance tierce de moins dans le chemin critique, et aucune adresse IP de
visiteur transmise à Google.

| Police | Auteur | Licence |
|---|---|---|
| Instrument Sans | Instrument / Rodrigo Fuenzalida & Jordan Egstad | [SIL OFL 1.1](https://openfontlicense.org/) |
| Instrument Serif | Instrument / Rodrigo Fuenzalida | [SIL OFL 1.1](https://openfontlicense.org/) |

L'OFL autorise la redistribution avec le logiciel, y compris commerciale, à
condition de ne pas vendre les fontes seules et de conserver la licence. Elle
n'impose pas de mention visible dans l'interface.

## Remerciements

Le parc national des Cévennes est le seul à publier sa réglementation en
données ouvertes géoréférencées, dans un dépôt public documenté
([PnCevennes/data_reglementation](https://github.com/PnCevennes/data_reglementation)).
C'est ce qui rend la partie « tronçons interdits » possible. Contact SI du
parc : `admin_si@cevennes-parcnational.fr`.
