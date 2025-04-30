---
topic: iti-68
---

# {{page-title}}

Die Retrieve Document [ITI-68] Transaktion wird vom Document Consumer verwendet, um ein Dokument vom Document Responder abzurufen.


<requirement target="Primärsystem" title="Unterstützung von GET und PUT für Suchanfragen">
    Der Document Responder KANN sowohl GET- als auch POST-basierte Suchanfragen unterstützen, wie in der <a href="http://hl7.org/fhir/R4/http.html#search">FHIR HTML Spezifikation</a> festgelegt.
</requirement>

## Retrieve-Document-Anfragenachricht

Diese Nachricht ist ein HTTP GET-Request zum Abrufen des Dokuments der Form:

``GET [base]/epa/mhd/retrieve/v1/content/<documentreference.masteridentifier>.<file_extension>``

<requirement target="MHD Service" title="Zugriffsrechte im Document Responder gemäß Legal Policy">
    Der Document Responder MUSS die gesetzlich verbindlichen Regelungen der Zugriffsrechte bzgl. der Berufsgruppen und Datenkategorien aus der <a href="https://gemspec.gematik.de/docs/gemSpec/gemSpec_Aktensystem_ePAfueralle/gemSpec_Aktensystem_ePAfueralle_V1.2.5/#3.10">Legal Policy</a> berücksichtigen (d.h. er DARF Dokumente ohne Leserecht NICHT für die Suche und Herausgabe berücksichtigen). Ferner DARF der Document Responder NICHT Dokumente berücksichtigen, die durch eine <i>General Deny Policy</i> verborgen wurden. Die generelle Ausführung des Document Responder ist ausschließlich für befugte Nutzgruppen der nachstehenden Liste durchzuführen:
    <figure>
        <table class="regular">
            <thead><tr><th>professionOID</th></tr></thead>
            <tbody>
                <tr><td>oid_praxis_arzt</td></tr>
                <tr><td>oid_krankenhaus</td></tr>
                <tr><td>oid_institution-vorsorge-reha</td></tr>
                <tr><td>oid_zahnarztpraxis</td></tr>
                <tr><td>oid_praxis_psychotherapeut</td></tr>
                <tr><td>oid_institution-oegd</td></tr>
                <tr><td>oid_öffentliche_apotheke</td></tr>
                <tr><td>oid_institution-pflege</td></tr>
                <tr><td>oid_institution-geburtshilfe</td></tr>
                <tr><td>oid_praxis-physiotherapeut</td></tr>
                <tr><td>oid_praxis-ergotherapeut</td></tr>
                <tr><td>oid_praxis-logopaede</td></tr>
                <tr><td>oid_praxis-podologe</td></tr>
                <tr><td>oid_praxis-ernaehrungstherapeut</td></tr>
                <tr><td>oid_institution-arbeitsmedizin</td></tr>
                <tr><td>oid_versicherter</td></tr>
            </tbody>
        </table>
        <figcaption>Tabelle: Befugbare Nutzergruppen mit Ausführungsrecht von Suche und Herausgabe von Dokumenten</figcaption>
    </figure>
</requirement>
<requirement target="MHD Service" title="Testdurchführung 4">
    Das ist noch ein Test
</requirement>
<requirement target="Primärsystem" title="Booten">
    Der Rechner MUSS booten.
</requirement>
<requirement target="Primärsystem" title="IRQ">
    Der Rechner MUSS IRQ haben
</requirement>



### Auslöserereignisse

Der Document Consumer möchte ein Dokument erhalten.


### Nachrichtensemantik

Der Document Consumer sendet eine HTTP GET-Request zum Document Responder. Dieser Request SOLL vom Document Consumer genutzt werden, um Dokumente über `DocumentReference`-Instanzen des FHIR-Elements `DocumentReference.content.attachment.url` abzurufen.

Der einzige MIME-Type, der zurückgegeben werden darf, ist der MIME-Type, welcher im Element `DocumentReference.content.attachment.contentType` angegeben ist.

