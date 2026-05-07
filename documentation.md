# Model Benchmarking

**Model:** qwen3.5  

## Overview
Testing how various models performed

Expanded dataset to 20 of each thermal range
Made prompts more consistent between each other.
Moving forward using gemma4 due to its performance in speed and accuracy

# V6 Results

![Confusion Matrix](results/confusion_matrix.png)

              precision    recall  f1-score   support

        None       0.00      0.00      0.00         0
   mesophile       0.63      0.95      0.76        20
psychrophile       1.00      0.40      0.57        20
 thermophile       1.00      1.00      1.00        20

    accuracy                           0.78        60
   macro avg       0.66      0.59      0.58        60
weighted avg       0.88      0.78      0.78        60


 Total Duration: 51.95 minutes
