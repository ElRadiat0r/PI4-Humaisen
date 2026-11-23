# Contrat d'intégration — lot Personne 5

## État du lot

Le lot Personne 5 est isolé sur sa branche. Pour respecter la propriété des
fichiers, `config/settings.py`, `config/urls.py`, les vues P2/P3 et l'application
React existante ne sont pas modifiés. Le module de restitution et son composant
sont prêts, mais ils deviennent accessibles après les raccords listés ci-dessous.

## Rôles communs

L'API d'authentification P1 utilise les valeurs `client`, `humai` et `admin`.
La branche P2 utilise encore des constantes en majuscules; P5 normalise la casse
pour fonctionner avec les deux versions. Les comptes utilisent l'adresse e-mail
comme identifiant; il n'y a pas de champ `username`.

## Raccords de fusion

À faire lors de la fusion avec les responsables des fichiers partagés :

1. Dans `config/settings.py`, ajouter `apps.reports` à `INSTALLED_APPS`, ainsi
   que les apps P2 `apps.experts`, `apps.projects` et `django_filters` selon le
   guide P2. Ajouter le middleware CORS pour `http://localhost:5173`, renseigner
   `ALLOWED_HOSTS`, et exposer les variables `AI_PROVIDER`, `AI_API_URL`,
   `AI_API_KEY` et `AI_MODEL`.
2. Dans `config/urls.py`, inclure `apps.reports.urls`. Les routes agenda, projets
   et experts sont également décrites dans le guide P2/P3.
3. Créer les migrations P2 dans la branche P2, puis lancer `migrate` pour les
   apps P2 et `reports`.
4. Dans le composant projet React, monter
   `<ReportWorkspace projectId={project.id} />`. Le P4 peut utiliser
   `person5/authAdapter.js` pour la connexion et stocker les JWT P1 dans les clés
   `humaisenAccess` et `humaisenRefresh` attendues par le client API.
5. La branche P3 actuelle ne relie pas encore une réservation à
   `Project.assigned_expert` ni aux statuts du projet. Ce raccord est requis
   avant que l'HumAI affecté puisse ouvrir une restitution.

Le contrat de rôle de P2 doit aussi être aligné sur P1 (`client`, `humai`,
`admin`); le module P5 tolère les deux casses, mais il ne corrige pas les
permissions internes P2/P3.

## Contrat attendu pour l'authentification, les profils et l'agenda

- `POST /api/auth/register/` et `POST /api/auth/login/` sont utilisés par React;
  le JWT d'accès est envoyé comme `Authorization: Bearer ...`.
- `GET /api/experts/me/` crée au besoin le profil de l'HumAI connecté.
  `PATCH /api/experts/me/` met à jour son profil et ses compétences; les
  compétences disponibles viennent de `GET /api/skills/`.
- `GET/POST /api/availability/` gère les créneaux propres au profil HumAI.
  Seul ce HumAI ou un administrateur peut modifier, bloquer ou supprimer ces
  créneaux. Le client peut consulter les disponibilités.
- Un administrateur vérifie un profil par `POST /api/experts/{id}/verify/` ou le
  refuse par `POST /api/experts/{id}/reject/`.
- Le contrat P3 attendu est que `POST /api/appointments/` rattache le projet à
  l'expert choisi et fait évoluer son statut. Le HumAI affecté démarre ensuite
  la consultation avec `POST /api/appointments/{id}/start/`.
  L'app agenda P3 ne contient pas encore de modèle `Consultation`; jusqu'à sa
  création, React envoie l'identifiant du dossier comme `consultation_id`.

## Cycle d'un dossier et d'une restitution

1. Le client crée un brouillon avec `POST /api/projects/` (`title`, `description`,
   `domain`, `consent_data_processing`, `consent_ai_analysis`).
2. Les pièces jointes passent par `POST /api/projects/{id}/attachments/` en
   `multipart/form-data`, puis le dossier est soumis via
   `POST /api/projects/{id}/submit/`.
3. Après le raccord prévu côté P3, la réservation relie le projet à
   l'ExpertProfile sélectionné et fait avancer le statut
   `SUBMITTED → MATCHED → SCHEDULED`. Le HumAI peut démarrer la consultation,
   faisant passer le projet à `IN_PROGRESS`.
4. L'HumAI affecté génère une version brouillon avec
   `POST /api/reports/` et `{ "project": <id> }`. Le serveur vérifie les deux
   consentements avant tout appel fournisseur.
5. L'HumAI modifie le contenu par `PATCH /api/reports/{id}/` avec `{ "content":
   { ... } }`, puis valide par `POST /api/reports/{id}/validate/`.
6. Le client propriétaire peut lire les restitutions validées seulement.
   Chaque nouvelle génération crée une version; une version validée est
   immuable. Sa validation fait passer un projet `IN_PROGRESS → DELIVERED`.

## Fournisseur IA

`AI_PROVIDER=demo` est le défaut : réponse synthétique déterministe, aucun appel
réseau et aucune recherche documentaire. Il sert aux démonstrations, pas à une
expertise métier. Les sources et limites sont inscrites dans le brouillon.

`AI_PROVIDER=openai` active un endpoint compatible Chat Completions si
`AI_API_URL`, `AI_API_KEY` et `AI_MODEL` sont renseignés. La charge utile est
limitée au titre, à la description et au domaine; les e-mails et numéros de
téléphone reconnus sont masqués. Ce masquage par motifs ne garantit pas une
anonymisation complète (par exemple les noms et adresses restent à vérifier).
L'appel n'a lieu qu'avec les deux consentements du dossier. Le texte du prompt
n'est pas enregistré séparément par l'application; le résultat et les métadonnées
du fournisseur sont conservés dans la restitution.

L'extraction de texte des pièces jointes, le RAG, la transcription audio et la
génération vocale ne sont pas intégrés par ce lot. Le fournisseur ne reçoit pas
les pièces jointes.

## Démarrage local après fusion des raccords

```powershell
cd backend
Copy-Item .env.example .env
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Dans un second terminal :

```powershell
cd frontend
Copy-Item .env.example .env
npm install
npm run dev
```

Pour créer des profils HumAI synthétiques : `python manage.py seed_experts --count 10`.
Pour un parcours complet client/HumAI : `python manage.py seed_demo`. Le script
crée des comptes `demo.client@humaisen.test` et `demo.humai@humaisen.test` avec
le mot de passe `Demo1234!`, un projet et un brouillon synthétique. Un compte
HumAI nouvellement inscrit obtient aussi son profil P2 lorsqu'il ouvre son espace.
