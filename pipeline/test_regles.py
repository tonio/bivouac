#!/usr/bin/env python3
"""Valide les fiches de règles — ce que le schéma seul n'exprime pas.

  ./test_regles.py

Complète `./build.py --demo`, qui teste la jointure. Ici on teste la donnée :
énums, sources, cohérence des identifiants, et non-régression des deux erreurs
qui ont traversé le dépôt (sanction L332-25, horaires de parc national recopiés
sur des réserves).

ponytail: pas de framework, des assertions et un compteur. Les contrôles qui ont
besoin de data/ sont sautés si les couches ne sont pas téléchargées, pour que la
CI tourne sans les 300 Mo.
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).parent
RULES, DATA = ROOT / "rules", ROOT / "data"

STATUTS = {"interdit", "interdit_sauf_exception", "verifier_arrete", "restreint_zones",
           "regime_specifique", "autorise_sous_conditions", "renvoi_droit_commun"}
TYPES = {"pn", "pnr", "n2000_sic", "n2000_zps", "rnn", "rnr", "rnc", "apb", "rb",
         "site_classe", "cdl"}
TENTE = {"aucune_restriction", "legere_sans_station_debout", "sans_tente_uniquement", "interdite"}
CONTRAINTE = {"libre", "distance_acces", "proximite_refuge_obligatoire", "couloir_sentier",
              "aires_designees"}
MOTS_HORAIRE = {"coucher_soleil", "coucher_soleil-1h", "lever_soleil+1h", "tombee_nuit",
                "lever_jour", "lever_soleil", "coucher_soleil+1h"}
ATOMIQUES = ("tente", "horaires", "localisation", "duree", "cout", "feu")

echecs = []


def verifie(ok, msg):
    if not ok:
        echecs.append(msg)


def charge(nom):
    return json.loads((RULES / nom).read_text(encoding="utf-8"))


def horaire_valide(h):
    return h is None or h in MOTS_HORAIRE or bool(re.fullmatch(r"\d{2}:\d{2}", h))


def champs_atomiques(cle, r, source):
    """Les invariants communs à toute fiche portant une règle."""
    for champ in ATOMIQUES:
        verifie(champ in r, f"{source} {cle} : champ '{champ}' manquant")
    verifie(r.get("statut") in STATUTS, f"{source} {cle} : statut {r.get('statut')!r}")

    t = r.get("tente") or {}
    verifie(t.get("type") in TENTE | {None}, f"{source} {cle} : tente.type {t.get('type')!r}")

    loc = r.get("localisation") or {}
    verifie(loc.get("contrainte") in CONTRAINTE | {None},
            f"{source} {cle} : contrainte {loc.get('contrainte')!r}")
    # une contrainte « aires_designees » sans aires nommées ne dit rien de plus
    # que la règle générique du type : c'est le trou qu'on cherche à combler.
    if loc.get("contrainte") == "aires_designees" and r.get("statut") == "restreint_zones":
        verifie(loc.get("aires_designees") or loc.get("detail"),
                f"{source} {cle} : aires_designees sans liste ni detail")

    for bout in ("debut", "fin"):
        h = (r.get("horaires") or {}).get(bout)
        verifie(horaire_valide(h), f"{source} {cle} : horaires.{bout} {h!r}")

    n = (r.get("duree") or {}).get("nuits_max")
    verifie(n is None or isinstance(n, int), f"{source} {cle} : nuits_max {n!r}")

    # La sanction fausse a traversé 6 entrées du dépôt : R332-70 (3e classe,
    # 68 €) et non L332-25, qui est 9 000 € et suppose une atteinte notable.
    s = r.get("sanction") or ""
    verifie("1 500 € (C. env. art. L332-25)" not in s,
            f"{source} {cle} : sanction L332-25 à 1 500 € (régression)")


def test_reserves(ids_couches):
    d = charge("reserves.json")
    meta = d.pop("_meta")
    verifie(meta.get("couverture"), "reserves.json : _meta sans couverture")

    for cle, r in d.items():
        verifie(cle.startswith("FR"), f"reserves.json : id_mnhn suspect {cle!r}")
        verifie(r.get("type") in TYPES, f"reserves.json {cle} : type {r.get('type')!r}")
        verifie(bool(r.get("reserve") or r.get("nom")), f"reserves.json {cle} : sans nom")
        verifie(len(r.get("resume") or "") >= 30, f"reserves.json {cle} : resume trop court")
        # une fiche sans source n'est pas vérifiable : c'est une affirmation
        verifie(bool(r.get("sources")), f"reserves.json {cle} : aucune source")
        champs_atomiques(cle, r, "reserves.json")

        if ids_couches:
            couche = ids_couches.get(r.get("type"))
            # une fiche dont l'id n'existe pas dans sa couche ne se joindra
            # jamais : invisible sur la carte, sans que rien ne le signale
            if couche is not None:
                verifie(cle in couche,
                        f"reserves.json {cle} : absent de la couche {r['type']}")
    return len(d)


def test_par_type():
    d = charge("par-type.json")
    d.pop("_meta")
    n = 0
    for cle, r in d.items():
        if cle.startswith("_"):
            continue
        n += 1
        verifie(cle in TYPES, f"par-type.json : clé {cle!r} inconnue")
        champs_atomiques(cle, r, "par-type.json")
        verifie(bool(r.get("libelle")), f"par-type.json {cle} : sans libelle")
    return n


def test_parcs():
    d = charge("parcs-nationaux.json")
    meta = d.pop("_meta")
    verifie(bool(meta.get("regle_aire_adhesion")),
            "parcs-nationaux.json : _meta sans regle_aire_adhesion")
    for cle, r in d.items():
        verifie(cle.startswith("FR33"), f"parcs-nationaux.json : id {cle!r} inattendu")
        verifie(bool(r.get("parc")), f"parcs-nationaux.json {cle} : sans nom de parc")
        champs_atomiques(cle, r, "parcs-nationaux.json")
    return len(d)


def ids_des_couches():
    """id_mnhn par couche, si data/ est téléchargé. Sinon None (CI sans données)."""
    if not DATA.exists() or not list(DATA.glob("*.geojson")):
        return None
    out = {}
    for f in DATA.glob("*.geojson"):
        if f.stem == "zones_internes":
            continue
        fc = json.loads(f.read_text(encoding="utf-8"))
        out[f.stem] = {x["properties"].get("id_mnhn") for x in fc.get("features", [])}
    return out


def main():
    couches = ids_des_couches()
    n_res = test_reserves(couches)
    n_typ = test_par_type()
    n_pn = test_parcs()

    if echecs:
        print(f"{len(echecs)} échec(s) :", file=sys.stderr)
        for e in echecs:
            print(f"  {e}", file=sys.stderr)
        sys.exit(1)

    jointure = "vérifiée" if couches else "sautée (data/ absent)"
    print(f"règles OK — {n_res} sites, {n_typ} types, {n_pn} cœurs de parc ; "
          f"cohérence des id_mnhn {jointure}")


if __name__ == "__main__":
    main()
