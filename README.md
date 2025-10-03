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
current: 1.0.4      # The current active version
directory: data     # Directory containing the text files with the documented requirements to be parsed
frozen_version: 1.0.4  # Marks if the release is frozen (null if not frozen)
frozen_hash: eb6ccfb60f31c933d07398f63a68c01d94a0f81bd6de8459a0c14829ecfc49a1
name: Test          # Project name
prefix: IG          # Prefix used for generating unique requirement keys
releases:           # List of available releases
  - 1.0.0
  - 1.0.1
  - 1.0.2
  - 1.0.3
  - 1.0.4
scope: MED          # Defines the scope of the requirements (e.g., medical domain)
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

#### Deprecated Example of a Requirement Tag

```xml
<requirement actor="Audit Event Service, Medication Service" conformance="SHALL" title="Support for Content-Types in FHIR-Data Interfaces" version="1">
    The FHIR Data Service SHALL support the Content-Type <code>application/fhir+json</code> for requests and responses at the interfaces.
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

#### New Version: Example of a Requirement Tag
```xml
<requirement conformance="SHALL" title="Support for Content-Types in FHIR-Data Interfaces" version="1">
    <meta lockversion="false"/>
    <actor name="EPA-Medication-Service">
        <testProcedure id="Produkttest"/>
    </actor>
    <actor name="Audit-Event-Service">
        <testProcedure id="Produktgutachten"/>
    </actor>
    The FHIR Data Service SHALL support the Content-Type <code>application/fhir+json</code> for requests and responses at the interfaces.
</requirement>
```


### Manage Releases
#### Create a New Release
```sh
igtools release <version> [--force] [--yes]
```
- `<version>`: Version number of the release.
- `--force`: Force the creation of a release even if it already exists.
- `--yes`: Automatically confirm prompts.

#### Freeze a Release

Freeze the current release: compute and store a release hash to lock its state. After freezing, any structural or textual changes will cause integrity check failures.

```sh
igtools release --freeze
```

#### Unfreeze a Release

Unfreeze the current release: remove the frozen state and its release hash. After unfreezing, further modifications to the release are allowed again.

```sh
igtools release --unfreeze
```

#### Check if Release is Feozen

Checks whether the current release is marked as final. If it is, the command will exit with a non-zero code.

```sh
igtools release --is-frozen
```


### Generate Release Notes
```sh
igtools ig-release-notes <output-directory> [--config <config-directory>] [--filename <filename>]
```
- `<output-directory>`: Directory to save the release notes.
- `--filename`: Name of the output file.

### Export Requirements
```sh
igtools export <output-directory> [--format <format>] [--filename <filename>] [--version <version>] [--with-deleted]
```
- `<output-directory>`: Directory to save the exported file.
- `--format`: Export format, either JSON or YAML (default: JSON).
- `--filename`: Optional filename. If no file extension is provided, it will be added automatically based on the format.
- `--version` / `-v`: Optional version identifier for exporting a specific requirements release (e.g., 1.0.5). If no filename is provided, a version-specific filename will be generated automatically.
- `--filename`: If set, deleted requirements are included in the export. By default, deleted requirements are excluded.

This command exports the requirements of a specific release into a structured JSON or YAML file. It is useful for archiving, sharing, or reviewing requirement sets externally.

#### Examples

__Export the current release to a default JSON file:__
```
igtools export ./exports
```

__Export a specific release to a YAML file:__
```
igtools export ./exports --version 1.0.5 --format YAML
```

__Export including deleted requirements:__
```
igtools export ./exports --version 1.0.5-1 --with-deleted
```
If no --filename is specified, the tool automatically generates a filename such as requirements-1.0.5.json or requirements.yaml, depending on the version and format provided.


### Import Requirements
```sh
igtools import <input-file> --release <release-version> [--next <next-version>] [--dry-run]
```
- `<input-file>`: JSON or YAML file with requirements to import.
- `--release`: The version number of the imported release (e.g., 1.0.5-1). If the release does not exist, it will be created.
- `--next`: Optional version number of the next release (e.g., 1.1.5). If set, any updates from the imported release will be propagated to this version.
- `--dry-run`: Simulate the import and propagation without modifying files.

Imported requirements are written to the specified release folder (if not already present). If a `--next` version is specified, the tool compares each requirement and:
- Adds new ones
- Updates changed ones
- Removes deleted requirements (only if also deleted in the imported version)

Deleted requirements are preserved in the imported release for documentation and changelog purposes but marked for removal in the next version if applicable.

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



