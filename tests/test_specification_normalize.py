import os
import json
import pytest
from unittest.mock import patch, mock_open, MagicMock

from igtools.specifications.data import Requirement, ReleaseState
import igtools.specifications.normalize as normalize


def test_editorial_whitespace_does_not_change_fingerprint():
    req_one = Requirement(
        key="REQ-001",
        title="Zusammenstellung der Hashwerte des EPAMedicationUniqueIdentifier",
        actor=["EPA-First-Service", "EPA-Second-Service", "EPA-Third-Service"],
        conformance="SHALL",
        text='Der Medication Service MUSS die einzelnen Bestandteile in folgender Reihenfolge in die Hash-Berechnung einfließen lassen:\n    <br/><br/>\n    <ol>\n      <li><i>Medication.code</i> - Alle Kodierungen in der Reihenfolge ihrer Angabe in der <i>Medication</i>-Instanz.</li>\n      <li><i>Medication.code.text</i> - Nach Entfernung von Leerzeichen und Umwandlung in Kleinbuchstaben.</li>\n      <li><i>Medication.form</i> - Alle Kodierungen in der Reihenfolge ihrer Angabe in der <i>Medication</i>-Instanz.</li>\n      <li>\n        <i>Medication.ingredient[x]</i> - Alphabetisch sortierte Kombination aus:\n        <ul>\n          <li>Falls ein <i>ingredient.itemCodeableConcept</i> vorhanden ist, werden die Kodierungen und der Text extrahiert.</li>\n          <li>Falls eine <i>ingredient.strength</i> vorhanden ist, werden die numerischen Werte und Einheiten verarbeitet.</li>\n         <li>Falls <i>ingredient.itemReference</i> vorhanden ist, wird die Referenz gespeichert und erst nach der Verarbeitung von <i>ingredient.itemCodeableConcept</i> behandelt.</li>\n        </ul>\n      </li>\n      <li>Alphabetische Sortierung der Ingredients - Nach der Kombination der Werte müssen alle Ingredients alphabetisch sortiert werden.</li>\n      <li>Enthaltene Medications (<i>contained</i>) - Falls eine über <i>ingredient.itemReference</i> referenzierte <i>contained</i> Medication existiert, wird sie rekursiv verarbeitet und alphabetisch sortiert.</li>\n      <li>Extensions - Berücksichtigung spezifischer Extensions mit der entsprechenden URL, wobei die Werte in Kleinbuchstaben umgewandelt, Leerzeichen entfernt und alphabetisch sortiert werden.</li>\n    </ol>\n    Der daraus resultierende Hashwert wird in Großbuchstaben dargestellt und stellt den eindeutigen <i>EPAMedicationUniqueIdentifier</i> dar. Der Begriff <i>\"Kodierung\"</i> in dieser Anforderung bedeutet die ausschließliche Berücksichtigung der FHIR-Elementwerte <i>Coding.code</i> und <i>Coding.system</i> des Datentyps <i>Coding</i>.',
        version=0,
        process=ReleaseState.STABLE.value
    )
    req_two = Requirement(
        key="REQ-001",
        title="Zusammenstellung der Hashwerte des EPAMedicationUniqueIdentifier",
        actor=["EPA-Third-Service", "EPA-Second-Service", "EPA-First-Service"],
        conformance="SHALL",
        text='Der Medication Service MUSS die einzelnen Bestandteile in folgender Reihenfolge in die Hash-Berechnung einfließen lassen: Medication.code - Alle Kodierungen in der Reihenfolge ihrer Angabe in der Medication-Instanz. Medication.code.text - Nach Entfernung von Leerzeichen und Umwandlung in Kleinbuchstaben. Medication.form - Alle Kodierungen in der Reihenfolge ihrer Angabe in der Medication-Instanz. Medication.ingredient[x] - Alphabetisch sortierte Kombination aus: Falls ein ingredient.itemCodeableConcept vorhanden ist, werden die Kodierungen und der Text extrahiert. Falls eine ingredient.strength vorhanden ist, werden die numerischen Werte und Einheiten verarbeitet. Falls ingredient.itemReference vorhanden ist, wird die Referenz gespeichert und erst nach der Verarbeitung von ingredient.itemCodeableConcept behandelt. Alphabetische Sortierung der Ingredients - Nach der Kombination der Werte müssen alle Ingredients alphabetisch sortiert werden. Enthaltene Medications (contained) - Falls eine über ingredient.itemReference referenzierte contained Medication existiert, wird sie rekursiv verarbeitet und alphabetisch sortiert. Extensions - Berücksichtigung spezifischer Extensions mit der entsprechenden URL, wobei die Werte in Kleinbuchstaben umgewandelt, Leerzeichen entfernt und alphabetisch sortiert werden. Der daraus resultierende Hashwert wird in Großbuchstaben dargestellt und stellt den eindeutigen EPAMedicationUniqueIdentifier dar. Der Begriff "Kodierung" in dieser Anforderung bedeutet die ausschließliche Berücksichtigung der FHIR-Elementwerte Coding.code und Coding.system des Datentyps Coding.',
        version=0,
        process=ReleaseState.STABLE.value
    )
    fp1, _ = normalize.build_requirement_fingerprint(req_one)
    fp2, _ = normalize.build_requirement_fingerprint(req_two)
    assert fp1 == fp2


def test_substantive_conformance_change_bumps():
    r1 = Requirement(key="REQ-001", text="ABC", conformance="SHALL", actor=["EPA-Third-Service", "EPA-Second-Service", "EPA-First-Service"], title="The Title")
    r2 = Requirement(key="REQ-001", text="ABC", conformance="SHOULD", actor=["EPA-First-Service", "EPA-Second-Service", "EPA-Third-Service"], title="The Title")
    fp1, _ = normalize.build_requirement_fingerprint(r1)
    fp2, _ = normalize.build_requirement_fingerprint(r2)
    assert fp1 != fp2  # substantive


def test_normalize_normalize_text_for_semantics_removes_spaces_and_tabs():
    assert normalize.normalize_text_for_semantics("  This is   a test\t") == "thisisatest"


def test_normalize_normalize_text_for_semantics_removes_linebreaks():
    assert normalize.normalize_text_for_semantics("This\nis\na\ntest") == "thisisatest"


def test_normalize_normalize_text_for_semantics_mixed_whitespace():
    assert normalize.normalize_text_for_semantics(" \nThis\t is  \na \ttest ") == "thisisatest"


def test_normalize_normalize_text_for_semantics_is_case_insensitive():
    assert normalize.normalize_text_for_semantics("This Is A TEST") == "thisisatest"

@pytest.mark.parametrize("input_value, expected", [
    ("This <b>is</b> A TEST", "thisisatest"),
    ("<table><tr><td>This</td></tr><tr><td><b>is</b> A TEST</td></tr></table>", "thisisatest"),
])
def test_normalize_normalize_text_for_semantics_with_no_html_tags(input_value, expected):
    assert normalize.normalize_text_for_semantics(input_value) == expected


def test_normalize_normalize_text_for_semantics_empty_string():
    assert normalize.normalize_text_for_semantics("") == ""


def test_normalize_normalize_text_for_semantics_only_whitespace():
    assert normalize.normalize_text_for_semantics(" \t\n  ") == ""

