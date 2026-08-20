#!/usr/bin/env python3
"""Zonages internes aux parcs : tronçons interdits, aires de bivouac par refuge.

Ce que les couches nationales ne contiennent pas — la réglementation *à
l'intérieur* d'un cœur de parc.

  ./zones_internes.py         -> data/zones_internes.geojson
  ./zones_internes.py --demo  -> self-check

Deux origines, très inégales :
  - Cévennes : 11 polygones officiels (Geotrek/ODbL) déjà géoréférencés.
  - Vanoise  : 23 refuges nommés par le parc, appariés aux points OSM (ODbL).
               Position du refuge, PAS le contour de l'aire de bivouac —
               le parc ne publie que des PDF.

ponytail: appariement par nom normalisé, pas de fuzzy matching. Les non-appariés
sont listés en sortie plutôt que devinés — mieux vaut un trou visible qu'un
point faux.
"""
import json
import pathlib
import re
import sys
import unicodedata

ROOT = pathlib.Path(__file__).parent
DATA = ROOT / "data"

# Liste officielle du parc national de la Vanoise (portail « L'art du bivouac
# responsable en Vanoise », consulté 2026-08-17). 5 € / emplacement, réservation
# obligatoire auprès du gardien, 1er juin - 30 septembre, 19h-8h.
VANOISE_AVEC_BIVOUAC = {
    "Refuge de l'Arpont": "Val-Cenis Termignon",
    "Refuge du Col du Palet": "Peisey",
    "Refuge de la Femma": "Val-Cenis Termignon",
    "Refuge du Fond des Fours": "Val d'Isère",
    "Refuge de la Leisse": "Val-Cenis Termignon",
    "Refuge de la Martin": "Villaroger",
    "Refuge de l'Orgère": "Villarodin-Bourget",
    "Refuge de Plaisance": "Champagny-en-Vanoise",
    "Refuge de Plan du Lac": "Val-Cenis Termignon",
    "Refuge de Prariond": "Val d'Isère",
    "Refuge de Rosuel": "Peisey-Nancroix",
    "Refuge de Turia": "Villaroger",
    "Refuge de la Valette": "Pralognan-la-Vanoise",
    "Refuge de Vallonbrun": "Val Cenis Lanslevillard",
    "Refuge du Carro": "Bonneval-sur-Arc",
    "Refuge du Fond d'Aussois": "Aussois",
    "Refuge du Mont Pourri": "Peisey-Nancroix",
    "Refuge de la Dent Parrachée": "Aussois",
    "Refuge d'Entre le Lac": "Peisey-Nancroix",
    "Refuge d'Entre deux Eaux": "Val-Cenis Termignon",
    "Refuge de la Glière": "Champagny-en-Vanoise",
    "Refuge du Lac Blanc": "Val-Cenis Termignon",
    "Refuge des Lacs Merlets": "Courchevel",
}

# Explicitement SANS aire de bivouac — l'information négative compte autant.
VANOISE_SANS_BIVOUAC = {
    "Refuge du Col de la Vanoise": "Bivouac supprimé : forte fréquentation, capacité d'assainissement",
    "Refuge de Péclet-Polset": "Pas d'aire de bivouac",
}

CEVENNES_SRC = "https://github.com/PnCevennes/data_reglementation"

# Noms officiels du parc qui diffèrent du nom OSM. Alias explicites plutôt que
# fuzzy matching : un rapprochement approximatif placerait un point au mauvais
# refuge sans prévenir.
ALIAS_OSM = {
    "Refuge des Lacs Merlets": "Refuge des lacs Merlet",
}


def norm(s):
    """Normalise un nom de refuge pour l'appariement."""
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()
    s = s.lower().replace("refuge", " ").replace("rifugio", " ")
    s = re.sub(r"\b(de|du|des|le|la|les|l|d)\b", " ", s)
    return re.sub(r"[^a-z0-9]+", "", s)


def strip_html(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s or "")).strip()


# Le titre du tronçon (« GR®70 - Portion du Sommet de Finiels ») précède un
# paragraphe explicatif identique sur tous les objets. On coupe dessus.
_BOILERPLATE = re.compile(r"\s*Le\s+bivouac\s+est\s+interdit\b", re.I)


def titre(desc):
    t = _BOILERPLATE.split(desc, 1)[0].strip(" .-")[:120]
    # Un objet (déviation provisoire du GR®66/71) n'a pas de titre séparé :
    # sa description commence directement par le texte explicatif.
    if len(t) > 90 or not t:
        return "GR®66/71 - Déviation provisoire pont du Lingas – Lac des Pises"
    return t


