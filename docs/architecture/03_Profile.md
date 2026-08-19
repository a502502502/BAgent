# Profile

## Definizione

Un Profile rappresenta l'insieme delle Knowledge associate a una singola entità.

Può essere:

- Player
- Match
- Tournament
- Team

---

## Responsabilità

Il Profile:

- aggrega le Knowledge

- offre una vista coerente agli Agent

- evita interrogazioni ripetute al Repository

---

## Principio

Il Repository salva Knowledge.

Il Profile viene costruito al momento della richiesta.