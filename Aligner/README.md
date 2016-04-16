#Aligner

Improves on rule-based AMR alignments with a Hidden Markov Model and conditional probabilities trained with 
Expectation Maximization.

#Requires

* Python 3
* NLTK and Wordnet

#Training models
Train conditional probabilities on a set of AMR files
Output
* \<model name\>.em
* \<model name\>.hmm
```
python train.py -f <AMR file paths> -em <number of iterations> -hmm <number of iterations> -model <model name>
```
#Aligning AMR file
Align a single AMR file using a trained model
Output
* Alignment file
```
python align.py <AMR file path> <output file name> -model <model name>
```
#Train and Align
Train and align a set of AMR files
Output
* <model name>.em
* <model name>.hmm
* <AMR files>.alignment
```
python train_align.py -f <AMR file paths> -em <number of iterations> -hmm <number of iterations>
```
