#!/usr/bin/env python3
"""Attache les règles de bivouac aux géométries et produit un GeoJSON unifié.

  ./fetch.sh && ./build.py    -> out/bivouac.geojson
  ./build.py --pmtiles        -> out/bivouac.pmtiles (nécessite GDAL >= 3.8)

ponytail: un seul fichier de sortie, pas de couche par type. Le champ `type`
suffit à styler côté carte, et un seul PMTiles = une seule requête.
"""
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).parent
DATA, OUT = ROOT / "data", ROOT / "out"

# couche -> clé dans rules/par-type.json. L'ordre définit la priorité d'affichage
# (le plus contraignant en dernier = dessiné au-dessus).
LAYERS = [
    "n2000_sic", "n2000_zps", "pnr", "cdl", "site_classe",
    "apb", "rb", "rnr", "rnc", "rnn", "pn",
]

# statut -> sévérité, pour trier/styler et pour résoudre les superpositions.
SEVERITE = {
    "renvoi_droit_commun": 0,
    "autorise_sous_conditions": 1,
    "restreint_zones": 2,
    "regime_specifique": 2,
    "verifier_arrete": 3,
    "interdit_sauf_exception": 4,
    "interdit": 5,
}


def load(name):
    return json.loads((ROOT / "rules" / name).read_text(encoding="utf-8"))


def props_pn(feat, regles_pn, meta_pn):
    """Parc national : règle propre au site via id_mnhn, sinon règle d'AOA."""
    p = feat["properties"]
    r = regles_pn.get(p.get("id_mnhn"))
    if r:
        return r, r["statut"]
    # aire d'adhésion : pas de réglementation « cœur »
    return {
        "parc": p.get("nom_site", ""),
        "zone": "Aire d'adhésion",
        "statut": "renvoi_droit_commun",
        "resume": meta_pn["regle_aire_adhesion"],
        "cout": {"payant": False, "reservation_obligatoire": False},
    }, "renvoi_droit_commun"


def main():
    regles_pn = load("parcs-nationaux.json")
    meta_pn = regles_pn.pop("_meta")
    par_type = load("par-type.json")
    par_type.pop("_meta")

    OUT.mkdir(exist_ok=True)
    features, stats = [], {}

    for layer in LAYERS:
        src = DATA / f"{layer}.geojson"
        if not src.exists():
            print(f"  ! {layer}.geojson absent — lancer ./fetch.sh", file=sys.stderr)
            continue

        fc = json.loads(src.read_text(encoding="utf-8"))
        base = par_type.get(layer, {})
        statut = base.get("statut", "verifier_arrete")

        for feat in fc.get("features", []):
            src_props = feat["properties"]
            if layer == "pn":
                regle, statut = props_pn(feat, regles_pn, meta_pn)
                libelle = "Parc national"
            else:
                regle, statut = base, base.get("statut", "verifier_arrete")
                libelle = base.get("libelle", layer)

            feat["properties"] = {
                "type": layer,
                "libelle": libelle,
                "nom": src_props.get("nom_site", ""),
                "id_mnhn": src_props.get("id_mnhn", ""),
                "zone": src_props.get("zone") or regle.get("zone", ""),
                "statut": statut,
                "severite": SEVERITE.get(statut, 3),
                "resume": regle.get("resume", ""),
                "acte": src_props.get("acte_deb", ""),
                "fiche_inpn": src_props.get("url_fiche", ""),
                # règle complète sérialisée : les tuiles vectorielles n'acceptent
                # pas d'attributs imbriqués.
                "regle_json": json.dumps(regle, ensure_ascii=False, separators=(",", ":")),
            }
            features.append(feat)

        stats[layer] = len(fc.get("features", []))
        print(f"  {layer:<12} {stats[layer]:>5} objets  [{statut}]")

    # Zonages internes aux parcs (tronçons interdits, aires de bivouac).
    # Ajoutés en dernier : les plus précis, donc dessinés au-dessus.
    zi = DATA / "zones_internes.geojson"
    if zi.exists():
        internes = json.loads(zi.read_text(encoding="utf-8"))["features"]
        for feat in internes:
            p = feat["properties"]
            p.setdefault("libelle", "Zonage interne au parc")
            p["regle_json"] = json.dumps(p.copy(), ensure_ascii=False,
                                         separators=(",", ":"))
        features += internes
        print(f"  {'zones_internes':<12} {len(internes):>5} objets  [zonage interne]")
    else:
        print("  ! zones_internes.geojson absent — lancer ./zones_internes.py",
              file=sys.stderr)

    dest = OUT / "bivouac.geojson"
    dest.write_text(
        json.dumps({"type": "FeatureCollection", "features": features},
                   ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"\n{len(features)} objets -> {dest} ({dest.stat().st_size / 1e6:.0f} Mo)")

    if "--pmtiles" in sys.argv:
        tiles = OUT / "bivouac.pmtiles"
        # ponytail: zoom 5-12 suffit pour du zonage; au-delà on lit la géométrie
        # source. Monter MAXZOOM si tu veux du calage fin sur sentier.
        subprocess.run(
            ["ogr2ogr", "-f", "PMTiles", str(tiles), str(dest),
             "-dsco", "MINZOOM=5", "-dsco", "MAXZOOM=12", "-nln", "bivouac"],
            check=True,
        )
        print(f"tuiles -> {tiles} ({tiles.stat().st_size / 1e6:.0f} Mo)")


def demo():
    """Vérifie la logique de jointure sans toucher aux gros fichiers."""
    regles = load("parcs-nationaux.json")
    meta = regles.pop("_meta")

    coeur = {"properties": {"id_mnhn": "FR3300010", "nom_site": "Calanques"}}
    r, s = props_pn(coeur, regles, meta)
    assert s == "interdit", s
    assert r["tente"]["autorisee"] is False
    assert SEVERITE[s] == 5

    aoa = {"properties": {"id_mnhn": "FR3400010", "nom_site": "Calanques [Aire D'Adhésion]"}}
    r, s = props_pn(aoa, regles, meta)
    assert s == "renvoi_droit_commun", s
    assert "droit commun" in r["resume"]

    # Vanoise : seul parc payant, doit être détectable comme tel
    r, _ = props_pn({"properties": {"id_mnhn": "FR3300001"}}, regles, meta)
    assert r["cout"]["payant"] is True and r["cout"]["montant_eur"] == 5
    assert r["localisation"]["refuge_obligatoire"] is True

    # tous les cœurs ont les champs atomiques attendus
    for pid, p in regles.items():
        for champ in ("statut", "tente", "horaires", "localisation", "duree", "cout", "feu"):
            assert champ in p, f"{pid} ({p['parc']}) : champ '{champ}' manquant"
        assert p["statut"] in SEVERITE, f"{pid} : statut inconnu {p['statut']}"

    par_type = load("par-type.json")
    par_type.pop("_meta")
    for k, v in par_type.items():
        if k.startswith("_"):
            continue
        assert v["statut"] in SEVERITE, f"{k} : statut inconnu {v['statut']}"

    print(f"demo OK — {len(regles)} cœurs de parc, {len(par_type) - 1} types de zonage")


if __name__ == "__main__":
    demo() if "--demo" in sys.argv else main()
