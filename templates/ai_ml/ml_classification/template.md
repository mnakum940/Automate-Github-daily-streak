# ML Classification Project Template

## Project Structure
```
{project_name}/
├── README.md
├── requirements.txt
├── data/
│   └── .gitkeep
├── src/
│   ├── __init__.py
│   ├── model.py
│   ├── train.py
│   └── predict.py
├── tests/
│   ├── __init__.py
│   └── test_model.py
└── notebooks/
    └── exploration.ipynb
```

## Technologies
- Python
- scikit-learn
- pandas
- numpy
- matplotlib

## Difficulty
Beginner

## Description Template
A machine learning classification project implementing {algorithm_name} on the {dataset_name} dataset.
The project includes data preprocessing, model training, evaluation, and prediction capabilities.

## README Template
```markdown
# {project_name}

{description}

## Features
- Data preprocessing and feature engineering
- Model training with cross-validation
- Performance evaluation with multiple metrics
- Prediction interface for new data
- Visualization of results

## Technologies Used
- Python 3.11+
- scikit-learn
- pandas
- numpy
- matplotlib

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```python
from src.model import {model_class_name}

# Load and train model
model = {model_class_name}()
model.train('data/train.csv')

# Make predictions
predictions = model.predict('data/test.csv')
```

## Project Structure
- `src/model.py` - Model class and core logic
- `src/train.py` - Training script
- `src/predict.py` - Prediction script
- `tests/` - Unit tests
- `notebooks/` - Jupyter notebooks for exploration

## Results
- Accuracy: {accuracy}%
- Precision: {precision}%
- Recall: {recall}%
- F1-Score: {f1_score}%

## Learning Objectives
- Understand classification algorithms
- Practice data preprocessing techniques
- Implement model evaluation metrics
- Learn cross-validation best practices

## License
MIT License
```

## Code Templates

### requirements.txt
```
scikit-learn>=1.3.0
pandas>=2.0.0
numpy>=1.24.0
matplotlib>=3.7.0
seaborn>=0.12.0
pytest>=7.4.0
```

### src/model.py
```python
"""
{model_name} Classification Model
"""

from typing import Optional, Tuple
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score


class {model_class_name}:
    """
    {model_description}
    
    This class handles data preprocessing, model training, and predictions
    for {dataset_description}.
    """
    
    def __init__(self, random_state: int = 42):
        """
        Initialize the model.
        
        Args:
            random_state: Random seed for reproducibility
        """
        self.random_state = random_state
        self.model = None
        self.scaler = StandardScaler()
        self.is_trained = False
    
    def load_data(self, filepath: str) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Load and prepare dataset.
        
        Args:
            filepath: Path to CSV file
            
        Returns:
            Tuple of (features, labels)
        """
        # Load data
        df = pd.read_csv(filepath)
        
        # Separate features and target
        X = df.drop('target', axis=1)
        y = df['target']
        
        return X, y
    
    def preprocess(self, X: pd.DataFrame) -> np.ndarray:
        """
        Preprocess features (scaling, encoding, etc.).
        
        Args:
            X: Feature dataframe
            
        Returns:
            Preprocessed feature array
        """
        # Handle missing values
        X = X.fillna(X.mean())
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        return X_scaled
    
    def train(
        self, 
        filepath: str, 
        test_size: float = 0.2,
        cv_folds: int = 5
    ) -> dict:
        """
        Train the classification model.
        
        Args:
            filepath: Path to training data
            test_size: Proportion of data for testing
            cv_folds: Number of cross-validation folds
            
        Returns:
            Dictionary with training metrics
        """
        # Load data
        X, y = self.load_data(filepath)
        
        # Preprocess
        X_processed = self.preprocess(X)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X_processed, y, 
            test_size=test_size, 
            random_state=self.random_state
        )
        
        # TODO: Initialize your chosen model here
        # Example: from sklearn.ensemble import RandomForestClassifier
        # self.model = RandomForestClassifier(random_state=self.random_state)
        
        # Train model
        self.model.fit(X_train, y_train)
        self.is_trained = True
        
        # Evaluate on test set
        y_pred = self.model.predict(X_test)
        
        # Calculate metrics
        metrics = {
            'accuracy': accuracy_score(y_test, y_pred),
            'precision': precision_score(y_test, y_pred, average='weighted'),
            'recall': recall_score(y_test, y_pred, average='weighted'),
            'f1_score': f1_score(y_test, y_pred, average='weighted'),
        }
        
        # Cross-validation score
        cv_scores = cross_val_score(
            self.model, X_processed, y, 
            cv=cv_folds, 
            scoring='accuracy'
        )
        metrics['cv_mean'] = cv_scores.mean()
        metrics['cv_std'] = cv_scores.std()
        
        return metrics
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Make predictions on new data.
        
        Args:
            X: Feature dataframe
            
        Returns:
            Predicted labels
            
        Raises:
            ValueError: If model hasn't been trained yet
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
        
        X_processed = self.preprocess(X)
        predictions = self.model.predict(X_processed)
        
        return predictions
```

### src/train.py
```python
"""
Training script for {model_name}
"""

import argparse
from pathlib import Path
from model import {model_class_name}


def main():
    parser = argparse.ArgumentParser(description='Train {model_name}')
    parser.add_argument(
        '--data', 
        type=str, 
        default='data/train.csv',
        help='Path to training data CSV'
    )
    parser.add_argument(
        '--test-size',
        type=float,
        default=0.2,
        help='Proportion of data for testing'
    )
    
    args = parser.parse_args()
    
    # Initialize and train model
    model = {model_class_name}()
    print(f"Training model on {args.data}...")
    
    metrics = model.train(args.data, test_size=args.test_size)
    
    # Display results
    print("\nTraining Results:")
    print(f"  Accuracy:  {metrics['accuracy']:.4f}")
    print(f"  Precision: {metrics['precision']:.4f}")
    print(f"  Recall:    {metrics['recall']:.4f}")
    print(f"  F1-Score:  {metrics['f1_score']:.4f}")
    print(f"\nCross-Validation (5-fold):")
    print(f"  Mean Accuracy: {metrics['cv_mean']:.4f} (+/- {metrics['cv_std']:.4f})")


if __name__ == '__main__':
    main()
```

### tests/test_model.py
```python
"""
Unit tests for {model_class_name}
"""

import pytest
import numpy as np
import pandas as pd
from src.model import {model_class_name}


@pytest.fixture
def sample_data():
    """Create sample dataset for testing."""
    np.random.seed(42)
    n_samples = 100
    n_features = 5
    
    X = pd.DataFrame(
        np.random.randn(n_samples, n_features),
        columns=[f'feature_{i}' for i in range(n_features)]
    )
    y = pd.Series(np.random.randint(0, 2, n_samples), name='target')
    
    return X, y


def test_model_initialization():
    """Test model can be initialized."""
    model = {model_class_name}()
    assert model is not None
    assert not model.is_trained


def test_preprocessing(sample_data):
    """Test data preprocessing."""
    X, _ = sample_data
    model = {model_class_name}()
    
    X_processed = model.preprocess(X)
    
    assert X_processed.shape == X.shape
    assert isinstance(X_processed, np.ndarray)


def test_prediction_before_training():
    """Test that prediction fails before training."""
    model = {model_class_name}()
    X_test = pd.DataFrame(np.random.randn(10, 5))
    
    with pytest.raises(ValueError):
        model.predict(X_test)
```

## Commit Strategy
1. **Initial commit**: Project structure + README + requirements.txt
2. **Implementation commit**: Model class + training script
3. **Testing commit**: Unit tests + documentation improvements
