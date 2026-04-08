# Cloud Cost Optimizer
 
Intelligent AWS resource monitoring and cost optimization — automatically tracks EC2, S3, and RDS usage, forecasts spending trends, and surfaces actionable recommendations to reduce your cloud bill.

---
 
## Overview
 
Cloud Cost Optimizer is a full-stack AWS monitoring platform built for teams who want visibility into their cloud spending without the enterprise price tag. It continuously collects metrics from AWS resources, stores them in DynamoDB, and exposes a REST API that powers a real-time Next.js dashboard with cost forecasting and optimization recommendations.
 
---
 
## Features
 
- **Real-time Metrics** — Collects EC2 CPU/memory utilization, S3 storage consumption, and resource metadata via AWS SDK
- **Cost Forecasting** — Uses exponential smoothing with rule-based adjustments to project future spending based on historical trends
- **Recommendation Engine** — Flags underutilized instances, oversized storage, and idle resources with actionable suggestions
- **REST API** — FastAPI backend with structured endpoints for metrics, forecasts, and recommendations
- **Interactive Dashboard** — Next.js frontend with live charts, resource breakdowns, and cost summaries
- **Serverless Data Collection** — S3-triggered Lambda functions for automated storage metric ingestion
- **Zero-cost Infrastructure** — Designed to run within AWS Free Tier limits for development and small-scale use
 
---
 
## Tech Stack
- **Frontend**: Next.js, TypeScript, Tailwind CSS 
- **Backend**: Python, FastAPI 
- **Database**: AWS DynamoDB 
- **Cloud**: AWS EC2, S3, Lambda, IAM 
- **Deployment**: Vercel (frontend), AWS EC2 (backend) 
 
---
## Prerequisites
 
- Python 3.10+
- Node.js 18+
- AWS account with IAM credentials configured
- AWS CLI installed and configured (`aws configure`)
 
 
 
