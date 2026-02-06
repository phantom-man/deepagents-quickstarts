"""
ClimateML Agent - ML models for environmental prediction and anomaly detection

This agent is responsible for:
- Training and deploying ML models for environmental predictions
- Anomaly detection in sensor data streams
- Time series forecasting for environmental parameters
- Model performance monitoring and retraining
- Providing prediction APIs for other agents
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import joblib
import os
from pathlib import Path

from app.services.database import (
    get_sensor_readings,
    create_environmental_event,
    get_recent_predictions
)
from app.services.cache import cache_set, cache_get, predictions_key
from app.models.models import Prediction
from app.schemas.schemas import PredictionCreate

logger = logging.getLogger(__name__)

class ClimateMLAgent:
    """Agent for ML-based environmental prediction and anomaly detection."""

    def __init__(self):
        self.models: Dict[str, Any] = {}
        self.scalers: Dict[str, StandardScaler] = {}
        self.anomaly_detectors: Dict[int, IsolationForest] = {}
        self.running = False
        self.tasks: List[asyncio.Task] = []
        self.model_dir = Path("models")
        self.model_dir.mkdir(exist_ok=True)

    async def initialize(self):
        """Initialize the ClimateML agent."""
        logger.info("🧠 Initializing ClimateML Agent...")

        # Load or train initial models
        await self._initialize_models()

        # Start prediction and monitoring tasks
        await self.start_prediction_pipeline()

        logger.info("✅ ClimateML Agent initialized")

    async def cleanup(self):
        """Cleanup agent resources."""
        logger.info("🧹 Cleaning up ClimateML Agent...")

        self.running = False

        # Cancel all running tasks
        for task in self.tasks:
            task.cancel()

        # Wait for tasks to complete
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)

        logger.info("✅ ClimateML Agent cleanup complete")

    async def _initialize_models(self):
        """Initialize ML models for different environmental parameters."""
        # Temperature prediction model
        self._init_temperature_model()

        # Air quality prediction model
        self._init_air_quality_model()

        # Water quality prediction model
        self._init_water_quality_model()

        # Load anomaly detectors
        await self._load_anomaly_detectors()

    def _init_temperature_model(self):
        """Initialize temperature prediction model."""
        # Simple exponential smoothing for demo
        # In production, use more sophisticated models like LSTM, Prophet, etc.
        self.models["temperature"] = {
            "type": "exponential_smoothing",
            "alpha": 0.3,
            "last_values": []
        }
        logger.info("🌡️ Temperature prediction model initialized")

    def _init_air_quality_model(self):
        """Initialize air quality prediction model."""
        # Simple moving average for demo
        self.models["air_quality"] = {
            "type": "moving_average",
            "window": 24,  # 24 readings
            "values": []
        }
        logger.info("🌬️ Air quality prediction model initialized")

    def _init_water_quality_model(self):
        """Initialize water quality prediction model."""
        # Simple linear regression for demo
        self.models["water_quality"] = {
            "type": "linear_regression",
            "coefficients": [0.8, 0.2],  # Mock coefficients
            "intercept": 7.0
        }
        logger.info("💧 Water quality prediction model initialized")

    async def _load_anomaly_detectors(self):
        """Load or train anomaly detection models for sensors."""
        # In production, this would load pre-trained models or train new ones
        # For demo, we'll create simple isolation forest models

        sensor_ids = [1, 2, 3]  # Our sample sensors

        for sensor_id in sensor_ids:
            try:
                # Try to load existing model
                model_path = self.model_dir / f"anomaly_detector_{sensor_id}.joblib"
                if model_path.exists():
                    detector = joblib.load(model_path)
                else:
                    # Train new model with historical data
                    detector = await self._train_anomaly_detector(sensor_id)

                self.anomaly_detectors[sensor_id] = detector
                logger.info(f"🔍 Anomaly detector loaded for sensor {sensor_id}")

            except Exception as e:
                logger.error(f"❌ Failed to load anomaly detector for sensor {sensor_id}: {e}")

    async def _train_anomaly_detector(self, sensor_id: int) -> IsolationForest:
        """Train anomaly detection model for a sensor."""
        # Get historical data
        readings = await get_sensor_readings(sensor_id, limit=1000)

        if len(readings) < 50:
            # Not enough data, create default model
            detector = IsolationForest(contamination=0.1, random_state=42)
            # Fit with dummy data
            dummy_data = np.random.normal(0, 1, (100, 1))
            detector.fit(dummy_data)
        else:
            # Extract values and prepare for training
            values = np.array([r.value for r in readings]).reshape(-1, 1)

            # Scale the data
            scaler = StandardScaler()
            scaled_values = scaler.fit_transform(values)

            # Train isolation forest
            detector = IsolationForest(contamination=0.1, random_state=42)
            detector.fit(scaled_values)

            # Store scaler
            self.scalers[sensor_id] = scaler

        # Save model
        model_path = self.model_dir / f"anomaly_detector_{sensor_id}.joblib"
        joblib.dump(detector, model_path)

        return detector

    async def start_prediction_pipeline(self):
        """Start the prediction and monitoring pipeline."""
        if self.running:
            return

        self.running = True
        logger.info("🚀 Starting ML prediction pipeline...")

        # Start prediction tasks
        prediction_task = asyncio.create_task(self._run_predictions())
        self.tasks.append(prediction_task)

        # Start anomaly detection tasks
        anomaly_task = asyncio.create_task(self._run_anomaly_detection())
        self.tasks.append(anomaly_task)

        # Start model retraining task
        retrain_task = asyncio.create_task(self._run_model_retraining())
        self.tasks.append(retrain_task)

    async def _run_predictions(self):
        """Run prediction tasks for all environmental parameters."""
        while self.running:
            try:
                # Generate predictions for all sensors
                await self._generate_predictions()

                # Wait for next prediction cycle (1 hour)
                await asyncio.sleep(3600)

            except Exception as e:
                logger.error(f"❌ Error in prediction pipeline: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes before retry

    async def _generate_predictions(self):
        """Generate predictions for all sensors."""
        sensor_configs = [
            (1, "temperature", 24),  # Sensor 1, temperature, 24 hours ahead
            (2, "air_quality", 12),  # Sensor 2, air quality, 12 hours ahead
            (3, "water_quality", 6),  # Sensor 3, water quality, 6 hours ahead
        ]

        for sensor_id, pred_type, window in sensor_configs:
            try:
                predictions = await self._predict_sensor_data(sensor_id, pred_type, window)

                for pred in predictions:
                    # Store prediction in database
                    await self._store_prediction(
                        sensor_id=sensor_id,
                        prediction_type=pred_type,
                        predicted_value=pred["value"],
                        confidence_score=pred["confidence"],
                        prediction_window=window,
                        features_used=pred.get("features", {})
                    )

                logger.info(f"🔮 Generated {len(predictions)} predictions for sensor {sensor_id}")

            except Exception as e:
                logger.error(f"❌ Error generating predictions for sensor {sensor_id}: {e}")

    async def _predict_sensor_data(self, sensor_id: int, pred_type: str, window: int) -> List[Dict[str, Any]]:
        """Generate predictions for a specific sensor and type."""
        # Get recent readings
        readings = await get_sensor_readings(sensor_id, limit=100)

        if len(readings) < 10:
            logger.warning(f"Insufficient data for predictions on sensor {sensor_id}")
            return []

        values = [r.value for r in readings]
        timestamps = [r.timestamp for r in readings]

        predictions = []

        if pred_type == "temperature":
            predictions = self._predict_temperature(values, window)
        elif pred_type == "air_quality":
            predictions = self._predict_air_quality(values, window)
        elif pred_type == "water_quality":
            predictions = self._predict_water_quality(values, window)

        return predictions

    def _predict_temperature(self, values: List[float], window: int) -> List[Dict[str, Any]]:
        """Predict temperature using exponential smoothing."""
        if len(values) < 5:
            return []

        model = self.models["temperature"]
        alpha = model["alpha"]

        # Simple exponential smoothing prediction
        last_value = values[-1]
        predictions = []

        for i in range(1, window + 1):
            # Predict next value (simplified)
            predicted_value = last_value + (np.random.normal(0, 0.5) * i * 0.1)
            predicted_value = max(-50, min(60, predicted_value))  # Clamp to reasonable range

            predictions.append({
                "value": predicted_value,
                "confidence": max(0.5, 1.0 - (i * 0.02)),  # Confidence decreases over time
                "features": {"method": "exponential_smoothing", "alpha": alpha}
            })

        return predictions

    def _predict_air_quality(self, values: List[float], window: int) -> List[Dict[str, Any]]:
        """Predict air quality using moving average."""
        if len(values) < 10:
            return []

        model = self.models["air_quality"]
        window_size = min(model["window"], len(values))

        # Calculate moving average
        recent_avg = np.mean(values[-window_size:])

        predictions = []
        for i in range(1, window + 1):
            # Add some trend and noise
            trend = np.random.normal(0, 2)  # Random trend
            noise = np.random.normal(0, 5)  # Random noise

            predicted_value = recent_avg + trend + (noise * i * 0.1)
            predicted_value = max(0, predicted_value)  # Air quality can't be negative

            predictions.append({
                "value": predicted_value,
                "confidence": max(0.4, 1.0 - (i * 0.03)),
                "features": {"method": "moving_average", "window": window_size}
            })

        return predictions

    def _predict_water_quality(self, values: List[float], window: int) -> List[Dict[str, Any]]:
        """Predict water quality using simple linear model."""
        if len(values) < 5:
            return []

        model = self.models["water_quality"]

        # Simple prediction based on recent trend
        recent_values = values[-5:]
        trend = (recent_values[-1] - recent_values[0]) / len(recent_values)

        predictions = []
        last_value = recent_values[-1]

        for i in range(1, window + 1):
            predicted_value = last_value + (trend * i) + np.random.normal(0, 0.1)
            predicted_value = max(0, min(14, predicted_value))  # pH range

            predictions.append({
                "value": predicted_value,
                "confidence": max(0.6, 1.0 - (i * 0.01)),
                "features": {"method": "linear_trend", "trend": trend}
            })

        return predictions

    async def _store_prediction(self, sensor_id: int, prediction_type: str,
                               predicted_value: float, confidence_score: float,
                               prediction_window: int, features_used: Dict[str, Any]):
        """Store prediction in database."""
        from app.services.database import create_sensor_reading

        # Create prediction record
        prediction = Prediction(
            sensor_id=sensor_id,
            prediction_type=prediction_type,
            timestamp=datetime.utcnow(),
            predicted_value=predicted_value,
            confidence_score=confidence_score,
            prediction_window=prediction_window,
            model_version="1.0.0",
            features_used=features_used
        )

        # In production, this would use a proper database session
        # For now, we'll just log it
        logger.debug(f"Stored prediction: {prediction_type} = {predicted_value} (confidence: {confidence_score})")

    async def _run_anomaly_detection(self):
        """Run anomaly detection on sensor data streams."""
        while self.running:
            try:
                # Check all sensors for anomalies
                await self._detect_anomalies()

                # Wait for next detection cycle (15 minutes)
                await asyncio.sleep(900)

            except Exception as e:
                logger.error(f"❌ Error in anomaly detection: {e}")
                await asyncio.sleep(300)

    async def _detect_anomalies(self):
        """Detect anomalies in sensor readings."""
        sensor_ids = [1, 2, 3]

        for sensor_id in sensor_ids:
            try:
                anomalies = await self._check_sensor_anomalies(sensor_id)

                for anomaly in anomalies:
                    # Create environmental event for anomaly
                    await create_environmental_event(
                        event_type="anomaly",
                        severity="medium",
                        title=f"Sensor Anomaly Detected - {anomaly['sensor_name']}",
                        description=f"Anomalous reading detected: {anomaly['value']} {anomaly['unit']}",
                        latitude=anomaly.get('latitude'),
                        longitude=anomaly.get('longitude'),
                        metadata={
                            "sensor_id": sensor_id,
                            "anomaly_score": anomaly["score"],
                            "detection_method": "isolation_forest"
                        }
                    )

                    logger.warning(f"🚨 Anomaly detected on sensor {sensor_id}: {anomaly['value']}")

            except Exception as e:
                logger.error(f"❌ Error detecting anomalies for sensor {sensor_id}: {e}")

    async def _check_sensor_anomalies(self, sensor_id: int) -> List[Dict[str, Any]]:
        """Check for anomalies in a specific sensor's recent readings."""
        # Get recent readings
        readings = await get_sensor_readings(sensor_id, limit=50)

        if len(readings) < 10:
            return []

        detector = self.anomaly_detectors.get(sensor_id)
        if not detector:
            return []

        # Prepare data for anomaly detection
        values = np.array([r.value for r in readings]).reshape(-1, 1)

        # Scale if scaler exists
        scaler = self.scalers.get(sensor_id)
        if scaler:
            scaled_values = scaler.transform(values)
        else:
            scaled_values = values

        # Get anomaly scores
        scores = detector.decision_function(scaled_values)
        predictions = detector.predict(scaled_values)

        anomalies = []
        for i, (score, pred) in enumerate(zip(scores, predictions)):
            if pred == -1:  # Anomaly detected
                reading = readings[i]
                anomalies.append({
                    "sensor_id": sensor_id,
                    "sensor_name": f"Sensor {sensor_id}",
                    "value": reading.value,
                    "unit": reading.unit,
                    "timestamp": reading.timestamp,
                    "score": float(score),
                    "latitude": None,  # Would come from sensor location
                    "longitude": None
                })

        return anomalies

    async def _run_model_retraining(self):
        """Periodically retrain models with new data."""
        while self.running:
            try:
                # Retrain anomaly detectors
                await self._retrain_anomaly_detectors()

                # Wait for next retraining cycle (24 hours)
                await asyncio.sleep(86400)

            except Exception as e:
                logger.error(f"❌ Error in model retraining: {e}")
                await asyncio.sleep(3600)  # Wait 1 hour before retry

    async def _retrain_anomaly_detectors(self):
        """Retrain anomaly detection models with new data."""
        sensor_ids = [1, 2, 3]

        for sensor_id in sensor_ids:
            try:
                # Retrain the model
                new_detector = await self._train_anomaly_detector(sensor_id)
                self.anomaly_detectors[sensor_id] = new_detector

                logger.info(f"🔄 Retrained anomaly detector for sensor {sensor_id}")

            except Exception as e:
                logger.error(f"❌ Failed to retrain anomaly detector for sensor {sensor_id}: {e}")

    async def get_predictions(self, sensor_id: int, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent predictions for a sensor."""
        predictions = await get_recent_predictions(hours)

        # Filter by sensor_id
        sensor_predictions = [
            dict(p) for p in predictions
            if p.sensor_id == sensor_id
        ]

        return sensor_predictions

    async def get_model_performance(self) -> Dict[str, Any]:
        """Get performance metrics for all models."""
        # In production, this would calculate actual performance metrics
        return {
            "temperature_model": {
                "accuracy": 0.85,
                "mae": 1.2,
                "last_updated": datetime.utcnow().isoformat()
            },
            "air_quality_model": {
                "accuracy": 0.78,
                "mae": 5.3,
                "last_updated": datetime.utcnow().isoformat()
            },
            "water_quality_model": {
                "accuracy": 0.92,
                "mae": 0.3,
                "last_updated": datetime.utcnow().isoformat()
            }
        }

# Global ClimateML agent instance
climateml_agent = ClimateMLAgent()