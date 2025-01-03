---
topic: iti-68
---

# {{page-title}}

Die Retrieve Document [ITI-68] Transaktion wird vom Document Consumer verwendet, um ein Dokument vom Document Responder abzurufen.


## Retrieve-Document-Anfragenachricht

Diese Nachricht ist ein HTTP GET-Request zum Abrufen des Dokuments der Form:

``GET [base]/epa/mhd/retrieve/v1/content/<documentreference.masteridentifier>.<file_extension>``


<requirement id="REQ-00016" target="MHD Service" title="Testdurchführung 3" version="1">
    Das ist ein Test 4
</requirement>
<requirement id="REQ-00017" target="MHD Service" title="Testdurchführung 4" version="1">
    Das ist noch ein Test
</requirement>
<requirement id="REQ-00018" target="Primärsystem" title="Booten" version="1">
    Der Rechner MUSS booten. Und das auch ziemlich schnell.
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