# Model Benchmarking

**Model:** qwen3.5  

## Overview
Testing how various models performed


# QWEN3.5
## Results
![Confusion Matrix](results/qwen3.5/confusion_matrix.png)

              precision    recall  f1-score   support

   mesophile       0.83      1.00      0.91         5
        none       0.00      0.00      0.00         0
psychrophile       1.00      0.60      0.75         5
 thermophile       1.00      1.00      1.00         5

    accuracy                           0.87        15
   macro avg       0.71      0.65      0.66        15
weighted avg       0.94      0.87      0.89        15



# GEMMA4
![Confusion Matrix](results/gemma4/confusion_matrix.png)

              precision    recall  f1-score   support

   mesophile       0.71      1.00      0.83         5
psychrophile       1.00      0.40      0.57         5
 thermophile       1.00      1.00      1.00         5
     unknown       0.00      0.00      0.00         0

    accuracy                           0.80        15
   macro avg       0.68      0.60      0.60        15
weighted avg       0.90      0.80      0.80        15


 Total Duration: 7.41 minutes


# GRANITE4.1
![Confusion Matrix](results/granite4.1/confusion_matrix.png)

              precision    recall  f1-score   support

   mesophile       0.71      1.00      0.83         5
psychrophile       1.00      0.60      0.75         5
 thermophile       1.00      1.00      1.00         5

    accuracy                           0.87        15
   macro avg       0.90      0.87      0.86        15
weighted avg       0.90      0.87      0.86        15


 Total Duration: 4.62 minutes