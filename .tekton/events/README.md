# Trigger the CD pipeline from a GitHub webhook

This directory wires a GitHub **push** webhook to the `customers-pipeline`
PipelineRun via a Tekton `EventListener`. The manifests are already committed;
the one-time setup below creates the two pieces that cannot live in git: the
webhook **secret** and a public **Route** to the EventListener.

```
GitHub push (master)
        │  HMAC-signed JSON
        ▼
Route customers-listener ──► Service el-customers-listener ──► EventListener customers-listener
                                                                      │ github + cel interceptors
                                                                      ▼
                                                              Trigger customers-trigger
                                                                      ▼
                                                          PipelineRun customers-pipeline-xxxx
```

## One-time setup

Run these against the OpenShift namespace that hosts the pipeline.

1. Apply the Tekton resources (Pipeline, Tasks, EventListener, Trigger, bindings, PVC).

   ```bash
   kubectl apply -R -f .tekton/
   ```

2. Create the shared webhook secret. The value must match what you type into
   GitHub later, so capture it first.

   ```bash
   WEBHOOK_TOKEN="$(openssl rand -hex 20)"
   echo "GitHub webhook secret: ${WEBHOOK_TOKEN}"   # save this for step 4

   kubectl create secret generic github-webhook-secret \
     --from-literal=secretToken="${WEBHOOK_TOKEN}" \
     --dry-run=client -o yaml | kubectl apply -f -
   ```

   > The secret is intentionally **not** committed to git.

3. Expose the EventListener so GitHub can reach it.

   ```bash
   kubectl apply -f .tekton/events/event_listener_route.yaml
   kubectl get route customers-listener -o jsonpath='{.spec.host}{"\n"}'
   ```

   The host is your **Payload URL** (`https://<host>`). The Route uses edge TLS,
   which GitHub requires.

4. Add the webhook in GitHub.

   - Repository **Settings → Webhooks → Add webhook**
   - **Payload URL:** `https://<route-host>` (from step 3)
   - **Content type:** `application/json`
   - **Secret:** the `WEBHOOK_TOKEN` from step 2
   - **Which events:** *Just the push event*
   - Leave **Active** checked, then **Add webhook**.

## Prove it works

### Option A — a real merge to master

Merge any PR into `master`. GitHub sends the push webhook and Tekton starts a
run automatically:

```bash
tkn pipelinerun list
# or
kubectl get pipelinerun
```

### Option B — fire a signed webhook locally

Useful when GitHub cannot reach the cluster. Forward the EventListener service
and send a signed push payload with the helper script:

```bash
kubectl port-forward svc/el-customers-listener 8080:8080
```

In another terminal:

```bash
EVENTLISTENER_URL=http://localhost:8080 \
WEBHOOK_SECRET="${WEBHOOK_TOKEN}" \
.tekton/events/fire-webhook.sh
```

A successful delivery returns `HTTP 202`. Confirm a new PipelineRun appeared:

```bash
tkn pipelinerun list
```

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `HTTP 202` but no PipelineRun | CEL filter rejected it. The payload must have `ref == refs/heads/master`. |
| `HTTP 401` / signature mismatch | The `WEBHOOK_SECRET` differs from the `github-webhook-secret` value, or the body was re-encoded. Post raw JSON (the script uses `--data-binary`). |
| GitHub shows a red delivery | Check **Settings → Webhooks → Recent Deliveries** response, then `kubectl logs deploy/el-customers-listener`. |
| EventListener 404 on the Route | The EventListener has not reconciled yet: `kubectl get svc el-customers-listener`, `kubectl get pods -l eventlistener=customers-listener`. |
| PipelineRun starts but clone fails | The `after` sha must exist on the remote; on a merged PR the `master` sha is fine. |
| PipelineRun fails at deploy/BDD | See the pipeline itself; the DB (`k8s/postgres/`) and `customers-test-db` secret must be present in the namespace. |
