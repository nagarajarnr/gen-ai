#!/usr/bin/env python3
"""
Fine-tuning script for Google Gemini/Vertex AI models.

This script demonstrates the complete fine-tuning workflow:
1. Extract Q&A pairs from audit logs
2. Format data for Vertex AI
3. Upload to GCS
4. Start fine-tune job
5. Monitor job progress
6. Register trained model

Prerequisites:
- Google Cloud Project with Vertex AI enabled
- Service account with necessary permissions
- GCS bucket for training data
- GEMINI_PROJECT, GEMINI_CREDENTIALS_PATH environment variables set
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from motor.motor_asyncio import AsyncIOMotorClient

from app.config import get_settings

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

settings = get_settings()


class GeminiFineTuner:
    """Fine-tuning manager for Gemini/Vertex AI models."""

    def __init__(self, project_id: str, location: str, credentials_path: str, gcs_bucket: str):
        """
        Initialize fine-tuner.

        Args:
            project_id: GCP project ID
            location: GCP region (e.g., 'us-central1')
            credentials_path: Path to service account JSON
            gcs_bucket: GCS bucket name for training data
        """
        self.project_id = project_id
        self.location = location
        self.credentials_path = credentials_path
        self.gcs_bucket = gcs_bucket

        logger.info(f"Initialized GeminiFineTuner (project: {project_id}, location: {location})")

        # In production, initialize Vertex AI client:
        """
        from google.cloud import aiplatform
        from google.oauth2 import service_account

        credentials = service_account.Credentials.from_service_account_file(
            credentials_path
        )

        aiplatform.init(
            project=project_id,
            location=location,
            credentials=credentials
        )

        self.aiplatform = aiplatform
        """

    async def extract_training_data(
        self, mongo_uri: str, db_name: str, min_samples: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Extract Q&A pairs from audit logs for training.

        Args:
            mongo_uri: MongoDB connection string
            db_name: Database name
            min_samples: Minimum number of samples required

        Returns:
            List of training examples
        """
        logger.info("Extracting training data from audit logs...")

        client = AsyncIOMotorClient(mongo_uri)
        db = client[db_name]

        # Fetch Q&A queries from audit logs
        cursor = db.audit_logs.find(
            {
                "event_type": "qa_query",
                "confidence": {"$gte": 0.7},  # Only high-confidence answers
            }
        ).sort("timestamp", -1)

        audit_entries = await cursor.to_list(length=None)
        client.close()

        logger.info(f"Found {len(audit_entries)} Q&A entries")

        if len(audit_entries) < min_samples:
            logger.warning(
                f"Only {len(audit_entries)} samples found, less than minimum {min_samples}"
            )

        # Format for Vertex AI training
        training_examples = []
        for entry in audit_entries:
            example = {
                "messages": [
                    {
                        "role": "user",
                        "content": entry["query"]
                    },
                    {
                        "role": "assistant",
                        "content": entry["answer"]
                    }
                ],
                "metadata": {
                    "confidence": entry["confidence"],
                    "timestamp": entry["timestamp"].isoformat() if hasattr(entry["timestamp"], 'isoformat') else str(entry["timestamp"]),
                    "num_citations": entry.get("num_citations", 0)
                }
            }
            training_examples.append(example)

        logger.info(f"Prepared {len(training_examples)} training examples")
        return training_examples

    def save_training_data(
        self, examples: List[Dict[str, Any]], output_path: str
    ) -> str:
        """
        Save training data in JSONL format for Vertex AI.

        Args:
            examples: Training examples
            output_path: Output file path

        Returns:
            Path to saved file
        """
        logger.info(f"Saving training data to {output_path}")

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, 'w') as f:
            for example in examples:
                f.write(json.dumps(example) + '\n')

        logger.info(f"Saved {len(examples)} examples to {output_path}")
        return output_path

    def upload_to_gcs(self, local_path: str, gcs_path: str) -> str:
        """
        Upload training data to Google Cloud Storage.

        Args:
            local_path: Local file path
            gcs_path: GCS destination path (without gs:// prefix)

        Returns:
            Full GCS URI
        """
        logger.info(f"Uploading {local_path} to gs://{self.gcs_bucket}/{gcs_path}")

        # Production implementation:
        """
        from google.cloud import storage

        storage_client = storage.Client.from_service_account_json(
            self.credentials_path
        )
        bucket = storage_client.bucket(self.gcs_bucket)
        blob = bucket.blob(gcs_path)

        blob.upload_from_filename(local_path)

        gcs_uri = f"gs://{self.gcs_bucket}/{gcs_path}"
        logger.info(f"Uploaded to {gcs_uri}")
        return gcs_uri
        """

        # Placeholder
        gcs_uri = f"gs://{self.gcs_bucket}/{gcs_path}"
        logger.info(f"[PLACEHOLDER] Would upload to {gcs_uri}")
        return gcs_uri

    def start_fine_tune_job(
        self, training_data_uri: str, base_model: str = "gemini-1.5-pro", epochs: int = 3
    ) -> str:
        """
        Start a fine-tuning job on Vertex AI.

        Args:
            training_data_uri: GCS URI to training data
            base_model: Base model to fine-tune
            epochs: Number of training epochs

        Returns:
            Job ID
        """
        logger.info(f"Starting fine-tune job for {base_model}")
        logger.info(f"Training data: {training_data_uri}")
        logger.info(f"Epochs: {epochs}")

        # Production implementation:
        """
        from vertexai.preview.tuning import sft

        # Create supervised fine-tuning job
        sft_job = sft.train(
            source_model=base_model,
            train_dataset=training_data_uri,
            epochs=epochs,
            learning_rate=0.0001,
            tuning_job_location=self.location,
        )

        job_id = sft_job.name
        logger.info(f"Fine-tune job started: {job_id}")

        return job_id
        """

        # Placeholder
        job_id = f"fine-tune-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
        logger.info(f"[PLACEHOLDER] Fine-tune job ID: {job_id}")
        return job_id

    def monitor_job(self, job_id: str, poll_interval: int = 60) -> Dict[str, Any]:
        """
        Monitor fine-tuning job progress.

        Args:
            job_id: Job identifier
            poll_interval: Polling interval in seconds

        Returns:
            Job status dictionary
        """
        logger.info(f"Monitoring job {job_id}...")

        # Production implementation:
        """
        from vertexai.preview.tuning import sft

        job = sft.SupervisedTuningJob(job_id)

        while True:
            job.refresh()
            state = job.state

            logger.info(f"Job state: {state}")

            if state == aiplatform.gapic.JobState.JOB_STATE_SUCCEEDED:
                logger.info("Fine-tuning completed successfully!")
                return {
                    "status": "completed",
                    "model_name": job.tuned_model_name,
                    "endpoint": job.tuned_model_endpoint_name,
                }
            elif state == aiplatform.gapic.JobState.JOB_STATE_FAILED:
                logger.error(f"Fine-tuning failed: {job.error}")
                return {
                    "status": "failed",
                    "error": str(job.error)
                }
            elif state == aiplatform.gapic.JobState.JOB_STATE_CANCELLED:
                logger.warning("Fine-tuning was cancelled")
                return {
                    "status": "cancelled"
                }

            time.sleep(poll_interval)
        """

        # Placeholder
        logger.info("[PLACEHOLDER] In production, this would poll job status until completion")
        return {
            "status": "completed",
            "model_name": f"accord-compliance-{job_id}",
            "endpoint": f"projects/{self.project_id}/locations/{self.location}/endpoints/placeholder",
        }

    async def register_model(
        self, model_id: str, model_name: str, performance_metrics: Dict[str, float],
        mongo_uri: str, db_name: str
    ) -> str:
        """
        Register fine-tuned model in model registry.

        Args:
            model_id: Unique model identifier
            model_name: Human-readable model name
            performance_metrics: Model performance metrics
            mongo_uri: MongoDB connection string
            db_name: Database name

        Returns:
            Registry entry ID
        """
        logger.info(f"Registering model in registry: {model_name}")

        client = AsyncIOMotorClient(mongo_uri)
        db = client[db_name]

        registry_entry = {
            "_id": f"model-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
            "model_id": model_id,
            "model_type": "qa",
            "model_name": model_name,
            "model_provider": "vertex_ai",
            "model_config": {
                "base_model": "gemini-1.5-pro",
                "fine_tuned": True,
                "training_date": datetime.utcnow().isoformat(),
            },
            "performance_metrics": performance_metrics,
            "status": "active",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        result = await db.model_registry.insert_one(registry_entry)
        client.close()

        logger.info(f"Model registered with ID: {result.inserted_id}")
        return str(result.inserted_id)


async def main():
    """Main fine-tuning workflow."""
    parser = argparse.ArgumentParser(description="Fine-tune Gemini model for compliance Q&A")
    parser.add_argument(
        "--dataset-source",
        default="audit",
        choices=["audit", "file"],
        help="Data source: 'audit' (from logs) or 'file' (from JSONL)"
    )
    parser.add_argument(
        "--input-file",
        help="Input JSONL file (if dataset-source=file)"
    )
    parser.add_argument(
        "--min-samples",
        type=int,
        default=100,
        help="Minimum number of training samples"
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=3,
        help="Number of training epochs"
    )
    parser.add_argument(
        "--base-model",
        default="gemini-1.5-pro",
        help="Base model to fine-tune"
    )
    parser.add_argument(
        "--output-dir",
        default=settings.fine_tune_dataset_path,
        help="Output directory for training data"
    )

    args = parser.parse_args()

    # Validate configuration
    if not settings.gemini_project:
        logger.error("GEMINI_PROJECT not set. Please configure your GCP project.")
        sys.exit(1)

    if not settings.gcs_bucket_name:
        logger.error("GCS_BUCKET_NAME not set. Please configure a GCS bucket.")
        sys.exit(1)

    logger.info("="*60)
    logger.info("Accord AI Compliance - Gemini Fine-Tuning")
    logger.info("="*60)
    logger.info(f"Project: {settings.gemini_project}")
    logger.info(f"Location: {settings.gemini_location}")
    logger.info(f"Base model: {args.base_model}")
    logger.info(f"Min samples: {args.min_samples}")
    logger.info(f"Epochs: {args.epochs}")
    logger.info("="*60)

    # Initialize fine-tuner
    fine_tuner = GeminiFineTuner(
        project_id=settings.gemini_project,
        location=settings.gemini_location,
        credentials_path=settings.gemini_credentials_path,
        gcs_bucket=settings.gcs_bucket_name,
    )

    # Step 1: Get training data
    if args.dataset_source == "audit":
        training_data = await fine_tuner.extract_training_data(
            mongo_uri=settings.mongo_uri,
            db_name=settings.mongo_db_name,
            min_samples=args.min_samples,
        )
    else:
        logger.info(f"Loading training data from {args.input_file}")
        with open(args.input_file, 'r') as f:
            training_data = [json.loads(line) for line in f]

    if not training_data:
        logger.error("No training data available. Exiting.")
        sys.exit(1)

    # Step 2: Save training data
    timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    local_path = f"{args.output_dir}/training_data_{timestamp}.jsonl"
    fine_tuner.save_training_data(training_data, local_path)

    # Step 3: Upload to GCS
    gcs_path = f"finetune/training_data_{timestamp}.jsonl"
    training_data_uri = fine_tuner.upload_to_gcs(local_path, gcs_path)

    # Step 4: Start fine-tune job
    job_id = fine_tuner.start_fine_tune_job(
        training_data_uri=training_data_uri,
        base_model=args.base_model,
        epochs=args.epochs,
    )

    # Step 5: Monitor job
    result = fine_tuner.monitor_job(job_id)

    if result["status"] == "completed":
        logger.info("✓ Fine-tuning completed successfully!")

        # Step 6: Register model
        model_id = result["model_name"]
        await fine_tuner.register_model(
            model_id=model_id,
            model_name=f"Accord Compliance Fine-Tuned {timestamp}",
            performance_metrics={"training_samples": len(training_data)},
            mongo_uri=settings.mongo_uri,
            db_name=settings.mongo_db_name,
        )

        logger.info("="*60)
        logger.info("Fine-tuning complete!")
        logger.info(f"Model ID: {model_id}")
        logger.info(f"To use this model, update your .env:")
        logger.info(f"  MODEL_ADAPTER=gemini_vertex")
        logger.info(f"  GEMINI_MODEL_NAME={model_id}")
        logger.info("="*60)
    else:
        logger.error(f"Fine-tuning failed with status: {result['status']}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

