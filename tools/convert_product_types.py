#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import argparse
import xml.etree.ElementTree as ET
from typing import Callable, Dict, Optional
import yaml

#####
#
# python convert_product_types.py ../data/eProductType-enum.xml  --testproc-xml ../data/eTestProcedure-enum.xml -o polarion.yaml
#
#####


# Hier definierst du deine gewünschte Zuordnung: Actor → Produktname (so wie er im XML-Attribut name steht).
ACTOR_TO_PRODUCT = {
    "SUP-EPA": "Anb_Aktensystem_ePA",
    "EPA-Medication-Service": "Aktensystem_ePA",
    "EPA-Patient-Service": "Aktensystem_ePA",
    "EPA-Audit-Service": "Aktensystem_ePA",
    "EPA-MHD-Service": "Aktensystem_ePA",
    "EPA-XDS-Document-Service": "Aktensystem_ePA",
    "EPA-PS": "PS_ePA",
    "EPA-FdV": "Frontend_Vers_ePA",
    "EPA-FDV": "Frontend_Vers_ePA",
    "EPA-CS-KTR": "CS_ePA_KTR",
    "EPA-CS-Ombudsstelle": "CS_ePA_Ombudsstelle",
    "EPA-APO": "PS_ePA_Apotheke",
    "EPA-DIGA": "CS_ePA_DiGA",
    "ERP": "eRp_FD",
    "ERP-APO": "PS_E-Rezept_abgebend",
    "ERP-PS": "PS_E-Rezept_verordnend",
    "ERP-CS-KTR": "CS_E-Rezept_KTR",
    "SUP-ERP": "Anb_eRp_FD",
    "VSDM": "VSDM_2_FD",
    "SUP-VSDM":"Anb_VSDM_2_FD",
    "VSDM-Client": "CS_VSDM_2"
}

KEY_TO_TESTPROC_ID = {
    "Produkttest": "testProcedurePT03",
    "Anbietergutachten": "testProcedureAN05",
    "Herstellererklärung": "testProcedurePT02",
    "Produktgutachten": "testProcedurePT27"
}


def parse_name_to_info(
    xml_path: str,
    key_attr: str = "name",
    key_transform: Optional[Callable[[str], str]] = None
) -> Dict[str, dict]:
    """
    Parst das XML und liefert ein Mapping:
      <key_attr-Wert> -> {"id": <id>, "name": <name>, "description": <description oder None>}

    Args:
        xml_path: Pfad zur XML-Datei.
        key_attr: Welches Attribut als Key verwendet werden soll (z.B. "name", "id", "description").
        key_transform: Optionale Funktion, die auf den Key angewendet wird (z.B. str.lower).

    Hinweise:
        - Einträge ohne 'id' oder ohne 'name' werden übersprungen (da beides typischerweise benötigt wird).
        - Bei doppelten Keys gewinnt der erste Eintrag (setdefault).
    """
    tree = ET.parse(xml_path)
    root = tree.getroot()
    out: Dict[str, dict] = {}

    for opt in root.findall(".//option"):
        name = opt.get("name")
        opt_id = opt.get("id")
        desc = opt.get("description")
        key_val = opt.get(key_attr)

        # 'id' und 'name' sind für den Value-Block sinnvoll; ohne eine der beiden: skip
        if not opt_id or not name:
            continue
        # Key fehlt? -> skip
        if not key_val:
            continue

        if key_transform:
            key_val = key_transform(key_val)

        out.setdefault(key_val, {
            "id": opt_id,
            "name": name,
            "description": desc
        })

    return out


def build_actor_yaml(name_to_info: dict, actor_to_product_name: dict, include_empty_description: bool = True) -> dict:
    """
    Baut die gewünschte YAML-Struktur:
    actor_to_product:
      <Actor>:
        name: <Produktname>
        id:   <Produkt-ID>
        description: <Beschreibung>   # nur wenn vorhanden oder include_empty_description=True
    """
    out = {"actor_to_product": {}}
    missing = []

    for actor, product_name in actor_to_product_name.items():
        info = name_to_info.get(product_name)
        if not info:
            missing.append((actor, product_name))
            continue

        entry = {"name": product_name, "id": info["id"]}
        if info.get("description") is not None:
            entry["description"] = info["description"]
        elif include_empty_description:
            entry["description"] = ""
        out["actor_to_product"][actor] = entry

    for key, value in name_to_info.items():
        entry = {"name": key, "id": value["id"]}
        if value.get("description") is not None:
            entry["description"] = info["description"]
        elif include_empty_description:
            entry["description"] = ""
        out["actor_to_product"][key] = entry

    if missing:
        lines = [f"- Actor '{a}' erwartet Produktname '{p}' (nicht im XML gefunden)" for a, p in missing]
        raise ValueError("Fehlende Produktnamen im XML:\n" + "\n".join(lines))

    return out


def build_testproc_yaml(name_to_info_testproc: dict,
                        key_to_testproc_name: dict,
                        include_all_testprocs: bool = True) -> dict:
    """
    Baut:
    testproc_to_id:
      <Key>:
        id: <ID aus XML>
        name: <Name aus XML>

    Wenn include_all_testprocs=True, werden zusätzlich alle gefundenen Testprocs
    unter ihrem XML-Namen als Key aufgenommen.
    """
    out = {"testproc_to_id": {}}
    missing = []

    # Explizite Zuordnung
    for key, proc_name in key_to_testproc_name.items():
        info = name_to_info_testproc.get(proc_name)
        if not info:
            missing.append((key, proc_name))
            continue
        out["testproc_to_id"][key] = {"id": info["id"], "name": info.get("name", "")}

    # Optional: alle Testprozeduren aufnehmen (Key = XML-Name)
    if include_all_testprocs:
        for proc_name, info in name_to_info_testproc.items():
            if info.get("hidden", False):
                continue
            out["testproc_to_id"].setdefault(info["id"], {"id": info["id"], "name": info.get("name", "")})

    if missing:
        lines = [f"- Key '{k}' erwartet TestProcedure-Name '{p}' (nicht im XML gefunden)" for k, p in missing]
        raise ValueError("Fehlende TestProcedure-Namen im XML:\n" + "\n".join(lines))

    return out



def main():
    parser = argparse.ArgumentParser(description="XML → YAML (actor_to_product) Generator mit description")
    parser.add_argument("xml", help="Pfad zur XML-Datei (Enumeration)")
    parser.add_argument("--testproc-xml", help="Pfad zur TestProcedure-Enumeration XML")
    parser.add_argument("-o", "--out", help="Pfad zur Ausgabedatei (YAML). Default: stdout")
    parser.add_argument("--include-empty-description", action="store_true",
                        help="Lege description als leeren String an, wenn im XML keine vorhanden ist.")
    args = parser.parse_args()


    product_name_to_info = parse_name_to_info(args.xml)
    actor_block = build_actor_yaml(product_name_to_info, ACTOR_TO_PRODUCT, include_empty_description=args.include_empty_description)

    combined = dict(actor_block)  # shallow copy
    if args.testproc_xml:
        testproc_name_to_info = parse_name_to_info(args.testproc_xml, key_attr="id")
        testproc_block = build_testproc_yaml(testproc_name_to_info, KEY_TO_TESTPROC_ID)
        combined.update(testproc_block)
    else:
        # Wenn keine TestProc-XML übergeben wurde, lege eine leere Sektion an (optional)
        combined["testproc_to_id"] = {}


    yaml_text = yaml.safe_dump(combined, sort_keys=False, allow_unicode=True)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(yaml_text)
    else:
        sys.stdout.write(yaml_text)


if __name__ == "__main__":
    main()