def cevennes():
    """11 polygones « Bivouac interdit » (Geotrek, ODbL)."""
    src = DATA / "cev_sensitivity_area.geojson"
    if not src.exists():
        print("  ! cev_sensitivity_area.geojson absent", file=sys.stderr)
        return []

    import html as html_mod

    out = []
    for f in json.loads(src.read_text(encoding="utf-8"))["features"]:
        p = f["properties"]
        if "bivouac" not in str(p.get("Rules", "")).lower():
            continue
        desc = html_mod.unescape(strip_html(p.get("Description fr")))
        out.append({
            "type": "Feature",
            "geometry": f["geometry"],
            "properties": {
                "type": "zone_interne",
                "parc": "Cévennes",
                "id_mnhn": "FR3300004",
                "nom": titre(desc) or f"Tronçon {p.get('id')}",
                "statut": "interdit",
                "severite": 5,
                "resume": "Tronçon de GR/GRP où le bivouac est interdit (exception à "
                          "la tolérance le long des sentiers balisés).",
                "massif": p.get("District", ""),
                "communes": p.get("City", ""),
                "periode": "toute l'année",
                "description": desc[:600],
                "acte": "Arrêté n° 20140007 du 20/01/2014, art. 2",
                "source_nom": "Parc national des Cévennes (Geotrek)",
                "source_url": p.get("URL fr") or CEVENNES_SRC,
                "source_licence": "ODbL",
                "precision_geo": "polygone officiel",
            },
        })
    return out


def rings(geom):
    cs = geom["coordinates"]
    polys = cs if geom["type"] == "MultiPolygon" else [cs]
    return [r for poly in polys for r in poly]


def dans_coeur(pt, geom):
    """Ray casting — évite une dépendance shapely pour un seul test."""
    x, y = pt
    dedans = False
    for ring in rings(geom):
        for i in range(len(ring) - 1):
            x1, y1 = ring[i][:2]
            x2, y2 = ring[i + 1][:2]
            if (y1 > y) != (y2 > y) and x < x1 + (y - y1) / (y2 - y1) * (x2 - x1):
                dedans = not dedans
    return dedans


def geom_coeur(id_mnhn):
    src = DATA / "pn.geojson"
    if not src.exists():
        return None
    for f in json.loads(src.read_text(encoding="utf-8"))["features"]:
        if f["properties"].get("id_mnhn") == id_mnhn:
            return f["geometry"]
    return None


def vanoise():
    """23 aires de bivouac de refuge, position issue d'OSM."""
    src = DATA / "osm_refuges_vanoise.json"
    if not src.exists():
        print("  ! osm_refuges_vanoise.json absent — voir fetch_osm.sh", file=sys.stderr)
        return [], list(VANOISE_AVEC_BIVOUAC)

    osm = {}
    for el in json.loads(src.read_text(encoding="utf-8")).get("elements", []):
        nom = el.get("tags", {}).get("name")
        if not nom:
            continue
        pt = el if "lon" in el else el.get("center", {})
        if "lon" in pt:
            osm.setdefault(norm(nom), (pt["lon"], pt["lat"], nom))

    coeur = geom_coeur("FR3300001")
    out, absents = [], []
    for nom, commune in VANOISE_AVEC_BIVOUAC.items():
        hit = osm.get(norm(ALIAS_OSM.get(nom, nom)))
        if not hit:
            absents.append(nom)
            continue
        lon, lat, nom_osm = hit
        # Plusieurs refuges de porte d'entrée sont hors cœur : la réglementation
        # « cœur » (dont l'obligation de bivouaquer près d'un refuge) ne s'y
        # applique pas, même si l'aire de bivouac existe.
        en_coeur = dans_coeur((lon, lat), coeur) if coeur else None
        out.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [lon, lat]},
            "properties": {
                "type": "aire_bivouac",
                "parc": "Vanoise",
                "id_mnhn": "FR3300001",
                "nom": nom,
                "nom_osm": nom_osm,
                "commune": commune,
                "statut": "autorise_sous_conditions",
                "severite": 1,
                "resume": "Aire de bivouac de refuge — seul endroit où le bivouac "
                          "est autorisé dans le cœur de la Vanoise.",
                "horaires": "19:00-08:00",
                "saison": "1er juin – 30 septembre (gardiennage effectif)",
                "payant": True,
                "montant_eur": 5,
                "unite": "emplacement",
                "reservation_obligatoire": True,
                "en_coeur": en_coeur,
                "acte": "Arrêté du 09/07/2015 (cœur du PN de la Vanoise)"
                        if en_coeur else
                        "Refuge hors cœur — la réglementation « cœur » ne s'applique pas ; "
                        "conditions fixées par le refuge",
                "source_nom": "Parc national de la Vanoise (liste) + OpenStreetMap (position)",
                "source_url": "https://www.vanoise-parcnational.fr/fr/des-decouvertes/sejourner-dans-le-parc/lart-du-bivouac-responsable-en-vanoise",
                "source_licence": "ODbL (OpenStreetMap)",
                # ponytail: le point est le refuge, pas l'aire. Suffisant pour
                # localiser; à remplacer si le parc publie les contours.
                "precision_geo": "position du refuge (l'aire est à proximité immédiate)",
            },
        })

    for nom, motif in VANOISE_SANS_BIVOUAC.items():
        hit = osm.get(norm(nom))
        if not hit:
            continue
        lon, lat, _ = hit
        out.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [lon, lat]},
            "properties": {
                "type": "aire_bivouac",
                "parc": "Vanoise",
                "id_mnhn": "FR3300001",
                "nom": nom,
                "statut": "interdit",
                "severite": 5,
                "resume": f"Refuge SANS aire de bivouac. {motif}.",
                "payant": False,
                "source_nom": "Parc national de la Vanoise + OpenStreetMap",
                "source_url": "https://www.vanoise-parcnational.fr/fr/des-decouvertes/sejourner-dans-le-parc/lart-du-bivouac-responsable-en-vanoise",
                "source_licence": "ODbL (OpenStreetMap)",
                "precision_geo": "position du refuge",
            },
        })
    return out, absents


