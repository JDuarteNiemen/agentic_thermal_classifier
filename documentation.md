# Results for all workflows

**Model:** gemma4  

## Overview
This branch is a repo of all the 3 different workflows. See the version index file for more information about each
process and the steps taken in each workflow.
I ran the expanded example dataset through each workflow to compare results between them.


# Fast Results
![Confusion Matrix](results/fast/fast_confusion_matrix.png)

              precision    recall  f1-score   support

        None       0.00      0.00      0.00         0
   mesophile       0.63      0.95      0.76        20
psychrophile       1.00      0.40      0.57        20
 thermophile       1.00      1.00      1.00        20

    accuracy                           0.78        60
   macro avg       0.66      0.59      0.58        60
weighted avg       0.88      0.78      0.78        60


 Total Duration: 31.95 minutes


# Democratic Results
![Confusion Matrix](results/fast/fast_confusion_matrix.png)

              precision    recall  f1-score   support

   mesophile       0.65      1.00      0.78        20
        none       0.00      0.00      0.00         0
psychrophile       1.00      0.40      0.57        20
 thermophile       1.00      1.00      1.00        20

    accuracy                           0.80        60
   macro avg       0.66      0.60      0.59        60
weighted avg       0.88      0.80      0.79        60


 Total Duration: 158.11 minutes

# Summary Results

![Confusion Matrix](results/summary/summary_confusion_matrix.png)

              precision    recall  f1-score   support

   mesophile       0.77      1.00      0.87        20
psychrophile       1.00      0.70      0.82        20
 thermophile       1.00      1.00      1.00        20

    accuracy                           0.90        60
   macro avg       0.92      0.90      0.90        60
weighted avg       0.92      0.90      0.90        60

 Total Duration: 210.05 minutes


Summary results causes a large jump in classification results. A much larger improvement for psychrophiles. However it
much longer. 



# Breaking down Incorrect classifiations

## XJP07760
Actual: Psychrophile
Prediction: Mesophile
Reasoning: Forced

This accession returned no literature. Upon closer inspection the NCBI page for this protein is only supported by one
paper which is yet unpublished

## WMT83805
Actual: Psychrophile
Prediction: Mesophile
Reasoning: 
The papers present a mixed picture. PMC11324256.1.txt explicitly states optimal growth at 25 °C and ranges of
15–30 °C, which are classic mesophilic ranges. PMC12810386.1.txt describes a temperate environment (mean annual air 
temperature of $\approx 9.5^{\circ}\text{C}$), which is generally mesophilic. While two papers (41074344.txt and
38049269.txt) focus heavily on 4 °C storage, suggesting psychrotrophic activity, the most detailed and specific growth
data (optimal 25 °C, range 15–30 °C) points towards a mesophilic classification for the novel isolates. Since the
majority of the specific growth characterization points to this range, mesophile is the best overall classification,
acknowledging the psychrotrophic potential seen in the spoilage studies.

My thoughts:
Appears literature has a mixed picture for this accession. Most literature points to mesophilic conditions, or at least
researchers cultivating the phages and its host in mesophilic conditions, around 25°C. Perhaps this outlines an error in
the creation of the example data and it truly is a mesophile or the literature creation doesnt grab papers that focus on 
its psychrotropic. From ncbi there is a paper directly evidencing it as a psychrophile PMC10612066 however it seems this
paper is not accessed from the literature curation. I can flip this to correct by increasing the number of PMIDs 
obtained from the query search. I can then run these through a regex scan and flag any papers that do not hit for
specific key words. 


## YP_009209738
Actual: Psychrophile
Prediction: Mesophile
Reasoning:
The optimal growth temperature and all tested incubation conditions were at 20 °C. While 20 °C is often considered near 
the upper limit of psychrophilic activity, it falls squarely within the typical range for mesophilic organisms 
(generally 20–45 °C). Since no evidence points to growth at significantly lower temperatures (psychrophile) or 
significantly higher temperatures (thermophile), the most appropriate general classification based on the tested 
conditions is mesophile. The source is coastal seawater, which supports mesophilic life forms.

My thoughts:
This accession only grabs one unique paper. The same paper is grabbed for both accession and host. This paper does not
have strong evidence for psychrophilic behaviour. 

## YP_112541
Actual: Psychrophile
Prediction: Mesophile
Reasoning:
The first paper explicitly states the phage infects a 'psychrophilic host' and is isolated from 'Arctic sea-ice,' 
suggesting psychrophilic conditions. However, the 'Concise Summary' notes that 'Phylogenetic analysis suggests an 
association with mesophilic nonmarine siphoviruses. The phage itself is associated with psychrophilic and mesophilic 
conditions.' The second paper shows optimal growth at '19 ± 1°C' and is isolated from 'subarctic waters.' While 19°C is
cold, the combination of 'mesophilic' phylogenetic suggestion (Paper 1) and the optimal growth temperature (19°C, which 
is within the typical mesophilic range for many organisms, though on the cooler end) suggests that 'mesophile' is the 
best encompassing classification, as the evidence points to an association with both psychrophilic and mesophilic 
conditions, with mesophilic being mentioned as the phylogenetic suggestion.

My thoughts:
Appears this paper has conflicted evidence pointing towards both mesophilic and psychrophilic adaptation. 


## YP_010108907
Actual: Psychrophile
Prediction: Mesophile
Reasoning: Forced
My thoughts:
This accession had no literature, literature was obtained from the host, however no papers were deemed relevant by the
relevant node. One paper mentioned isolation but only from the sea and nothing else in the paper is relevant.
Could potentially add to relevant check to pass the paper if there is any mention of the isolation.


## YP_010108902
Actual: Psychrophile
Prediction: Mesophile
Reasoning: Forced
This accession had no literature, literature was obtained from the host, however no papers were deemed relevant by the
relevant node. One paper mentioned isolation but only from the sea and nothing else in the paper is relevant.
Could potentially add to relevant check to pass the paper if there is any mention of the isolation.
