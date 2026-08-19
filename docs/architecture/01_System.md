# BAgent Architecture

## Vision

BAgent è una piattaforma di Decision Intelligence.

L'obiettivo non è produrre una previsione.

L'obiettivo è costruire un sistema che:

- acquisisce conoscenza
- interpreta i dati
- genera evidenze
- prende decisioni
- apprende dai risultati

---

## Pipeline

WORLD

↓

Providers

↓

Collectors

↓

Parsers

↓

Knowledge

↓

Knowledge Repository

↓

Profile Builder

↓

Profiles

↓

Evidence Agents

↓

Fusion Engine

↓

Decision

↓

Learning

---

## Principi

1. I Provider non contengono logica di business.

2. Il Domain non conosce i Provider.

3. Gli Agent non leggono direttamente i Provider.

4. Tutta la conoscenza passa dal Knowledge Layer.

5. Ogni Decisione deve essere spiegabile.