def main():
    feats = cevennes()
    print(f"  Cévennes   {len(feats):>3} tronçons GR interdits (polygones officiels)")

    van, absents = vanoise()
    hors = sum(1 for f in van if f["properties"].get("en_coeur") is False)
    print(f"  Vanoise    {len(van):>3} aires de refuge appariées à OSM "
          f"({hors} hors cœur, régime différent)")
    if absents:
        # ponytail: on liste, on ne devine pas.
        print(f"             {len(absents)} non appariés : {', '.join(absents)}")
    feats += van

    dest = DATA / "zones_internes.geojson"
    dest.write_text(
        json.dumps({"type": "FeatureCollection", "features": feats},
                   ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"\n{len(feats)} objets -> {dest}")


def demo():
    assert norm("Refuge de l'Arpont") == norm("refuge  Arpont")
    assert norm("Refuge du Carro") == norm("Le Carro")
    assert norm("Refuge de Péclet-Polset") == norm("Refuge de Peclet Polset")
    # deux refuges distincts ne doivent pas collapser
    assert norm("Refuge du Lac Blanc") != norm("Refuge des Lacs Merlets")
    assert len(VANOISE_AVEC_BIVOUAC) == 23, len(VANOISE_AVEC_BIVOUAC)
    assert not set(VANOISE_AVEC_BIVOUAC) & set(VANOISE_SANS_BIVOUAC)

    assert titre("GR®70 - Portion du Sommet de Finiels Le bivouac est interdit dans "
                 "le cœur") == "GR®70 - Portion du Sommet de Finiels"
    assert titre("Le tracé actuel du GR®66/71 a été dévié " * 4).startswith("GR®66/71")

    cev = cevennes()
    for f in cev:
        p = f["properties"]
        assert p["statut"] == "interdit" and p["severite"] == 5
        assert p["source_licence"] == "ODbL"
        assert f["geometry"]["type"] in ("Polygon", "MultiPolygon")
        assert "Le bivouac est interdit" not in p["nom"], p["nom"]

    # Sans les données sources il n'y a rien à valider : le dire, plutôt que
    # laisser un check vide passer pour un succès.
    if not cev:
        print("demo PARTIELLE — données Cévennes absentes (lancer ./fetch.sh), "
              f"{len(VANOISE_AVEC_BIVOUAC)} refuges Vanoise vérifiés")
        return
    assert len(cev) == 11, f"attendu 11 tronçons, obtenu {len(cev)}"
    print(f"demo OK — {len(cev)} tronçons Cévennes, {len(VANOISE_AVEC_BIVOUAC)} refuges Vanoise")


if __name__ == "__main__":
    demo() if "--demo" in sys.argv else main()
