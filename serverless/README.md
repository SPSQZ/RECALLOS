# ⚙️ Nebius Serverless Jobs — RecallOS Background Worker

This directory contains the deployment configuration and background task runner for **Nebius Serverless Jobs**, fulfilling the **Member 1 (Cloud & Inference Lead)** hackathon requirement.

---

## 📌 Architecture Overview

Nebius Serverless Jobs execute decoupled asynchronous tasks without maintaining an idle virtual machine:
1. **Batch Memory & Reasoning Auditing**: Runs periodic latency and quality profiling over user conversations.
2. **Dynamic Model Routing Profiler**: Executes offline evaluation comparing **Nemotron Nano/Super** vs. **Nemotron 3 Ultra**.
3. **Artifact Generation**: Persists structured JSON audit reports to cloud object storage.

---

## 🚀 Deployment Instructions

### 1. Build and Push Container Image to Nebius Container Registry
```bash
# Log in to Nebius Container Registry
nebius cr login

# Build image
docker build -t cr.nebius.com/recallos/batch-profiler:v1.0 .

# Push image
docker push cr.nebius.com/recallos/batch-profiler:v1.0
```

### 2. Create the Serverless Job
```bash
nebius serverless job create \
  --name recallos-batch-profiler \
  --image cr.nebius.com/recallos/batch-profiler:v1.0 \
  --cores 1 \
  --memory 2GB \
  --environment NEBIUS_BASE_URL="https://api.tokenfactory.nebius.com/v1/"
```

### 3. Trigger Job Execution
```bash
nebius serverless job execute --name recallos-batch-profiler
```

### 4. Inspect Execution Logs
```bash
nebius serverless job logs --name recallos-batch-profiler --follow
```

---

## 🧪 Local Simulation
To test the serverless worker locally without cloud charges:
```bash
python batch_benchmark_job.py
```
Output artifacts are saved to `./job_artifacts/serverless_results_<job_id>.json`.

