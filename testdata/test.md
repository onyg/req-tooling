---
topic: iti-67
---

<requirement actor="EPA-Medication-Service, EPA-PS" conformance="SHALL" key="IG-MED29091JHN" title="Unterstützung von GET und PUT für Suchanfragen" version="0">
    <meta lockversion="false"/>
    <actor name="EPA-Medication-Service">
        <testProcedure id="Produkttest"/>
        <testProcedure id="Produktgutachten"/>
    </actor>
    <actor name="EPA-PS">
        <testProcedure id="Produkttest"/>
        <testProcedure id="Produktgutachten"/>
    </actor>
    Der Document Responder DARF sowohl GET- als auch POST-basierte Suchanfragen unterstützen, wie in der <a href="http://hl7.org/fhir/R4/http.html#search">FHIR HTML Spezifikation</a> festgelegt.
</requirement>

<requirement actor="EPA-Medication-Service, EPA-PS" conformance="SHALL" key="IG-MED33770HUF" title="Unterstützung von GET und PUT für Suchanfragen" version="0">
    <meta lockVersion="false"/>
    <meta lockVersion="false"/>
    <meta lockVersion="false"/>
    <meta lockVersion="false"/>
    <meta lockVersion="false"/>
    <actor name="EPA-Medication-Service"/>
    <actor name="EPA-PS"><testProcedure id="Produkttest"/></actor>
    Der Document Responder DARF sowohl GET- als auch POST-basierte Suchanfragen unterstützen, wie in der <a href="http://hl7.org/fhir/R4/http.html#search">FHIR HTML Spezifikation</a> festgelegt.
</requirement>


<requirement actor="EPA-Medication-Service, EPA-PS" conformance="SHALL" key="IG-MED03867EEQ" title="Unterstützung von GET und PUT für Suchanfragen" version="0">
    <meta lockVersion="false"/>
    <meta lockVersion="false"/>
    <meta lockVersion="false"/>
    <meta lockVersion="false"/>
    <meta lockVersion="false"/>
    <actor name="EPA-Medication-Service"/>
    <actor name="EPA-PS"><testProcedure id="Produkttest"/></actor>
    Der Document Responder DARF sowohl GET- als auch POST-basierte Suchanfragen unterstützen, wie in der <a href="http://hl7.org/fhir/R4/http.html#search">FHIR HTML Spezifikation</a> festgelegt.
</requirement>

<requirement actor="EPA-Medication-Service, EPA-PS" conformance="SHALL" key="IG-MED40753QXN" title="Unterstützung von GET und PUT für Suchanfragen" version="0">
    <meta lockVersion="false"/>
    <meta lockVersion="false"/>
    <meta lockVersion="false"/>
    <meta lockVersion="false"/>
    <meta lockVersion="false"/>
    <actor name="EPA-Medication-Service"/>
    <actor name="EPA-PS"><testProcedure id="Produkttest"/></actor>
    Der Document Responder DARF sowohl GET- als auch POST-basierte Suchanfragen unterstützen, wie in der <a href="http://hl7.org/fhir/R4/http.html#search">FHIR HTML Spezifikation</a> festgelegt.
</requirement>


<requirement conformance="SHALL" key="IG-MED26526K0H" title="GET und POST / PUT für Suchanfragen" version="3">
    <meta lockVersion="true"/>
    <actor name="EPA-Medication-Service"/>
    Der Document Responder DARF sowohl GET- als auch POST-basierte Suchanfragen unterstützen, wie in der <a href="http://hl7.org/fhir/R4/http.html#search">FHIR HTML Spezifikation</a> fest
</requirement>



<requirement conformance="SHALL" key="IG-MED84642MWN" title="Zugriffsrechte im Document Responder gemäß Legal Policy" version="0">
    <actor name="EPA-Medication-Service">
        <testProcedure id="Produktgutachten"/>
        <testProcedure active="true" id="Produkttest"/>
    </actor>
    <actor name="EPA-PS">
        <testProcedure id="Produkttest"/>
    </actor>
    <actor name="EPA-FdV">
        <testProcedure id="Produkttest"/>
    </actor>
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