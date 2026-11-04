# Kundbortfall – deployment i containeriserad miljö

Individuellt mini-projekt i kursen **Kontinuerlig integration och leverans** på
Nackademin. Projektet bygger vidare på
[teamets grupplaboration](https://github.com/pytt156/churn-mlops-pipeline).
Modellen förutsäger kundbortfall för det fiktiva telekombolaget Saldes Mobil AB.
All kunddata är fiktiv och används för utbildning.

## Teamets grund och mina tillägg

Teamets projekt innehåller modellträning, datavalidering, tester,
modellutvärdering, spårbarhet, Docker-paketering och ett FastAPI-API.
Det kan också generera en ringlista med kunder som riskerar att lämna.

Mina individuella tillägg är:

- Kubernetes Deployment och Service i `k8s/`.
- Publicering av API-imagen till GHCR för AMD64 och ARM64, med commit-SHA som tagg.
- Deployment från GitHub Actions till kursklustret via miljön `production`.
- En ny modellversion med `C=0.5` i logistisk regression.
- Rättning av publiceringen av scoring-imagen till mitt eget GHCR-namespace.

## Flöde från kod till tjänst

Arbetet följer **branch → pull request → kontroller → merge till main**.
Workflowet i `.github/workflows/ci.yml` kontrollerar data, kör tester och
dependency scan, tränar modellen och utvärderar dess kvalitet. Därefter testas
Docker-containrarna.

Vid push till `main` publiceras API-imagen till GHCR med commitens SHA som tagg.
Deployment-jobbet använder GitHub Environment `production`. Kravet på manuellt
godkännande konfigureras i GitHub, medan anslutningen till klustret använder
en Environment-secret med namnet `KUBECONFIG`.

Workflowet ersätter utvecklingstaggen `churn-api:dev` i manifestet med
den publicerade SHA-taggen, applicerar manifesten och väntar på färdig rollout.

## Kubernetes

Deploymenten `churn-api` kör två repliker med Kubernetes standardstrategi
Rolling Update. Den uppdaterar pods stegvis och passar projektets enkla tjänst.

- Containern lyssnar på port `8000`.
- En ClusterIP-Service exponerar port `80` mot containerport `8000`.
- Readiness och liveness kontrollerar `/health`.
- Varje pod begär `50m` CPU och `128Mi` minne, med minnesgränsen `384Mi`.

Readiness avgör om en pod kan ta emot trafik. Liveness kan starta om containern
vid upprepade fel. `/predict` används för att kontrollera en faktisk prediktion.

## Köra lokalt

Installera projektet, träna modellen och kör tester från projektroten:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python -m churn.model
pytest
```

Bygg och kör API-containern med den tränade modellen:

```bash
docker build -f Dockerfile.API -t churn-api:dev .
docker run --rm -p 8000:8000 churn-api:dev
```

För lokal Kubernetes-testning med ett befintligt kind-kluster som heter `kind`:

```bash
kind load docker-image churn-api:dev --name kind
kubectl --context kind-kind apply -f k8s/
kubectl --context kind-kind rollout status deployment/churn-api
kubectl --context kind-kind port-forward service/churn-api 8080:80
```

Testa i en annan terminal:

```bash
curl http://localhost:8080/health
curl -X POST http://localhost:8080/predict \
  -H 'Content-Type: application/json' \
  -d '{"alder":42,"manader_som_kund":18,"manadskostnad":399,"data_gb_per_manad":25,"supportarenden_12m":3,"region":"Stockholm","abonnemang":"Bas"}'
```

## Kurskluster och rollback

Tjänsten körs i namespace `haza-jijan`. Med kubeconfig redan konfigurerad kan
aktuellt tillstånd kontrolleras med:

```bash
kubectl -n haza-jijan get deployments,pods,services
kubectl -n haza-jijan rollout history deployment/churn-api
kubectl -n haza-jijan get deployment churn-api \
  -o jsonpath='{.spec.template.spec.containers[0].image}{"\n"}'
kubectl -n haza-jijan port-forward service/churn-api 8080:80
```

För rollback, ersätt `N` med önskad revision från revisionshistoriken:

```bash
kubectl -n haza-jijan rollout undo deployment/churn-api --to-revision=N
kubectl -n haza-jijan rollout status deployment/churn-api --timeout=180s
```

Rollback återställer API-containern inklusive modellen. Kontrollera image-taggen
och testa `/health` och `/predict` efteråt. Starta om port-forwarden vid behov.

Kubeconfig, tokens och andra autentiseringsuppgifter ska aldrig läggas i Git
eller skrivas ut i dokumentation.
