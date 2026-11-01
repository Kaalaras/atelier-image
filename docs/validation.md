# Validation — 1er novembre 2026

## Pile testée

- Windows, NVIDIA GeForce RTX 5070 Ti 16 Go, pilote 621.01.
- Forge Neo 2.31, révision `7d6fd36c58a0e861640bcfe421e4f990921d7f2a`.
- Python géré 3.13.15, uv 0.13.6, PyTorch 2.14.0+cu130, torchvision 0.29.0+cu130.
- FLUX.2 klein 4B FP8 officiel BFL ; encodeur Qwen3 4B et VAE Flux2 fournis par Comfy-Org.
- Pillow 10.4.0 et pillow-heif 0.22.0 : choix de compatibilité avec Gradio 4.40.0. Le moteur recommande Pillow 13 et pillow-heif 1.8, mais ces versions contredisent les contraintes de son interface. Aucun conflit n’est ignoré dans la pile finale.
- Les 106 distributions présentes après préparation (dont pip amorcé par uv) passent `uv pip check`.
- Extensions désactivées ; attention native PyTorch, cudaMallocAsync et transfert asynchrone des poids.

## Génération réellement exécutée

1024 × 1024, Euler, Beta, 4 étapes, CFG 1, batch 1, seed 123456.

| Mesure | Durée HTTP totale |
|---|---:|
| Premier appel, incluant chargement et initialisations | 37,32 s |
| Même prompt, modèle chaud, appel suivant | 1,95 s |
| Même prompt, modèle chaud, deuxième appel | 1,78 s |

Le prompt demande une cabane rouge au bord d’un lac alpin, montagnes et un panneau BONJOUR. L’image produite a été inspectée visuellement : scène cohérente, cabane et panneau présents ; le texte reste susceptible d’être imparfait.

L’ancienne installation SD1.5/AUTOMATIC1111 avait généré une image 512 × 512 en 1,3 s. Les modèles, dimensions et paramètres diffèrent : ces valeurs ne constituent pas une comparaison de vitesse à qualité égale. Aucun classement exhaustif des moteurs ou modèles n’a été mesuré. Le choix vise un compromis moderne, simple et adapté à 16 Go.

## Installateur

- 11 tests unittest : cache valide sans réseau, fichier corrompu, reprise HTTP acceptée ou ignorée, ZIP malveillant, espaces/accents, conservation des réglages, configuration initiale avant le moteur, reprise d’une copie interrompue, exclusion mutuelle des opérations.
- Script bootstrap analysé par Windows PowerShell 5.1 ; installation complète exécutée par ce même interpréteur.
- Installation relancée sur le dossier existant : modèles vérifiés et réutilisés, paramètres conservés, pile de dépendances synchronisée exactement.
- Installation séparée depuis le ZIP dans un chemin avec espaces et accent, avec PATH limité à Windows (sans Python/Git système) : réussite. uv, Python géré, moteur et Git portable préparés par le bootstrap.
- Le test du premier lancement a découvert que le moteur créait une configuration minimale avant les réglages du paquet : l’ordre a été corrigé et protégé par un test de régression. La préparation a ensuite été rejouée sans configuration existante et le modèle et ses deux modules ont été correctement sélectionnés.
- Un second lancement pendant le démarrage a été refusé ; le PID enregistré est resté inchangé. Les paquets d’extensions essayés en développement ont été retirés par synchronisation de l’environnement exact.
- L’installation séparée a généré une image 768 × 768 via son API locale, avec le modèle et ses deux modules, puis son bouton d’arrêt a terminé son processus. Le paquet principal a ensuite été remis en service.
- Revue indépendante : onze tests réexécutés, aucun problème critique ou important restant sur les scripts revus. Les deux défauts de reprise/double lancement détectés lors de la première revue ont été corrigés et retestés.
- Pour éviter de retélécharger 12,5 Go pendant cet essai, les trois fichiers modèles étaient prépositionnés par liens physiques puis revérifiés ; le cache uv était partagé. Leur téléchargement réel et leurs empreintes ont été vérifiés lors du premier essai. Ce test n’est donc pas une machine virtuelle totalement vierge.

## Limites

Pas de test sur la machine de votre ami, autre GPU, pilote minimal 580, Windows 10 distinct, compte Windows totalement neuf ou machine virtuelle sans cache. La machine de validation possède 64 Go de RAM ; la recommandation de 32 Go n’a pas été mesurée sur une machine limitée à 32 Go. Pas de test d’édition d’images, LoRA, ControlNet, vidéo, ni toutes les formes de coupure réseau. Les paquets compilés issus du cache évitent de caractériser tous les cas de construction sans compilateur ; les composants principaux disposent de roues Windows Python 3.13.

Les trois fichiers modèles et les archives de bootstrap/source ont des SHA-256 figés. Les dépendances Python sont figées en version dans requirements-lock.txt et téléchargées depuis PyPI ou les roues CUDA officielles. Elles ne sont pas toutes figées par empreinte.
