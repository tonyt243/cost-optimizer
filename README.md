# Scalar - AWS Cost Optimization Platform

Intelligent AWS cost monitoring and optimization platform that automatically tracks EC2 and S3 usage, analyzes spending patterns, and generates actionable recommendations to reduce your cloud bill.

---

## Overview

Scalar is a serverless AWS monitoring platform that provides real-time visibility into cloud infrastructure costs. It automatically collects metrics, calculates daily costs, and identifies optimization opportunities through AI-powered recommendations—all within AWS Free Tier limits.

---

## Features

- **Automated Metrics Collection** — Hourly EC2 CPU/network metrics and S3 storage data via AWS CloudWatch
- **Cost Analysis Engine** — Daily cost calculations for EC2 instances and S3 buckets with historical tracking
- **AI-Powered Recommendations** — Detects underutilized instances (CPU < 10%) and idle resources with savings estimates
- **REST API** — FastAPI backend with endpoints for metrics, cost summaries, trends, and recommendations
- **Real-Time Dashboard** — Next.js frontend with live charts, cost breakdowns, and optimization insights
- **Serverless Architecture** — Lambda functions triggered by EventBridge for fully automated data pipeline
- **Cost-Efficient** — Runs entirely within AWS Free Tier for development and small-scale deployments

---

## Tech Stack

**Frontend**: Next.js 14, React, TypeScript, Tailwind CSS, Recharts  
**Backend**: Python 3.12, FastAPI, Boto3, Uvicorn  
**Database**: AWS DynamoDB (3 tables: ResourceMetrics, CostAnalysis, Recommendations)  
**Cloud Infrastructure**: AWS Lambda, EC2, S3, CloudWatch, EventBridge, IAM  
**Deployment**: Vercel (frontend), AWS EC2 (backend API)

---

## Prerequisites

- AWS Account with administrative access
- Python 3.12+
- Node.js 18+
- AWS CLI installed and configured (`aws configure`)
- Git

---

## Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/tonyt243/cost-optimizer.git
cd cost-optimizer
```

### 2. Backend Setup (Local Development)
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Backend runs at: `http://localhost:8000`  
API docs: `http://localhost:8000/docs`

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

Frontend runs at: `http://localhost:3000`

### 4. AWS Infrastructure Setup

**Create DynamoDB Tables:**
- `CostOptimizer-ResourceMetrics` (PK: resource_id, SK: timestamp)
- `CostOptimizer-CostAnalysis` (PK: analysis_id, SK: date)
- `CostOptimizer-Recommendations` (PK: recommendation_id, SK: created_at)

**Deploy Lambda Functions:**
- EC2 Metrics Collector (hourly trigger)
- S3 Metrics Collector (6-hour trigger)
- Cost Analysis Engine (daily at 1 AM UTC)
- Recommendation Engine (daily at 2 AM UTC)

**Configure IAM Roles:**
- Lambda execution roles with CloudWatch and DynamoDB permissions
- EC2 instance role for API server

  ## Project Structure
```
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI application
│   │   └── metrics.py       # API endpoints
│   └── requirements.txt
├── frontend/
│   ├── app/
│   │   └── page.tsx         # Dashboard UI
│   ├── package.json
│   └── tailwind.config.ts
├── lambda/
│   ├── ec2_metrics_collector/
│   ├── s3_metrics_collector/
│   ├── cost_analysis_engine/
│   └── recommendation_engine/
└── README.md
```
  

---

## Architecture