Der HTTP If-Unmodified-Since Header DARF NICHT im HTTP GET-Request inkludiert werden.

Der Document Consumer MUSS die folgenden HTTP Header bei einer Anfrage an den Document Responder setzen:

| Name | Anforderung | Datentyp | Beschreibung |
|------|----------|------|--------------|
| **x-insurantid** | MUSS | String | Health Record Identifier|
| **x-useragent** | KANN | String | User Agent Information |
| **X-Request-ID** | MUSS | String | UUID der Nachricht |


### Erwartetes Verhalten

Dem Document Responder MÜSSEN zur Bearbeitung dieser IHE-Transaktion die folgenden Informationen bereitstehen:
- Name des Nutzers
- Nutzergruppe/Rolle ((profession-)oid)
- Kennung (Telematik-ID)
- Hinweis auf eine gültige Befugnis des aktuellen Benutzers (requestor)

Der Document Responder MUSS das Dokument im angeforderten MIME-Type bereitstellen oder mit einem HTTP-Statuscode antworten, der den Fehlerzustand angibt. Der Document Responder DARF das Dokument NICHT transformieren.


## Retrieve-Document-Antwortnachricht

Dies ist die vom Document Responder gesendete Antwortnachricht.


### Auslöserereignisse

Die HTTP-Antwortnachricht wird nach Bearbeitung des Retrieve Document Request gesendet.


### Nachrichtensemantik

Die Nachricht MUSS eine HTTP Response Nachricht nach [RFC 2616](https://datatracker.ietf.org/doc/html/rfc2616) sein. Wenn das angeforderte Dokument zurückgegeben wird, MUSS der Document Responder mit HTTP Status Code 200 antworten. Der HTTP Body MUSS den Inhalt des angeforderten Dokuments beinhalten.

Die nachstehende Tabelle beschreibt Fehlersituationen und die HTTP-Antwortnachrichten.


#### Antwort-Status-Codes

| Status Code | Bedingung | Error Code | Bemerkung |
|-------------|-----------|------------|-----------|
| 200 | Successful operation | | |
| 403 | Requestor role is not in the list of allowed user groups | invalidOid | |
| 403 | Insurant-ID mismatch | | |
| 404 | Health record is in state UNKNOWN or INITIALIZED | noHealthRecord | (siehe 'Wiederholungsintervalle') |
| 409 | Health record is in state SUSPENDED | statusMismatch | (siehe 'Wiederholungsintervalle') |
| 500 | Any other error | internalError | (siehe 'Wiederholungsintervalle') |

Error Codes MÜSSEN mit dem entsprechenden HTTP Status Code vom Document Responder mit dem Media Type `application/json` nach folgendem Schema zurückgegeben werden:

```json
{
  "errorCode": "statusMismatch"
}
```

#### Wiederholungsintervalle

Die folgenden Wiederholungsintervalle werden im Falle einer Fehlerantwort definiert:

- '409' Conflict (statusMismatch)
    - etwa 24 Stunden
- '500' Internal Error
    - etwa 10 Minuten


#### Erwartetes Verhalten

Der Document Consumer verarbeitet die Antwort und bringt sie zur Anzeige im ePA-Client.


## Sicherheitsanforderungen

Generelle Sicherheitsanforderungen werden {{pagelink:privacy-security-consideration, text: hier}} festgehalten.


## Audit

Für Protokollierungszwecke ist die folgende Operation-ID definiert:

Operation-ID: **retrieveDocument_MHDSvc**

Die Protokollierung erfolgt über den Audit Event Service. Weitere Anforderungen sind [gemSpec_Aktensystem_ePAfueralle#3.13.1.1](https://gemspec.gematik.de/docs/gemSpec/gemSpec_Aktensystem_ePAfueralle/gemSpec_Aktensystem_ePAfueralle_V1.3.0/#3.13.1.1) zu entnehmen.</file_extension></documentreference.masteridentifier>