# STRIDE — grille d'identification (défaut)

Source : Microsoft (Kohnfelder & Garg, ~1999) ; cours E21 ch. 06 et 10.

## Les six catégories

| Lettre | Menace | Question | Propriété violée | Contre-mesure type |
|---|---|---|---|---|
| S | Usurpation (spoofing) | Quelqu'un peut-il se faire passer pour un autre ? | Authenticité | MFA, certificats |
| T | Falsification (tampering) | Peut-on modifier les données ? | Intégrité | Signature, hachage |
| R | Répudiation | Peut-on nier avoir fait une action ? | Non-répudiation | Journaux horodatés |
| I | Divulgation (info disclosure) | Des informations peuvent-elles fuiter ? | Confidentialité | Chiffrement, contrôle d'accès |
| D | Déni de service | Peut-on rendre le service indisponible ? | Disponibilité | Redondance, limitation de débit |
| E | Élévation de privilèges | Peut-on obtenir plus de droits ? | Autorisation | Moindre privilège |

## Usage
- S'applique à **chaque élément du DFD** et à **chaque frontière de confiance**.
- Les attaques se concentrent au passage des frontières de confiance.
- STRIDE dit QUOI chercher, pas comment prioriser → on complète par DREAD, CVSS
  ou une matrice probabilité × impact.

## Rappel cours (p. 108)
- « Quelles menaces pèsent sur cette application ? » → STRIDE.
- Modèle par défaut du projet E21 (sujet p. 11).