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

# ponytail: z5-12 suffit pour du zonage; au-delà on lit la géométrie source.
MINZOOM, MAXZOOM = 5, 12

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
    # Réserves vérifiées une par une : surchargent la règle générique du type,
    # qui est trop restrictive pour plusieurs d'entre elles.
    reserves = load("reserves.json")
    reserves.pop("_meta")

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
                # Une réserve documentée l'emporte sur la règle du type.
                propre = reserves.get(src_props.get("id_mnhn"))
                if propre and layer in ("rnn", "rnr", "rnc"):
                    regle, statut = propre, propre["statut"]

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

    if not features:
        sys.exit("Aucune donnée : lancer ./fetch.sh, ./fetch_osm.sh puis "
                 "./zones_internes.py avant ./build.py")

    dest = OUT / "bivouac.geojson"
    dest.write_text(
        json.dumps({"type": "FeatureCollection", "features": features},
                   ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"\n{len(features)} objets -> {dest} ({dest.stat().st_size / 1e6:.0f} Mo)")

    if "--pmtiles" in sys.argv:
        pmtiles(features)


def pmtiles(features):
    """Deux couches MVT : les zones (polygones) et les points.

    Une couche de tuiles vectorielles ne porte qu'un type de géométrie — tout
    mélanger fait disparaître silencieusement les 25 points de refuge.
    """
    tiles = OUT / "bivouac.pmtiles"
    pts = [f for f in features if f["geometry"]["type"] == "Point"]
    zones = [f for f in features if f["geometry"]["type"] != "Point"]

    parts = {}
    for nom, feats in (("zones", zones), ("points", pts)):
        src = OUT / f"_{nom}.geojson"
        src.write_text(
            json.dumps({"type": "FeatureCollection", "features": feats},
                       ensure_ascii=False),
            encoding="utf-8",
        )
        parts[nom] = src

    # Le driver PMTiles n'accepte pas -update/-append : les deux couches
    # doivent être écrites dans la même ouverture du dataset.
    from osgeo import gdal

    gdal.UseExceptions()
    tiles.unlink(missing_ok=True)
    # Les zooms doivent être fixés à la création du dataset : passés seulement
    # en options de couche, le tileset reste borné à z5.
    dst = gdal.GetDriverByName("PMTiles").Create(
        str(tiles), 0, 0, 0, gdal.GDT_Unknown,
        ["NAME=bivouac", f"MINZOOM={MINZOOM}", f"MAXZOOM={MAXZOOM}"])
    for nom, src in parts.items():
        gdal.VectorTranslate(
            dst, str(src),
            options=gdal.VectorTranslateOptions(
                layerName=nom,
                layerCreationOptions=[f"MINZOOM={MINZOOM}", f"MAXZOOM={MAXZOOM}"],
            ),
        )
    dst = None
    for src in parts.values():
        src.unlink()

    got = subprocess.run(["ogrinfo", "-q", str(tiles)],
                         capture_output=True, text=True).stdout
    for nom in ("zones", "points"):
        assert nom in got, f"couche '{nom}' absente des tuiles :\n{got}"

    # Le tileset est resté borné à z5 quand les zooms n'étaient passés qu'en
    # options de couche : on vérifie plutôt que de faire confiance.
    ds = gdal.OpenEx(str(tiles), open_options=[f"ZOOM_LEVEL={MAXZOOM}"])
    assert ds is not None, f"tuiles illisibles au zoom {MAXZOOM}"
    ds = None
    print(f"tuiles -> {tiles} ({tiles.stat().st_size / 1e6:.0f} Mo) "
          f"— couches: zones + points ({len(pts)} refuges)")


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

    # Le site classé ne doit pas être présenté comme une interdiction de
    # bivouaquer : R111-33 vise le camping, et prévoit une dérogation.
    sc = par_type["site_classe"]
    assert sc["statut"] == "verifier_arrete", sc["statut"]
    assert sc["tente"]["autorisee"] is None

    reserves = load("reserves.json")
    reserves.pop("_meta")
    for rid, r in reserves.items():
        assert r["statut"] in SEVERITE, f"{rid} : statut inconnu {r['statut']}"
        for champ in ("tente", "horaires", "localisation", "duree", "cout", "feu"):
            assert champ in r, f"{rid} ({r['reserve']}) : champ '{champ}' manquant"

    # Chartreuse : la règle générique « interdit sauf exception » est fausse ici,
    # le bivouac y est autorisé — avec interdiction de la tente en juillet-août.
    ch = reserves["FR3600136"]
    assert ch["statut"] == "restreint_zones", ch["statut"]
    assert ch["tente"]["autorisee"] is True
    assert "1er juillet" in ch["restriction_saisonniere"]["periode"]

    print(f"demo OK — {len(regles)} cœurs de parc, {len(par_type) - 1} types de zonage, "
          f"{len(reserves)} réserves détaillées")


if __name__ == "__main__":
    demo() if "--demo" in sys.argv else main()
