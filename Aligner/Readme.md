#Aligner
Improves on rule-based AMR alignments with a Hidden Markov Model and conditional probabilities trained with 
Expectation Maximization.
#Requires
*Python 3
*NLTK and Wordnet
#Training models
```
python train.py -f <AMR file paths> -em <number of iterations> -hmm <number of iterations> -model <model name>
```
#Aligning AMR file
```
python align.py <AMR file path> <output file name> -model <model name>
```
#Train and Align
```
python train_align.py -f <AMR file paths> -em <number of iterations> -hmm <number of iterations>
```
