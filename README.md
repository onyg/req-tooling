# IG TOOLS

## Overview
**IG TOOLS** is a command-line tool for managing and processing textual requirements documented on the pages of FHIR Implementation Guides (IGs) created with the FHIR IG Publisher. It focuses on managing and processing these textual requirements separately from FHIR artifacts. The tool provides functionalities such as processing requirements, managing releases, generating release notes, exporting requirements, handling configurations, and extracting FHIR package definitions.

This tool was specifically developed for the gematik FHIR IG Template to ensure structured and efficient handling of textual requirements within FHIR Implementation Guides.

## Installation

You can install igtools directly using pip, with the current git repository that would be:
- pip install git+ssh://git@github.com/onyg/req-tooling.git

If you are on Ubuntu and don't want to create a virtualenv yourself, you can use pipx instead which instead creates the virtualenv implictly and uses it whenever you call igtools.
- pipx install git+ssh://git@github.com/onyg/req-tooling.git

## Features
- **Process Requirements**: Check for duplicate requirement IDs, process requirement data, and generate configurable unique requirement keys for the requirements project.
- **Manage Releases**: Create and finalize new release versions.
- **Generate Release Notes**: Generate release notes for a FHIR Implementation Guide.
- **Export Requirements**: Export requirements in different formats.
- **Extract FHIR Definitions**: Extract FHIR package definitions from a package manager.


## Usage

### Manage Configuration
#### Show Configuration
```sh
igtools config --show
```

#### Edit a Configuration File
```sh
igtools config
```

It is possible to customize the configuration to fit your specific needs. The configuration file allows defining the current release version, data directories, and project-specific settings. Below is an example of a configuration file:

```yaml
current: 1.0.5      # The current active version
directory: data     # Directory containing the text files with the documented requirements to be parsed
final: null         # Marks if the release is finalized (null if not finalized)
name: Test         # Project name
prefix: IG         # Prefix used for generating unique requirement keys
releases:
  - 1.0.5         # List of available releases
scope: MED        # Defines the scope of the requirements (e.g., medical domain)
```

By adjusting these values, you can control how the IG TOOLS handles versioning, storage locations, and requirement key generation.


Hier ist die angepasste Beschreibung für die **Process Requirements**-Nutzung:

---

Hier ist die angepasste **Process Requirements**-Sektion inklusive eines Beispiels für einen `<requirement>`-Tag:

---

### Process Requirements

```sh
igtools process --directory <input-directory> [--check]
```

- `--directory`: Directory containing the text files with documented requirements to be parsed.
- `--check`: Check for duplicate requirement IDs.

This command scans and processes textual requirements in the provided directory. It identifies and extracts `<requirement>` tags, ensuring each requirement has a unique key and version. If a key is missing, **IGTOOLS** generates a unique key based on the project configuration. If a key is provided manually, it is validated to ensure uniqueness within the project.

Additionally, the tool updates the **pagecontent** files by inserting the generated keys and versions into the respective `<requirement>` tags. This ensures consistency between structured storage and the original source files.

#### Example of a Requirement Tag

```xml
<requirement actor="Audit Event Service, Medication Service" conformance="SHALL" title="Support for Content-Types in FHIR-Data Interfaces" version="1">
    The FHIR Data Service MUST support the Content-Type <code>application/fhir+json</code> for requests and responses at the interfaces.
</requirement>
```
Each requirement is enclosed within a `<requirement>` tag and includes attributes such as:
- `actor`: Defines the actors involved.
- `conformance`: Specifies conformance levels (e.g., SHALL, SHOULD, MAY, or custom values).
- `title`: The title of the requirement.
- `version`: The version of the requirement.
- `key`: The unique requirement key (automatically generated unless manually specified). Duplicate keys are not allowed within the project.

If the `key` attribute is missing, **IGTOOLS** will automatically generate a unique key for the requirement and update the file accordingly.
The gematik FHIR IG Template provides a JavaScript function to render these structured requirements in a readable format on the IG pages.

### Manage Releases
#### Create a New Release
```sh
igtools release <version> [--force] [--yes]
```
- `<version>`: Version number of the release.
- `--force`: Force the creation of a release even if it already exists.
- `--yes`: Automatically confirm prompts.

#### Finalize a Release
```sh
igtools release --final
```

### Generate Release Notes
```sh
igtools ig-release-notes <output-directory> [--config <config-directory>] [--filename <filename>]
```
- `<output-directory>`: Directory to save the release notes.
- `--filename`: Name of the output file.

### Export Requirements
```sh
igtools export <output-directory> [--format <format>] [--filename <filename>] [--version <version>]
```
- `<output-directory>`: Directory to save the exported file.
- `--format`: Output format (JSON or YAML, default: JSON).
- `--filename`: Optional filename. If no file extension is provided, it will be added automatically based on the format.
- `--version` / `-v`: Optional version identifier for exporting a specific requirements release (e.g., 1.0.5). If no filename is provided, a version-specific filename will be generated automatically.

### Extract FHIR Definitions
```sh
igtools fhir-extract [--config <config-directory>] [--extractconfig <extract-config>] [--download <folder>]
```
- `--download`: Specifies the folder to download non-installed FHIR packages. The FHIR package will be downloaded to this folder to extract its definitions

```sh
igtools fhir-extract --extractconfig <extract-config>
```

- `--extractconfig`: Path to the extraction configuration file in YAML format.

This command extracts specific FHIR definitions from specified FHIR packages and exports them for explicit documentation in the **FHIR IG Publisher**. The extraction requires an additional YAML configuration file that defines which packages and resources should be extracted.

#### Example Usage

If the extraction configuration is stored in `igtools-fhir-extractor.yaml`, the command would be:

```sh
igtools fhir-extract --extractconfig igtools-fhir-extractor.yaml
```

#### Example Extraction Configuration (`igtools-fhir-extractor.yaml`)

```yaml
output: extracted/resources
packages:
  de.gematik.epa:
    version: 1.0.5
    resources:
      - StructureDefinition/epa-operation-outcome
  de.gematik.fhir.directory:
    version: 0.11.12
    resources:
      - StructureDefinition/OrganizationDirectory
      - StructureDefinition/PractitionerDirectory
```

### How it Works

- **Packages**: The configuration specifies FHIR packages along with their versions.
- **Resources**: Within each package, specific FHIR artifacts (e.g., StructureDefinitions, CodeSystems) are listed for extraction.
- **Output Directory**: Extracted resources are stored in the directory defined in the `output` field.

This feature ensures that selected FHIR resources are explicitly available for integration into the **FHIR IG Publisher**, making them referenceable and usable within implementation guides.



