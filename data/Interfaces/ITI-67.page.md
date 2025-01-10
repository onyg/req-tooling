---
topic: iti-67
---

# {{page-title}}

Die Find Document References Transaktion des MHD Service basiert auf der [ITI-67 Spezifikation](https://profiles.ihe.net/ITI/MHD/4.2.2/ITI-67.html#2-3-67-find-document-references-iti-67). Diese Transaktion wird vom Document Consumer verwendet, um Dokumentverweise zu finden, die eine Reihe von Suchparametern erfüllen. Als Ergebnis erhält der Document Consumer ein vom Document Responder erzeugtes FHIR Bundle mit `DocumentReference`-Ressourcen, die den Anfrageparametern entsprechen. Zusätzlich wird diese IHE-Transaktion hier um eine Volltextsuche ergänzt.


## Nachricht
<plantuml>
@startuml iti-67

skinparam Shadowing false
skinparam ParticipantPadding 20
skinparam BoxPadding 10

skinparam sequence {
    ArrowColor DodgerBlue
    ActorBorderColor DodgerBlue
    LifeLineBorderColor Blue

    ParticipantBackgroundColor #3483eb
    ParticipantBorderColor #3483eb
    ParticipantFontSize 14
    ParticipantFontColor White

    ActorBackgroundColor #3483eb
    ActorFontSize 14
    NoteBackgroundColor #3483eb
}

hide footbox

participant "Document Consumer" as consumer
participant "Document Responder" as responder

activate consumer
activate responder

autonumber
consumer -&gt; responder: Find Document Reference

autonumber stop
consumer &lt;-- responder

deactivate consumer
deactivate responder

@enduml
</plantuml>

### Find-Document-References-Anfragenachricht

Diese Nachricht wird als HTTP `GET`- oder HTTP `POST`-Anfrage an die folgende URI gesendet, um eine Liste von Dokumentmetadaten abzurufen:

`[base]/epa/mhd/api/v1/fhir/DocumentReference` 


<requirement id="IG_3052R8O" target="MHD Service" title="Unterstützung von GET und PUT für Suchanfragen" version="1">
    Der Document Responder DARF sowohl GET- als auch POST-basierte Suchanfragen unterstützen, wie in der <a href="http://hl7.org/fhir/R4/http.html#search">FHIR HTML Spezifikation</a> festgelegt.
</requirement>
<requirement id="IG_5151UPG" target="MHD Service" title="Unterstützung von GET und POST für Suchanfragen" version="1">
    Der Document Responder KANN sowohl GET- als auch POST-basierte Suchanfragen unterstützen, wie in der <a href="http://hl7.org/fhir/R4/http.html#search">FHIR HTTP Spezifikation</a> festgelegt.
</requirement>
<requirement id="IG_0417J7F" target="MHD Service" title="Unterstützung von PUT und POST für Suchanfragen" version="1">
    Der Document Responder MUSS sowohl PUT- als auch POST-basierte Suchanfragen unterstützen, wie in der <a href="http://hl7.org/fhir/R4/http.html#search">FHIR HTTP Spezifikation</a> festgelegt.
</requirement>
<requirement id="IG_6345DT7" target="MHD Service" title="Unterstützung von GET und PATCH für Suchanfragen" version="1">
    Der Document Responder MUSS sowohl GET- als auch PATCH-basierte Suchanfragen unterstützen, wie in der <a href="http://hl7.org/fhir/R4/http.html#search">FHIR HTTP Spezifikation</a> festgelegt.
</requirement>

#### Auslöserereignisse

Wenn der Document Consumer eine metadatengestützte Volltextsuche über PDF/A-Dokumente durchführen und dazu `DocumentReference`-Ressourcen ermitteln möchte, sendet er eine **Find Document References**-Nachricht.


#### Nachrichtensemantik

Der Document Consumer führt eine HTTP-Suche über die `DocumentReference`-URL des Document Responders durch. Das Suchziel richtet sich nach der [FHIR-HTTP-Spezifikation](http://hl7.org/fhir/R4/http.html) und bezieht sich auf die `DocumentReference`-Ressource.

`GET [base]/epa/mhd/api/v1/fhir/DocumentReference?<query>` 

oder

`POST [base]/epa/mhd/api/v1/fhir/DocumentReference/_search` 

Diese URL kann vom Document Responder konfiguriert werden und unterliegt den folgenden Einschränkungen.

<requirement id="IG_0339AMT" target="Primärsystem" title="Verwendung von GET oder POST für Suchanfragen" version="1">
    Der Document Consumer MUSS mindestens eine der beiden HTTP-Methoden (GET oder POST) für Suchanfragen implementieren. Die parallele Unterstützung beider Methoden ist möglich, aber nicht zwingend erforderlich. 
</requirement>
<requirement id="IG_0829NOV" target="MHD Service" title="Unterstützung von GET und POST für Suchanfragen" version="1">
    Der Document Responder MUSS sowohl GET- als auch POST-basierte Suchanfragen unterstützen, wie in der <a href="http://hl7.org/fhir/R4/http.html#search">FHIR HTTP Search Spezifikation</a> festgelegt. 
</requirement>
<requirement id="IG_1433INQ" target="Primärsystem" title="HTTP-Header für MHD-Service-Anfragen" version="1">
    Der Document Consumer MUSS die folgenden HTTP Header aus der Tabelle: <i>HTTP Headers für die MHD-Service-Anfragen</i> bei einer Anfrage an den Document Responder setzen. 
</requirement>
<figure>

| Name | Anforderung | Datentyp | Beschreibung |
|------|----------|------|--------------|
| **x-insurantid** | MUSS | String | Health Record Identifier|
| **x-useragent** | KANN | String | User Agent Information |
| **X-Request-ID** | MUSS | String | UUID der Nachricht |

<figcaption>Tabelle: HTTP Headers für die MHD-Service-Anfragen</figcaption>
</figure>


#### Suchparameters

``TODO``

- Standard-Suchparameter für alle Ressourcen
- Vergleiche und Präzision für Zahlen, Daten und Mengen

<requirement id="IG_3146QXD" target="MHD Service" title="Unterstützung definierter Suchparameter" version="1">
    Der Document Responder MUSS die Suchparameter, die in dem CapabilityStatement mit dem Namen <i>EPACapabilityStatementMHDDocumentResponder</i> verarbeiten können.
</requirement>
<figure>
@```
from 
CapabilityStatement
for rest.resource where type = 'DocumentReference'
select
    join searchParam {
    Parameter: '<b>' &amp; name &amp; '</b>',
    Type: '<a href="http://hl7.org/fhir/r4/search.html#' &amp; type &amp; '" target="_blank">' &amp; type &amp; '</a>', 
    Definition: definition,
    Beschreibung: documentation,
    Anforderung: extension[0].value.iif('SHALL', 'MUSS', extension[0].value.iif('SHOULD', 'KANN', extension[0].value.iif('MAY', 'SOLL NICHT', extension[0].value.iif('SHOULD-NOT', 'DARF NICHT') ) ))
    }
```
<figcaption>Tablle: Suchparameter für die Resource DocumentReference aus dem CapabilityStatement <i>EPACapabilityStatementMHDDocumentResponder</i></figcaption>
</figure>


##### Beispiel GET

```
GET http://epa4all/epa/mhd/api/v1/fhir/DocumentReference?status=current&amp;type=http://www.ihe-d.de/fhir/CodeSystem/Dokumententypen|BERI&amp;setting=http://www.ihe-d.de/fhir/CodeSystem/FachrichtungenAerztlich|ALLG&amp;_fulltext=Herz
```

##### Beispiel POST

```
POST http://epa4all/epa/mhd/api/v1/fhir/DocumentReference?status=current&amp;type=http://www.ihe-d.de/fhir/CodeSystem/Dokumententypen|BERI&amp;setting=http://www.ihe-d.de/fhir/CodeSystem/FachrichtungenAerztlich|ALLG&amp;_fulltext=Herz
```

##### Beispiel POST im Request-Body

```
POST http://epa4all/R4/fhir/DocumentReference/_search	  
Host epa4all
Content-Type: application/x-www-form-urlencoded
Accept: application/fhir+json; fhirVersion=4.0										  

status=current&amp;setting=http://www.ihe-d.de/fhir/CodeSystem/FachrichtungenAerztlich|ALLG&amp;_fulltext=Kopf OR Zahl
```

#### Sortierung von Ergebnissen

<requirement id="IG_06706JX" target="Primärsystem" title="Sortierung der Suchergebnisse durch _sort" version="1">
    Das Document Consumer KANN die Reihenfolge der zurückgegebenen Ergebnisse durch den Parameter <code>_sort</code> angeben, der eine durch Kommas getrennte Liste von Sortierregeln in Prioritätsreihenfolge enthalten kann.
</requirement>


Beispiel:
``GET [base]/epa/mhd/api/v1/fhir/DocumentReference?_sort=status,-creation``

<requirement id="IG_9806C6I" target="MHD Service" title="Umsetzung der Sortierfunktion gemäß FHIR" version="1">
    Der Document Responder MUSS die Sortierfunktion nach <a href="https://www.hl7.org/fhir/r4/search.html#sort">FHIR R4 Sorting</a> implementieren.
</requirement>


#### Volltextsuche

``TODO`` Suchlogik beschreiben...


#### Erwartetes Verhalten

<requirement id="IG_18075TI" target="MHD Service" title="Erforderliche Benutzerinformationen für diese Transaktion" version="1">
    Dem Document Responder MÜSSEN zur Bearbeitung dieser IHE-Transaktion die folgenden Informationen bereitstehen:
    <ul>
<li>Name des Nutzers</li>
<li>Nutzergruppe/Rolle ((profession-)oid)</li>
<li>Kennung (Telematik-ID)</li>
<li>Hinweis auf eine gültige Befugnis des aktuellen Benutzers (requestor)</li>
</ul>
</requirement>
<requirement id="IG_00016" target="MHD Service" title="Aufbau der DocumentReference.content.attachment.url" version="1">
    Der Document Responder MUSS den Wert des FHIR-Elements <code>DocumentReferences.content.attachment.url</code> nach dem Muster <code>http://epa4all/epa/mhd/retrieve/v1/content/fb202c64-ff3f-4109-836e-0bbc75e246d3.pdf</code> aufbauen und den Speicherort zum Abruf des Dokuments somit festlegen. Dabei wird nach dem Pfad das Dokument über die <code>DocumentEntry.uniqueId</code> bzw. <code>DocumentReference.masterIdentifier</code> zuzüglich der Dateiendung des MIME-Types adressiert. Zulässige Dateiendungen in Kombination zum MIME-Type sind in der Anforderung _A\_24864-*_ des Spezifikationsdokuments <a href="https://gemspec.gematik.de/docs/gemSpec/gemSpec_Aktensystem_ePAfueralle/gemSpec_Aktensystem_ePAfueralle_V1.3.0/#3.13.1.1">gemSpec_Aktensystem_ePAfueralle#3.13.1.1</a> definiert.
</requirement>
<requirement id="IG_00017" target="MHD Service" title="Unterstützung der XDS on FHIR gemäß ITI-67" version="1">
    Der Document Responder MUSS mit dem XDS Document Consumer gruppiert sein, um die XDS on FHIR  Unterstütztung zu verarbeiten. Der Document Responder MUSS die XDS on FHIR  Unterstütztung nach <a href="https://profiles.ihe.net/ITI/MHD/4.2.2/ITI-67.html#23674131-xds-on-fhir-option">IHE MHD ITI-67 XDS on FHIR Spezifikation</a> implementieren.
</requirement>


#### Find-Document-References-Antwortnachricht

Rückgabe einer Instanz des {{pagelink:mhd-document-search-result-bundle-profile, text: EPAMHDDocumentSearchResultBundle}}-Profils


#### Auslöserereignisse

``TODO`` ...


#### Nachrichtensemantik

``TODO``

- Bundle
- Pagination
- Search Extension
 

Die nachstehende Tabelle beschreibt Fehlersituationen und die HTTP-Antwortnachrichten.

##### Antwort-Status-Codes

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


##### Wiederholungsintervalle

Die folgenden Wiederholungsintervalle werden im Falle einer Fehlerantwort definiert:

- '409' Conflict (statusMismatch)
    - etwa 24 Stunden
- '500' Internal Error
    - etwa 10 Minuten


##### Erwartetes Verhalten

Der Document Consumer verarbeitet die Antwort und bringt sie zur Anzeige im ePA-Client.


## Sicherheitsanforderungen

Generelle Sicherheitsanforderungen werden {{pagelink:privacy-security-consideration, text: hier}} festgehalten.


### Audit

Für Protokollierungszwecke ist die folgende Operation-ID definiert:

Operation-ID: **findDocumentReferences_MHDSvc**

Die Protokollierung erfolgt über den Audit Event Service. Weitere Anforderungen sind [gemSpec_Aktensystem_ePAfueralle#3.13.1.1](https://gemspec.gematik.de/docs/gemSpec/gemSpec_Aktensystem_ePAfueralle/gemSpec_Aktensystem_ePAfueralle_V1.3.0/#3.13.1.1) zu entnehmen.</query>