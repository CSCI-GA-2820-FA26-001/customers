# Trigger the CD Pipeline from a GitHub Webhook

This directory configures a GitHub push webhook to trigger the `customers-pipeline` through a Tekton `EventListener`.

The event flow is:

```text
GitHub push to master
        |
        | HMAC-SHA256 signed JSON payload
        v
OpenShift Route: customers-listener
        |
        v
Service: el-customers-listener
        |
        v
EventListener: customers-listener
        |
        v
Trigger: customers-trigger
        |
        v
TriggerTemplate: customers-template
        |
        v
PipelineRun: customers-pipeline-xxxx
        |
        v
Pipeline: customers-pipeline
```

## Prerequisites

Before applying the resources, verify that:

- You have access to the OpenShift project where the pipeline will run.
- Tekton Pipelines and Tekton Triggers are installed.
- The `pipeline` ServiceAccount has the permissions required by the EventListener and pipeline tasks.
- The `customers-test-db` Secret exists and contains the required database connection value.
- The database resources required by the application are available.
- The cluster has an accessible OpenShift image registry.
- The pipeline's required storage and build permissions are configured.

The webhook secret must be created separately. It must not be committed to Git.

## 1. Apply the Tekton resources

Run the following command from the repository root:

```bash
kubectl apply -R -f .tekton/
```

This recursively applies the YAML manifests under `.tekton/`, including the Pipeline, Tasks, PVC, EventListener, Trigger, TriggerBinding, TriggerTemplate, and OpenShift Route.

The OpenShift Route requires an OpenShift cluster with the Route API available.

## 2. Create the GitHub webhook secret

Generate a secret:

```bash
WEBHOOK_TOKEN="$(openssl rand -hex 20)"
```

Keep the generated value available for the GitHub configuration in step 4.

Create the Kubernetes Secret:

```bash
kubectl create secret generic github-webhook-secret \
  --from-literal=secretToken="${WEBHOOK_TOKEN}" \
  --dry-run=client -o yaml | kubectl apply -f -
```

The Secret name and key must match the references in `trigger.yaml`:

- Secret: `github-webhook-secret`
- Key: `secretToken`

Do not commit the generated secret or place it in the repository.

## 3. Retrieve the EventListener Route

The Route manifest is already included in `.tekton/events/event_listener_route.yaml` and was applied in step 1.

Retrieve its hostname:

```bash
kubectl get route customers-listener \
  -o jsonpath='{.spec.host}{"\n"}'
```

The resulting hostname is used as the GitHub webhook Payload URL:

```text
https://<route-host>
```

The Route uses edge TLS termination to expose the EventListener through HTTPS.

Verify that the Route points to the `el-customers-listener` Service and that the Service is available before configuring GitHub.

## 4. Configure the GitHub webhook

In the GitHub repository:

1. Open **Settings → Webhooks**.
2. Select **Add webhook**.
3. Configure the following values:

| Setting | Value |
|---|---|
| Payload URL | `https://<route-host>` |
| Content type | `application/json` |
| Secret | The generated `WEBHOOK_TOKEN` from step 2 |
| Events | Just the push event |
| Active | Enabled |

4. Select **Add webhook**.

The webhook sends push events to the EventListener. The Trigger's CEL filter is responsible for accepting events targeting `refs/heads/master`.

## 5. Verify webhook delivery

There are two ways to test the integration.

### Option A: Merge a pull request into master

Merge a pull request into `master`.

GitHub should send a push event containing the updated commit SHA. The EventListener should process the event, and the Trigger should create a PipelineRun.

Check for PipelineRuns:

```bash
tkn pipelinerun list
```

Alternatively:

```bash
kubectl get pipelineruns
```

Verify that a new PipelineRun was created for the webhook event. Then inspect its status and task logs.

### Option B: Send a locally generated signed webhook

This option tests the EventListener without requiring an actual GitHub delivery. It still requires access to a running cluster.

First, forward the EventListener Service:

```bash
kubectl port-forward svc/el-customers-listener 8080:8080
```

Keep this command running.

Open a second terminal from the repository root. Set the webhook secret to the exact value generated in step 2.

Shell variables are not shared between separate terminal sessions, so paste the saved secret explicitly:

```bash
EVENTLISTENER_URL=http://localhost:8080 \
WEBHOOK_SECRET="PASTE_YOUR_WEBHOOK_TOKEN_HERE" \
./.tekton/events/fire-webhook.sh
```

The script generates a GitHub-style push payload, calculates its HMAC-SHA256 signature, and sends the request to the EventListener.

An HTTP `202` response indicates that the request was accepted. It does not independently prove that a PipelineRun was created or that the pipeline completed successfully.

Check for a new PipelineRun:

```bash
tkn pipelinerun list
```

Inspect the PipelineRun status and logs to determine whether execution succeeded.

## 6. Troubleshooting

| Symptom | What to check |
|---|---|
| HTTP 401 or signature mismatch | Verify that the supplied webhook secret matches the `secretToken` value in `github-webhook-secret`. Ensure the request body was not modified after signing. |
| HTTP 202 but no PipelineRun appears | Check EventListener logs, Trigger configuration, CEL filtering, TriggerTemplate parameters, and ServiceAccount permissions. |
| GitHub reports a failed delivery | Open **Settings → Webhooks → Recent Deliveries** and inspect the response and delivery details. |
| EventListener Route returns 404 | Check the Route, EventListener Service, and EventListener pods. |
| PipelineRun starts but cloning fails | Verify the repository URL and ensure the requested commit SHA exists in the remote repository. |
| PipelineRun fails during testing | Check the database resources and the `customers-test-db` Secret. |
| PipelineRun fails during image building | Check Buildah permissions and image registry access. |
| PipelineRun fails during deployment | Check the deployment resources, OpenShift permissions, and image availability. |

Useful inspection commands:

```bash
kubectl get route customers-listener
kubectl get svc el-customers-listener
kubectl get pods -l eventlistener=customers-listener
kubectl get triggers
kubectl get pipelineruns
```

To inspect EventListener logs, first identify its pod:

```bash
kubectl get pods -l eventlistener=customers-listener
```

Then:

```bash
kubectl logs <eventlistener-pod-name>
```

To inspect a specific PipelineRun:

```bash
tkn pipelinerun describe <pipelinerun-name>
tkn pipelinerun logs <pipelinerun-name>
```

## Completion criteria

The webhook integration should only be considered verified when:

1. GitHub delivers a push event for a merge into `master`.
2. The EventListener receives and processes the event.
3. The Trigger accepts the event and creates a PipelineRun.
4. The PipelineRun executes the `customers-pipeline`.
5. The resulting pipeline status confirms successful execution.

A successful HTTP response alone is not sufficient evidence that the complete integration works.
