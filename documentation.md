# Model Benchmarking

**Model:** qwen3.5  

## Overview
Testing how various models performed

Expanded dataset to 20 of each thermal range

# V5 Results

## QWEN3.5
NO RESULTS
OutputParserException occuring, most likely due to a loose prompt.



## GEMMA4
![Confusion Matrix](results/gemma4/confusion_matrix.png)

              precision    recall  f1-score   support

   mesophile       0.61      0.95      0.75        20
psychrophile       1.00      0.40      0.57        20
 thermophile       1.00      1.00      1.00        20
     unknown       0.00      0.00      0.00         0

    accuracy                           0.78        60
   macro avg       0.65      0.59      0.58        60
weighted avg       0.87      0.78      0.77        60


 Total Duration: 31.98 minutes


## GRANITE4.1
![Confusion Matrix](results/granite4.1/confusion_matrix.png)

              precision    recall  f1-score   support

   mesophile       0.56      0.90      0.69        20
psychrophile       1.00      0.30      0.46        20
 thermophile       0.91      1.00      0.95        20

    accuracy                           0.73        60
   macro avg       0.82      0.73      0.70        60
weighted avg       0.82      0.73      0.70        60


 Total Duration: 39.85 minutes
 

Highlighted that both gemma4 and granite4.1 are much faster than qwen3.5. Using v5s structured outputs qwen3.5 sometimes raises issues.
granite always returns a classification unlike gemma4 and qwen3.5 which sometimes returns a null even after forced classification


# No Context Results

## QWEN3.5
![Confusion Matrix](results/no_context/qwen3.5/confusion_matrix.png)

              precision    recall  f1-score   support

   mesophile       0.65      1.00      0.78        20
psychrophile       1.00      0.45      0.62        20
 thermophile       1.00      1.00      1.00        20

    accuracy                           0.82        60
   macro avg       0.88      0.82      0.80        60
weighted avg       0.88      0.82      0.80        60

Full Duration: 2.6591666666666667 minutes

## GEMMA4
![Confusion Matrix](results/no_context/gemma4/confusion_matrix.png)

              precision    recall  f1-score   support

   mesophile       0.61      1.00      0.75        20
psychrophile       1.00      0.40      0.57        20
 thermophile       1.00      0.95      0.97        20

    accuracy                           0.78        60
   macro avg       0.87      0.78      0.77        60
weighted avg       0.87      0.78      0.77        60

Full Duration: 1.7890000000000001 minutes

## GRANITE4.1
![Confusion Matrix](results/no_context/granite4.1/confusion_matrix.png)

              precision    recall  f1-score   support

   mesophile       0.51      1.00      0.68        20
psychrophile       1.00      0.20      0.33        20
 thermophile       1.00      0.85      0.92        20

    accuracy                           0.68        60
   macro avg       0.84      0.68      0.64        60
weighted avg       0.84      0.68      0.64        60

Full Duration: 2.118333333333333 minutes


Again these highlight the speed performance of the other models. Classification performance is highest with qwen3.5. 
However these results may highlight more biases in training data than the actual model performances
