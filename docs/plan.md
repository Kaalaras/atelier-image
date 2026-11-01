# Atelier Image Implementation Plan

> For agentic workers: use superpowers:executing-plans inline; final fresh review under requesting-code-review.

**Goal:** installer local récent et paquet Windows autonome pour un débutant.
**Architecture:** bootstrap PowerShell, gestionnaire Python standard library, manifeste JSON figé, runtime ignoré par Git.
**Tech Stack:** PowerShell 5.1, Python 3.13, uv, Forge Neo, FLUX.2 klein 4B.
**Spec:** docs/design.md

## Global Constraints
- Windows x64 / NVIDIA 16 Go, aucun diagnostic automatique ni collecte.
- Aucun chemin machine dans les scripts publiés ; aucune modification globale du système.
- Runtime et modèles absents du dépôt ; sources HTTPS et empreintes SHA-256.
- Interface 127.0.0.1 uniquement ; erreurs compréhensibles, installation relançable.

## Review Focus
- Chemins avec espaces et accents : tests dans un dossier temporaire nommé ainsi.
- ZIP hostile : refus des chemins sortant de la destination et des liens.
- Coupure réseau / fichier corrompu : conserver le fichier valide, reprise vérifiée.
- Processus existant / port occupé : éviter un second moteur et ne jamais arrêter un processus inconnu.
- Paquet partagé : absence de runtime, identifiants et chemins personnels.

## Task 1 — téléchargement vérifié et bootstrap
- [x] Écrire et exécuter tests/test_installer.py : cache valide, mauvais hash, reprise HTTP et ZIP hostile.
- [x] Créer scripts/manage.py et scripts/bootstrap.ps1 ; manifeste versions.json.
- [x] Tests unittest puis parsing des scripts avec Windows PowerShell 5.1.

## Task 2 — installation et génération
- [x] Ajouter Installer.bat, Lancer.bat, Arreter.bat et gestion setup/start/stop.
- [x] Télécharger versions figées, préparer venv avec uv, configurer le modèle et les paramètres.
- [x] Exécuter l’installation complète via bootstrap ; génération, redémarrage et réinstallation idempotente.
- [x] Documenter mesures et limites dans docs/validation.md.

## Task 3 — publication
- [x] Guide français trois étapes, prérequis, première image, dépannage, licences.
- [x] Revue indépendante et correction des problèmes importants.
- [ ] Tests complets, ZIP source inspecté, création du dépôt privé et release.
- [ ] Vérifier confidentialité et disponibilité du ZIP ; livrer URL et exemple généré.
