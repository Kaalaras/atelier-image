# Atelier Image — conception

Demande : moderniser la génération locale, puis fournir un dépôt privé installable par un débutant. Choix délégués par l’utilisateur, sans nouvelle validation de conception.

Windows x64, NVIDIA comparable à une RTX 5070 Ti 16 Go ; aucun inventaire du PC, télémétrie ou envoi de journaux. Les prérequis sont expliqués dans le guide. Pas de modification du Python système, du PATH système ou du pilote.

Choix : Forge Neo, révision du 1er novembre 2026, Python 3.13.15 et PyTorch 2.14.0/CUDA 13.0 recommandés par le projet. FLUX.2 klein 4B FP8 officiel et encodeur/VAE Comfy-Org : modèle compact récent, 4 étapes à 1024 px. Comparer par essais, sans prétendre avoir mesuré tous les moteurs/modèles.

Alternatives : ComfyUI offre davantage de contrôle mais des nœuds plus complexes ; SwarmUI ajoute une interface simple mais aussi .NET et un moteur supplémentaire. Forge Neo garde une interface familière avec moins de composants.

Distribution : dépôt `Kaalaras/atelier-image` privé ; ZIP des seuls scripts, documentation, versions et tests. Boutons Installer/Lancer/Arrêter. Runtime, modèles, images et journaux exclus du Git et du ZIP. Téléchargements publics depuis les éditeurs ; aucune clé GitHub transmise à l’ami. L’utilisateur peut envoyer le ZIP sans donner accès au dépôt.

Bootstrap PowerShell Windows 5.1 : télécharge uv portable avec SHA-256, puis Python géré dans le dossier. Gestion Python standard : source Forge figée, MinGit portable, environnement virtuel, installation, modèles avec empreintes, configuration initiale, lancement local. Reprise des fichiers partiels et remplacement uniquement après empreinte correcte ; jamais de suppression des images/configurations existantes.

Lancement : 127.0.0.1:7860, API locale pour essais, pas de partage public. Images dans un dossier visible. Pas de mise à jour aveugle : versions du manifeste testées et nouvelle release pour changer de pile.

Validation : tests standard-library des téléchargements et archives ; parsing Windows PowerShell ; installation réelle depuis le bootstrap ; génération 1024 px, chronométrage à chaud et comparaison avec l’ancien SD1.5 ; redémarrage ; réexécution de l’installation ; revue puis dépôt privé et release ZIP.
