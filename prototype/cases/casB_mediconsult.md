# Cas B — Téléconsultation médicale (MediConsult)

## Description du système (entrée de l'analyse)

MediConsult est une plateforme de téléconsultation exploitée par une PME de 25
personnes. Les patients prennent rendez-vous avec des médecins et réalisent des
consultations en visioconférence. Les médecins rédigent un compte rendu et peuvent
générer une ordonnance. Le secrétariat gère l'accueil, l'agenda et la facturation.
La plateforme est hébergée chez un prestataire certifié HDS (hébergement de données
de santé).

### Acteurs
- Patient (externe) : application mobile / site web — inscription, rendez-vous, visio,
  consultation de ses comptes rendus.
- Médecin (professionnel de santé) : portail web — visio, rédaction, accès aux dossiers
  des patients qu'il suit.
- Secrétariat / support (interne) : console d'administration — agenda, facturation.
- Administrateur technique (interne, privilégié) : exploitation, sauvegardes, journaux.
- Prestataires externes : hébergeur HDS, prestataire de visioconférence, notifications
  e-mail/SMS, paiement en ligne.

### Architecture en couches
1. **Accès** : app patient (mobile + web), portail médecin (navigateur), console du
   secrétariat (réseau interne uniquement).
2. **Applicatif** : WAF / API Gateway ; services — identité et accès (IAM, MFA),
   agenda, visio WebRTC, messagerie sécurisée, dossiers et comptes rendus, facturation.
3. **Données** : base de dossiers patients (données de santé), base des rendez-vous,
   stockage des comptes rendus, sauvegardes chiffrées hors ligne.
4. **Exploitation** : journaux d'authentification et d'accès (horodatés), supervision.

### Flux principaux
- Patient ⇄ Internet ⇄ WAF / API Gateway ⇄ services ⇄ base (HTTPS/TLS).
- Médecin ⇄ portail ⇄ API ⇄ dossier patient (accès conditionné à l'authentification forte).
- Services ⇄ prestataire de visio (média) et ⇄ notifications e-mail/SMS (sortants).
- Secrétariat ⇄ console ⇄ API (réseau interne).
- Administrateur ⇄ hébergement via VPN, accès privilégié contrôlé.
- Sauvegardes ⇄ stockage hors ligne chiffré et isolé.

### Frontières de confiance
1. Internet → WAF / API Gateway (publique).
2. API Gateway → réseau applicatif.
3. Réseau applicatif → réseau de données (base de dossiers).
4. Réseau interne → console d'administration.
5. Plateforme → prestataires externes (visio, SMS/e-mail, paiement).
6. Exploitation → infrastructure (VPN, administrateurs, sauvegardes).

### Contexte métier et contraintes
- RGPD : données de santé = catégorie particulière (art. 9) → protection renforcée,
  AIPD obligatoire, minimisation, notification CNIL en 72 h, DPO désigné.
- Secret médical : accès nominatifs et justifiés (besoin d'en connaître).
- Disponibilité : les consultations sont un enjeu de santé → RTO/RPO définis.
- Traçabilité : toute consultation de dossier doit être attribuable (non-répudiation).
- Chiffrement en transit (TLS 1.3) et au repos ; hébergement HDS.
- Aucune donnée patient ne doit sortir vers un service non contractuel.

## Actifs attendus (à ne pas oublier)
Données patients, identités (médecins, admins), console d'administration, service
visio, agenda, messagerie, comptes rendus/ordonnances, sauvegardes, journaux,
clés/certificats, prestataires, portail public, personnes, réputation/conformité.