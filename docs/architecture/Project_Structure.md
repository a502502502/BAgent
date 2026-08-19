# BAgent Architecture

Version: 1.0

---

# Vision

BAgent è una piattaforma di Decision Intelligence.

Il suo obiettivo non è produrre previsioni.

Il suo obiettivo è costruire decisioni spiegabili che migliorano nel tempo.

---

# Core Principles

## 1

Il Domain rappresenta il mondo.

## 2

L'Application rappresenta il comportamento.

## 3

L'Infrastructure rappresenta la tecnologia.

## 4

L'App orchestra i casi d'uso.

---

# Folder Structure

BAgent/

app/

application/

domain/

infrastructure/

storage/

tests/

docs/

tools/

---

# Responsibilities

## app

Contiene esclusivamente i casi d'uso.

Non contiene logica di business.

---

## domain

Contiene i concetti fondamentali del sistema.

Non dipende da nessuna libreria esterna.

---

## application

Contiene il comportamento del sistema.

Builder

Agent

Reasoning

Learning

---

## infrastructure

Contiene tutto ciò che parla con il mondo esterno.

Database

HTTP

Browser

Provider

Config

Persistence

---

## storage

Contiene esclusivamente dati.

Mai codice.

---

## tests

Test automatici.

---

## docs

Documentazione tecnica.

---

# Dependency Rule

Consentito

App

↓

Application

↓

Domain

Application

↓

Infrastructure

Non consentito

Domain

↓

Infrastructure

Domain

↓

Application

Infrastructure

↓

Application

---

# Decision Pipeline

Knowledge

↓

Profile

↓

Evidence

↓

Decision

↓

Learning

---

# Central Objects

Knowledge

↓

Profile

↓

Evidence

↓

Decision

↓

Case

---

# Golden Rules

Ogni classe ha una sola responsabilità.

Ogni cartella ha una sola responsabilità.

Ogni Agent produce una sola Evidence.

Ogni Provider produce esclusivamente Knowledge.

Il Learning modifica il sistema.

Mai il contrario.