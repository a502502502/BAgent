# ADR-001

## Titolo

Project Structure

## Stato

Accepted

## Decisione

Il progetto sarà organizzato in quattro layer.

Domain

Application

Infrastructure

App

## Motivazione

Separare la logica di business dalla tecnologia.

Ridurre l'accoppiamento.

Consentire la sostituzione dei Provider senza modificare gli Agent.

## Conseguenze

Ogni nuova classe dovrà rispettare questa struttura.