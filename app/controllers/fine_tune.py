"""Fine-tuning controller for Gemini models with image support."""

import asyncio
import json
import logging
import os
import shutil
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.config import get_settings
from app.models.fine_tune import (
    FineTuneDataSource,
    FineTuneJob,
    FineTuneRequest,
    FineTuneStatus,
    ImageTrainingData,
)

logger = logging.getLogger(__name__)
settings = get_settings()


class FineTuneController:
    """Controller for fine-tuning operations."""

    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize fine-tuning controller.

        Args:
            db: MongoDB database instance
        """
        self.db = db
        self.storage_path = Path(settings.storage_path) / "finetune"
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # GCP configuration
        self.gcs_bucket = settings.gcs_bucket_name
        self.gemini_project = settings.gemini_project
        self.gemini_location = settings.gemini_location

    async def upload_image_for_training(
        self, file_path: str, filename: str, prompt: str, expected_output: str
    ) -> Dict[str, Any]:
        """
        Upload an image for fine-tuning training data.

        Args:
            file_path: Path to image file
            filename: Original filename
            prompt: Training prompt for this image
            expected_output: Expected model output

        Returns:
            Dictionary with upload details
        """
        try:
            image_id = str(uuid.uuid4())
            logger.info(f"Uploading image for training: {filename} ({image_id})")

            # Validate image
            is_valid, error_msg = await self.image_processor.validate_image(file_path)
            if not is_valid:
                raise ValueError(f"Invalid image: {error_msg}")

            # Get image info
            image_info = await self.image_processor.get_image_info(file_path)

            # Move to training storage
            file_ext = Path(filename).suffix
            storage_filename = f"{image_id}{file_ext}"
            storage_file_path = self.storage_path / "images" / storage_filename

            storage_file_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(file_path, storage_file_path)

            # Upload to GCS (if configured)
            gcs_uri = None
            if self.gcs_bucket:
                gcs_uri = await self._upload_to_gcs(
                    str(storage_file_path), f"finetune/images/{storage_filename}"
                )

            # Store metadata in database
            training_image = {
                "_id": image_id,
                "filename": filename,
                "storage_path": str(storage_file_path),
                "gcs_uri": gcs_uri,
                "prompt": prompt,
                "expected_output": expected_output,
                "image_info": image_info,
                "uploaded_at": datetime.utcnow(),
                "used_in_jobs": [],
            }

            await self.db.training_images.insert_one(training_image)

            logger.info(f"Image uploaded successfully: {image_id}")

            return {
                "image_id": image_id,
                "filename": filename,
                "local_path": str(storage_file_path),
                "gcs_uri": gcs_uri,
                "size_bytes": image_info.get("size_bytes", 0),
                "format": image_info.get("format", "unknown"),
            }

        except Exception as e:
            logger.error(f"Failed to upload image for training: {e}")
            raise

    async def start_fine_tune_job(
        self, request: FineTuneRequest, user_id: Optional[str] = None
    ) -> str:
        """
        Start a fine-tuning job.

        Args:
            request: Fine-tuning request parameters
            user_id: User ID initiating the job

        Returns:
            Job ID
        """
        try:
            job_id = str(uuid.uuid4())
            logger.info(f"Starting fine-tuning job: {request.job_name} ({job_id})")

            # Create job record
            job = FineTuneJob(
                _id=job_id,
                job_name=request.job_name,
                status=FineTuneStatus.PENDING,
                base_model=request.base_model,
                data_source=request.data_source.value,
                epochs=request.epochs,
                learning_rate=request.learning_rate,
                batch_size=request.batch_size,
                created_by=user_id,
                description=request.description,
                tags=request.tags,
            )

            # Save job to database
            await self.db.fine_tune_jobs.insert_one(job.dict(by_alias=True))

            # Start async training process
            asyncio.create_task(self._execute_fine_tune_job(job_id, request))

            logger.info(f"Fine-tuning job created: {job_id}")

            return job_id

        except Exception as e:
            logger.error(f"Failed to start fine-tuning job: {e}")
            raise

    async def _execute_fine_tune_job(
        self, job_id: str, request: FineTuneRequest
    ) -> None:
        """
        Execute fine-tuning job asynchronously.

        Args:
            job_id: Job ID
            request: Fine-tuning request
        """
        try:
            # Update status: Preparing data
            await self._update_job_status(
                job_id, FineTuneStatus.PREPARING_DATA, "Preparing training data"
            )

            # Step 1: Collect training data
            training_data = await self._prepare_training_data(request)

            if len(training_data) < request.min_samples:
                raise ValueError(
                    f"Insufficient training data: {len(training_data)} < {request.min_samples}"
                )

            # Update job with sample count
            await self.db.fine_tune_jobs.update_one(
                {"_id": job_id},
                {
                    "$set": {
                        "num_training_samples": len(training_data),
                        "num_image_samples": sum(
                            1 for item in training_data if "image" in item
                        ),
                    }
                },
            )

            # Step 2: Upload to GCS
            await self._update_job_status(
                job_id, FineTuneStatus.UPLOADING_TO_GCS, "Uploading dataset to GCS"
            )

            gcs_dataset_uri = await self._upload_dataset_to_gcs(job_id, training_data)

            await self.db.fine_tune_jobs.update_one(
                {"_id": job_id}, {"$set": {"gcs_dataset_uri": gcs_dataset_uri}}
            )

            # Step 3: Start training
            await self._update_job_status(
                job_id, FineTuneStatus.TRAINING, "Training model on Vertex AI"
            )

            tuned_model_id, endpoint = await self._start_vertex_ai_training(
                job_id, request, gcs_dataset_uri
            )

            # Step 4: Complete
            await self._update_job_status(
                job_id,
                FineTuneStatus.COMPLETED,
                "Fine-tuning completed successfully",
                tuned_model_id=tuned_model_id,
                endpoint=endpoint,
            )

            # Register model in registry
            await self._register_model(job_id, tuned_model_id, request)

            logger.info(f"Fine-tuning job completed: {job_id}")

        except Exception as e:
            logger.error(f"Fine-tuning job failed: {e}")
            await self._update_job_status(
                job_id, FineTuneStatus.FAILED, f"Job failed: {str(e)}"
            )

    async def _prepare_training_data(
        self, request: FineTuneRequest
    ) -> List[Dict[str, Any]]:
        """Prepare training data from various sources."""
        training_data = []

        # Source 1: Audit logs (Q&A pairs)
        if request.data_source in [
            FineTuneDataSource.AUDIT_LOGS,
            FineTuneDataSource.MIXED,
        ]:
            audit_data = await self._extract_from_audit_logs(
                min_confidence=request.min_confidence
            )
            training_data.extend(audit_data)
            logger.info(f"Collected {len(audit_data)} samples from audit logs")

        # Source 2: Uploaded images
        if request.include_images and request.image_training_data:
            image_data = await self._prepare_image_training_data(
                request.image_training_data
            )
            training_data.extend(image_data)
            logger.info(f"Collected {len(image_data)} image training samples")

        # Source 3: Existing documents
        if request.data_source in [
            FineTuneDataSource.EXISTING_DOCUMENTS,
            FineTuneDataSource.MIXED,
        ]:
            doc_data = await self._extract_from_documents()
            training_data.extend(doc_data)
            logger.info(f"Collected {len(doc_data)} samples from documents")

        return training_data

    async def _extract_from_audit_logs(
        self, min_confidence: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Extract training samples from audit logs."""
        cursor = self.db.audit_logs.find(
            {
                "event_type": "qa_query",
                "confidence": {"$gte": min_confidence},
            }
        ).sort("timestamp", -1)

        audit_entries = await cursor.to_list(length=None)

        training_samples = []
        for entry in audit_entries:
            sample = {
                "messages": [
                    {"role": "user", "content": entry["query"]},
                    {"role": "assistant", "content": entry["answer"]},
                ],
                "metadata": {
                    "confidence": entry["confidence"],
                    "source": "audit_log",
                    "timestamp": entry["timestamp"].isoformat()
                    if hasattr(entry["timestamp"], "isoformat")
                    else str(entry["timestamp"]),
                },
            }
            training_samples.append(sample)

        return training_samples

    async def _prepare_image_training_data(
        self, image_data: List[ImageTrainingData]
    ) -> List[Dict[str, Any]]:
        """Prepare image training examples."""
        training_samples = []

        for img_data in image_data:
            # Upload image to GCS if not already uploaded
            if not img_data.gcs_uri and self.gcs_bucket:
                filename = Path(img_data.image_path).name
                gcs_uri = await self._upload_to_gcs(
                    img_data.image_path, f"finetune/images/{filename}"
                )
                img_data.gcs_uri = gcs_uri

            sample = {
                "messages": [
                    {
                        "role": "user",
                        "content": img_data.prompt,
                        "image_uri": img_data.gcs_uri or img_data.image_path,
                    },
                    {"role": "assistant", "content": img_data.expected_output},
                ],
                "metadata": {
                    "source": "uploaded_image",
                    "image_path": img_data.image_path,
                    "gcs_uri": img_data.gcs_uri,
                    **img_data.metadata,
                },
            }
            training_samples.append(sample)

        return training_samples

    async def _extract_from_documents(self) -> List[Dict[str, Any]]:
        """Extract training samples from existing documents."""
        # This could generate synthetic Q&A pairs from documents
        # For now, return empty list (implement based on requirements)
        return []

    async def _upload_to_gcs(self, local_path: str, gcs_path: str) -> str:
        """
        Upload file to Google Cloud Storage.

        Args:
            local_path: Local file path
            gcs_path: GCS destination path

        Returns:
            GCS URI
        """
        if not self.gcs_bucket:
            logger.warning("GCS bucket not configured, skipping upload")
            return f"local://{local_path}"

        logger.info(f"Uploading to GCS: {gcs_path}")

        # Production implementation:
        """
        from google.cloud import storage
        
        client = storage.Client.from_service_account_json(
            settings.gemini_credentials_path
        )
        bucket = client.bucket(self.gcs_bucket)
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

    async def _upload_dataset_to_gcs(
        self, job_id: str, training_data: List[Dict[str, Any]]
    ) -> str:
        """Upload training dataset to GCS in JSONL format."""
        # Save to local file first
        dataset_filename = f"training_data_{job_id}.jsonl"
        local_dataset_path = self.storage_path / "datasets" / dataset_filename
        local_dataset_path.parent.mkdir(parents=True, exist_ok=True)

        with open(local_dataset_path, "w") as f:
            for sample in training_data:
                f.write(json.dumps(sample) + "\n")

        logger.info(
            f"Saved dataset locally: {local_dataset_path} ({len(training_data)} samples)"
        )

        # Upload to GCS
        gcs_path = f"finetune/datasets/{dataset_filename}"
        gcs_uri = await self._upload_to_gcs(str(local_dataset_path), gcs_path)

        return gcs_uri

    async def _start_vertex_ai_training(
        self, job_id: str, request: FineTuneRequest, dataset_uri: str
    ) -> Tuple[str, str]:
        """
        Start Vertex AI training job.

        Args:
            job_id: Job ID
            request: Training request
            dataset_uri: GCS URI of training dataset

        Returns:
            Tuple of (tuned_model_id, endpoint)
        """
        logger.info(f"Starting Vertex AI training for job {job_id}")

        if not self.gemini_project:
            logger.warning("Vertex AI not configured, using placeholder")
            return f"model-{job_id}", f"endpoint-{job_id}"

        # Production implementation:
        """
        from vertexai.preview.tuning import sft
        from google.cloud import aiplatform
        
        aiplatform.init(
            project=self.gemini_project,
            location=self.gemini_location,
            credentials=settings.gemini_credentials_path
        )
        
        # Start supervised fine-tuning job
        sft_job = sft.train(
            source_model=request.base_model,
            train_dataset=dataset_uri,
            epochs=request.epochs,
            learning_rate=request.learning_rate,
            tuning_job_location=self.gemini_location,
        )
        
        # Monitor job
        while True:
            sft_job.refresh()
            state = sft_job.state
            
            if state == aiplatform.gapic.JobState.JOB_STATE_SUCCEEDED:
                logger.info("Training completed successfully")
                return sft_job.tuned_model_name, sft_job.tuned_model_endpoint_name
            
            elif state in [
                aiplatform.gapic.JobState.JOB_STATE_FAILED,
                aiplatform.gapic.JobState.JOB_STATE_CANCELLED
            ]:
                raise Exception(f"Training failed: {sft_job.error}")
            
            await asyncio.sleep(60)  # Poll every minute
        """

        # Placeholder
        logger.info("[PLACEHOLDER] Would start Vertex AI training")
        await asyncio.sleep(2)  # Simulate training time

        tuned_model_id = f"{request.base_model}-finetune-{job_id[:8]}"
        endpoint = f"projects/{self.gemini_project}/locations/{self.gemini_location}/endpoints/{job_id}"

        return tuned_model_id, endpoint

    async def _register_model(
        self, job_id: str, model_id: str, request: FineTuneRequest
    ) -> None:
        """Register fine-tuned model in model registry."""
        registry_entry = {
            "_id": f"model-{job_id}",
            "model_id": model_id,
            "model_type": "qa",
            "model_name": request.job_name,
            "model_provider": "vertex_ai",
            "model_config": {
                "base_model": request.base_model,
                "fine_tuned": True,
                "epochs": request.epochs,
                "learning_rate": request.learning_rate,
                "batch_size": request.batch_size,
            },
            "performance_metrics": {},
            "status": "active",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "fine_tune_job_id": job_id,
            "description": request.description,
            "tags": request.tags,
        }

        await self.db.model_registry.insert_one(registry_entry)
        logger.info(f"Registered model in registry: {model_id}")

    async def _update_job_status(
        self,
        job_id: str,
        status: FineTuneStatus,
        message: str,
        tuned_model_id: Optional[str] = None,
        endpoint: Optional[str] = None,
    ) -> None:
        """Update job status in database."""
        update_data = {
            "status": status.value,
            "updated_at": datetime.utcnow(),
        }

        if status == FineTuneStatus.TRAINING:
            update_data["started_at"] = datetime.utcnow()

        if status == FineTuneStatus.COMPLETED:
            update_data["completed_at"] = datetime.utcnow()
            if tuned_model_id:
                update_data["tuned_model_id"] = tuned_model_id
            if endpoint:
                update_data["tuned_model_endpoint"] = endpoint

        if status == FineTuneStatus.FAILED:
            update_data["error_message"] = message
            update_data["completed_at"] = datetime.utcnow()

        await self.db.fine_tune_jobs.update_one({"_id": job_id}, {"$set": update_data})

        logger.info(f"Job {job_id} status updated: {status.value} - {message}")

    async def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get fine-tuning job status."""
        job = await self.db.fine_tune_jobs.find_one({"_id": job_id})
        return job

    async def list_jobs(
        self, limit: int = 20, skip: int = 0, status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List fine-tuning jobs."""
        filter_query = {}
        if status:
            filter_query["status"] = status

        cursor = (
            self.db.fine_tune_jobs.find(filter_query)
            .sort("created_at", -1)
            .skip(skip)
            .limit(limit)
        )

        jobs = await cursor.to_list(length=limit)
        return jobs

    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a fine-tuning job."""
        job = await self.db.fine_tune_jobs.find_one({"_id": job_id})

        if not job:
            return False

        if job["status"] in ["completed", "failed", "cancelled"]:
            return False

        await self._update_job_status(
            job_id, FineTuneStatus.CANCELLED, "Job cancelled by user"
        )

        return True

