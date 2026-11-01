# Atelier Image

Générer des images sur son PC avec **Forge Neo** et **FLUX.2 klein 4B**.
Interface dans le navigateur, calcul local sur la carte graphique. Pas d’abonnement.

## Avant de commencer

- **Windows 10/11 64 bits**, carte **NVIDIA RTX récente avec 16 Go de mémoire vidéo**.
- **Pilote NVIDIA 580 ou plus récent**, à mettre à jour depuis [NVIDIA](https://www.nvidia.com/fr-fr/drivers/) si nécessaire.
- **32 Go de RAM recommandés**, environ **70 Go libres** pour l’installation et les caches.
- Connexion Internet : environ **17 Go à télécharger**, selon les caches et dépendances. Le premier démarrage peut encore récupérer des fichiers de configuration.

Ce paquet vise un PC comparable à une RTX 5070 Ti. AMD, Intel, Mac et les cartes anciennes ne sont pas pris en charge par cette version. Aucun diagnostic automatique ou inventaire de votre PC n’est exécuté.

## Installer en trois étapes

1. Télécharger **Atelier-Image-Windows.zip** depuis la [dernière version](../../releases/latest), ou demander ce fichier à la personne qui vous a envoyé ce guide.
2. Clic droit sur le ZIP → **Extraire tout**. Choisir un dossier personnel, par exemple `Documents\Atelier Image`. Ne pas lancer depuis le ZIP, `Program Files`, un lecteur réseau ou un dossier synchronisé par OneDrive.
3. Double-cliquer sur **Installer.bat**. Attendre le message **Installation terminée**. Ensuite, double-cliquer sur **Lancer.bat**.

**Ne pas lancer en administrateur.** Python et Git sont préparés dans le dossier du programme. Aucun réglage Windows global n’est changé. Si Windows ou votre antivirus bloque un fichier, vérifier sa provenance et demander de l’aide ; ne pas désactiver vos protections.

Une installation peut prendre 10 à 40 minutes selon la connexion. Si elle échoue ou si Internet coupe, relancer **Installer.bat** : les fichiers complets sont vérifiés et réutilisés, les fichiers partiels peuvent reprendre. Vos images et réglages sont conservés. Éviter de lancer deux installations à la fois.

## Votre première image

Après **Lancer.bat**, le navigateur ouvre **http://127.0.0.1:7860**. Si rien ne s’ouvre, copier cette adresse dans le navigateur.

Dans l’onglet **txt2img** :

1. Vérifier **UI Preset : klein** et le modèle **flux-2-klein-4b-fp8**.
2. Écrire la description dans **Prompt**, par exemple :

   `A photograph of a red wooden cabin beside a turquoise alpine lake, tall mountains in the background, bright morning light, realistic details.`

3. Garder **4 steps**, **CFG 1**, **Euler**, **Beta**, **1024 × 1024**, **Batch size 1**, puis cliquer **Generate**.

Le premier calcul peut être plus lent. Un prompt anglais est un bon point de départ. Avec ce modèle distillé, laisser le **Negative prompt** vide ; augmenter fortement les steps ou le CFG n’est pas une amélioration automatique.

Les images sont enregistrées dans le dossier **images**. Pour arrêter et libérer la mémoire de la carte, double-cliquer **Arreter.bat**. Fermer le navigateur seul ne suffit pas.

## En cas de problème

| Message / symptôme | Action |
|---|---|
| Installation absente | Lancer **Installer.bat** avant **Lancer.bat**. |
| Port 7860 déjà utilisé | Arrêter l’ancienne interface Stable Diffusion. Pour ce paquet, utiliser **Arreter.bat**. |
| Manque de mémoire vidéo | Fermer jeux et autres logiciels utilisant la carte. Revenir à une seule image, puis essayer 768 × 768. |
| Erreur CUDA / pilote trop ancien | Mettre à jour le pilote NVIDIA, redémarrer Windows, puis relancer. |
| SHA-256 incorrect / téléchargement interrompu | Relancer **Installer.bat** avec une connexion stable. Aucun fichier non vérifié n’est activé. |
| Le moteur s’arrête au démarrage | Consulter **logs\forge.log**. Ne partager ce journal qu’avec une personne de confiance ; il peut contenir des chemins locaux et vos prompts. |
| Le programme fonctionnait avant de déplacer le dossier | Le remettre à sa place. Pour changer d’emplacement, extraire un nouveau ZIP et réinstaller, puis copier vos images. |

Pour désinstaller : **Arreter.bat**, sauvegarder le dossier **images**, puis supprimer le dossier Atelier Image. Aucun service Windows n’est installé.

## Confidentialité et mises à jour

La génération et l’interface restent sur votre PC, adresse locale uniquement. Le paquet n’envoie aucun diagnostic ni journal et désactive les options de télémétrie connues. Les téléchargements contactent GitHub, PyTorch, Python et Hugging Face ; ces services voient les requêtes réseau usuelles. Aucun accès public n’est ouvert.

Les versions testées figurent dans [versions.json](versions.json). Ne pas mettre à jour chaque dépendance séparément : utiliser une nouvelle release testée, de préférence dans un nouveau dossier. Il n’y a pas de mise à jour silencieuse.

## Pour la personne qui partage

Le dépôt est privé : votre ami doit soit être invité sur GitHub, soit recevoir directement le **ZIP de la release**. Envoyer seulement le lien privé ne lui donnera pas accès. Le ZIP s’installe sans compte GitHub. Ne jamais envoyer votre dossier `.runtime`, vos clés ou l’installation complète.

## Sources et licences

- [Forge Neo](https://github.com/Haoming02/sd-webui-forge-classic/tree/neo) : AGPL-3.0, téléchargé depuis sa source officielle.
- [FLUX.2 klein 4B FP8](https://huggingface.co/black-forest-labs/FLUX.2-klein-4b-fp8) : Apache-2.0.
- [Encodeur et VAE Comfy-Org](https://huggingface.co/Comfy-Org/Flux-2-Klein-4B) : voir les licences et attributions du dépôt.
- [uv](https://github.com/astral-sh/uv), [Python](https://www.python.org/), [Git for Windows](https://gitforwindows.org/) et [PyTorch](https://pytorch.org/) conservent leurs licences respectives. Les dépendances sont téléchargées chez leurs éditeurs ; les poids et le moteur ne sont pas redistribués dans ce dépôt.
- Scripts de ce paquet : [licence MIT](LICENSE).

Les images générées peuvent contenir des erreurs. La performance mesurée et les limites de validation sont indiquées dans [docs/validation.md](docs/validation.md).

## Développement

Tests sans GPU ni téléchargement : `python -m unittest discover -s tests -v` (Python 3.11+).
Les fichiers `.runtime/`, `app/`, `images/`, `logs/` et les archives ne font jamais partie du dépôt.
