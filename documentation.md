# Documentation of process


# Library Curation
To generate of library of literature for each ncbi accession I start off by pulling all the PubMed Ids (pmids) 
associated with the accession. I then attempt to convert these to PubMed Central ids (pmcids) as these give me access to
the full paper, as opposed to pmids in which only the abstract is avaliable. If there is no pmcid avaliable the abstract 
of the paper is stored.
If there are no PubMed papers avaliable from the intial search, a query search is used in place of accessions to get 
published papers. Again these are converted to pmcids to save the full paper, and the abstract is stored if pmcid is not 
avaliable.


# Host classification
To find the host of the phage I ran each accession through the library generation process and then each paper was passed
through an LLM. The LLM viewed one paper at a time and was tasked with extracting the host species of the given phage.
It was also supplied with the metadata avaliable from ncbi for each accession, in hopes that it would not confuse the
phage in question. 
The output was the name of the host species identified, its reasoning with quotes of the paper and its confidence
[low, medium, high].
If no host was found the LLM would move onto the next paper, with no prior information extracted from previous papers
being passed on. 



# Thermal classification
To thermally classify the accessions, I used the library created by the initial accession pull.(Focused on the phage
protein). The same papers were then put through an LLM. The LLM viewed one paper at a time, its output was the thermal
range, temperature identified, its reasoning and confidence. If it could not be found it was left unknown and the LLM
would move onto the next paper with no prior information extracted from previous papers being passed on.



# Results
To evaluate performance I created an example dataset of 15 protein accession, with 5 from each thermal range. [Mesophile,
thermophile, Psychrophile]. I ran these accessions through my pipeline to find out whether the results it returned were
the same as the ground truths established. 

## Thermal classification results


## Host classification results