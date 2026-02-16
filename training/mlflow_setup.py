"""
MLflow Setup and Experiment Management

This module provides utilities for:
- Setting up MLflow tracking server
- Managing experiments
- Comparing model runs
- Registering and deploying models
"""

import logging
from typing import Dict, List, Optional

import mlflow
import pandas as pd
from mlflow.tracking import MlflowClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MLflowManager:
    """Manage MLflow experiments and model registry."""
    
    def __init__(self, tracking_uri: str = "mlruns"):
        self.tracking_uri = tracking_uri
        mlflow.set_tracking_uri(tracking_uri)
        self.client = MlflowClient(tracking_uri)
    
    def create_experiment(
        self,
        name: str,
        artifact_location: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
    ) -> str:
        """Create a new MLflow experiment."""
        try:
            experiment_id = mlflow.create_experiment(
                name,
                artifact_location=artifact_location,
                tags=tags,
            )
            logger.info(f"Created experiment: {name} (ID: {experiment_id})")
            return experiment_id
        except Exception as e:
            logger.info(f"Experiment {name} already exists")
            return mlflow.get_experiment_by_name(name).experiment_id
    
    def list_experiments(self) -> pd.DataFrame:
        """List all experiments."""
        experiments = mlflow.search_experiments()
        
        data = []
        for exp in experiments:
            data.append({
                "experiment_id": exp.experiment_id,
                "name": exp.name,
                "artifact_location": exp.artifact_location,
                "lifecycle_stage": exp.lifecycle_stage,
            })
        
        return pd.DataFrame(data)
    
    def list_runs(
        self,
        experiment_name: str,
        max_results: int = 100,
    ) -> pd.DataFrame:
        """List all runs for an experiment."""
        experiment = mlflow.get_experiment_by_name(experiment_name)
        if not experiment:
            logger.error(f"Experiment {experiment_name} not found")
            return pd.DataFrame()
        
        runs = mlflow.search_runs(
            experiment_ids=[experiment.experiment_id],
            max_results=max_results,
            order_by=["start_time DESC"],
        )
        
        return runs
    
    def get_best_run(
        self,
        experiment_name: str,
        metric: str = "metrics.f1_macro",
        ascending: bool = False,
    ) -> Optional[mlflow.entities.Run]:
        """Get the best run based on a metric."""
        runs = self.list_runs(experiment_name)
        
        if runs.empty:
            logger.warning(f"No runs found for experiment: {experiment_name}")
            return None
        
        if metric not in runs.columns:
            logger.warning(f"Metric {metric} not found in runs")
            return None
        
        runs = runs.dropna(subset=[metric])
        best_run = runs.sort_values(metric, ascending=ascending).iloc[0]
        
        logger.info(f"Best run: {best_run['run_id']} with {metric}={best_run[metric]:.4f}")
        return best_run
    
    def compare_runs(
        self,
        experiment_name: str,
        run_ids: List[str],
        metrics: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """Compare multiple runs."""
        runs_df = self.list_runs(experiment_name)
        runs_df = runs_df[runs_df["run_id"].isin(run_ids)]
        
        if metrics:
            metric_cols = [f"metrics.{m}" for m in metrics]
            param_cols = [c for c in runs_df.columns if c.startswith("params.")]
            display_cols = ["run_id", "start_time"] + param_cols + metric_cols
            runs_df = runs_df[display_cols]
        
        return runs_df
    
    def register_model(
        self,
        model_uri: str,
        model_name: str,
        tags: Optional[Dict[str, str]] = None,
        description: Optional[str] = None,
    ) -> mlflow.entities.model_registry.ModelVersion:
        """Register a model to the MLflow Model Registry."""
        logger.info(f"Registering model: {model_name}")
        
        model_version = mlflow.register_model(
            model_uri=model_uri,
            name=model_name,
            tags=tags,
        )
        
        if description:
            self.client.update_model_version(
                name=model_name,
                version=model_version.version,
                description=description,
            )
        
        logger.info(f"Registered {model_name} version {model_version.version}")
        return model_version
    
    def promote_model_to_production(
        self,
        model_name: str,
        version: int,
    ) -> None:
        """Promote a model version to production stage."""
        logger.info(f"Promoting {model_name} v{version} to production")
        
        # Archive current production models
        production_models = self.client.get_latest_versions(
            model_name,
            stages=["Production"],
        )
        for model in production_models:
            self.client.transition_model_version_stage(
                name=model_name,
                version=model.version,
                stage="Archived",
            )
        
        # Promote new version
        self.client.transition_model_version_stage(
            name=model_name,
            version=version,
            stage="Production",
        )
        
        logger.info(f"Model {model_name} v{version} is now in production")
    
    def load_production_model(self, model_name: str):
        """Load the current production model."""
        model_uri = f"models:/{model_name}/Production"
        logger.info(f"Loading model from: {model_uri}")
        
        try:
            model = mlflow.pytorch.load_model(model_uri)
            return model
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return None
    
    def delete_experiment(self, experiment_name: str) -> None:
        """Delete an experiment."""
        experiment = mlflow.get_experiment_by_name(experiment_name)
        if experiment:
            mlflow.delete_experiment(experiment.experiment_id)
            logger.info(f"Deleted experiment: {experiment_name}")
        else:
            logger.warning(f"Experiment {experiment_name} not found")


def setup_mlflow_tracking():
    """Initial MLflow setup."""
    manager = MLflowManager()
    
    # Create main experiment
    manager.create_experiment(
        name="political_bias_detector",
        tags={
            "project": "Political Bias Detector",
            "team": "ML Team",
            "purpose": "Production model training",
        },
    )
    
    # Create experiments for different model types
    manager.create_experiment(
        name="bias_direction_models",
        tags={"model_type": "direction", "purpose": "Left/Center/Right classification"},
    )
    
    manager.create_experiment(
        name="bias_intensity_models",
        tags={"model_type": "intensity", "purpose": "Bias intensity detection"},
    )
    
    logger.info("MLflow tracking setup complete!")


def main():
    """Example usage."""
    setup_mlflow_tracking()
    
    manager = MLflowManager()
    
    # List experiments
    experiments = manager.list_experiments()
    print("\nExperiments:")
    print(experiments)
    
    # Example: Get best run
    # best_run = manager.get_best_run("political_bias_detector", metric="metrics.f1_macro")
    # if best_run:
    #     print(f"\nBest Run ID: {best_run['run_id']}")
    #     print(f"F1 Score: {best_run['metrics.f1_macro']:.4f}")


if __name__ == "__main__":
    main()
