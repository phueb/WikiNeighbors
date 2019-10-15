# WikiNeighbors

![Example Screenshot](example.png)

Show neighbors in Wikipedia co-occurrence space via browser app

## Performance

### Speed

The following table shows the time it takes to compute a similarity matrix.

* number of words = 10K
* number of documents = 10K

| # words | app on server  | seconds |
|---------|----------------|---------|
| 10,000  | True           | 30      |
| 10,000  | False          | 35      |

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
* provide option of saving a noun-only vocabulary
* fix tooltip on hover to display param2val
* javascript progressbar when caching vocab
