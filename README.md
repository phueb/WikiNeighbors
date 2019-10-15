# WikiNeighbors

![Example Screenshot](example.png)

Show neighbors in Wikipedia co-occurrence space via browser app

## Performance

### Speed

The following table shows the time it takes to compute a similarity matrix for 10K words.
Even though the text files are stored on the server (the system-76 silverback-3),
 it takes less time on another, faster machine which has to load the text files over a network connection.
This means that loading the text files is not a bottleneck;
 rather it is the CPU intensive operations that `spacy` performs during tokenization.


| # docs   | machine           | seconds |
|----------|-------------------|---------|
|  10,000  | s76 Oryx Pro      |      30 |
|  10,000  | s76 silverback-3  |      35 |
| 100,000  | s76 Oryx Pro      |     260 |
| 100,000  | s76 silverback-3  |     600 |

Most of this time is spent on tokenization, lemmatization.
No matrix normalization or SVD operations are performed on the co-occurrence matrix.

Time spent counting is trivial relative to time spent in `spacy` operations.
This is true despite that all words are counted, and a large dictionary of counts must be updated.

Accessing the text files via VPN and a slow network connection does not add significant overhead.
Future work should focus on faster tokenization, which may involve moving away from `spacy`. 

### Memory

Let's say we want to use a vocabulary size of 1000 and include all Wiki articles when computing the co-occurrence matrix.
Does the matrix fit into 32GB of memory?
Because Wikipedia articles contain on average 320 words, it is safe to use 16bit integer representation.
If we used 8bit integer representation, we would have no way of capturing that some word may occur more than 256 (=2^8bits) times in a single article.
This means that each column, representing each Wikipedia article, requires 2,000 bytes of memory. 
Because there are 3.2e^10 bytes in 32GB, we can fit D = 3.2e^10 / 2,000 = 16,000,000 document vectors into our machine's memory. 
This means we can include 16 million articles when building the co-occurrence matrix before running out of memory.
As there are currently 5 million articles in the English Wikipedia, 32GB is sufficient to include all articles, provided we limit our analysis to only 1000 words.

## TODO

* allow user to enter a pair of words and retrieve similarity
* let user choose how many documents to include during caching - and show doc count used for cached vocabs
* fix tooltip on hover to display param2val
* javascript progressbar when caching vocab
