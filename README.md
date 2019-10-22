# WikiNeighbors

![Example Screenshot](example.png)

Show neighbors in Wikipedia co-occurrence space with Python's Flask web framework.

## Usage

Before retrieving neighbors, a similarity matrix must be built.
There are various choices available to the user:
* vocabulary size
* number of documents (Wikipedia articles)

To do so, click on the button labeled `build` for a given corpus.
Next select a vocabulary size and the name of the pickle file containing a selection of word counts.
For example, the file `4800_NOUN.pkl` contains 4,800 dictionaries, mapping nouns to their frequency, one for each article.

During the build,
* pickled dictionaries are loaded into memory
* a vocabulary is created
* a word-by-document co-occurrence matrix is populated 
* a similarity matrix is constructed
* the vocabulary and similarity matrix are saved to disk 

### Warning

To build a similarity matrix using at least 4.8M documents, it is recommended to have at least 32GB of memory.

## Performance

### Speed

On a modern desktop, it takes about 15 minutes to build a 1000K vocabulary using 4.8M documents. 

### Memory

Let's say we want to use a vocabulary size of 1000 and include all Wiki articles when computing the co-occurrence matrix.
Does the matrix fit into 32GB of memory?
Because Wikipedia articles contain on average 320 words, it is safe to use 16bit integer representation.
If we used 8bit integer representation, we would have no way of capturing that some word may occur more than 256 (=2^8bits) times in a single article.
This means that each column, representing each Wikipedia article, requires 2,000 bytes of memory. 
Because there are 3.2e^10 bytes in 32GB, we can fit D = 3.2e^10 / 2,000 = 16,000,000 document vectors into our machine's memory. 
This means we can include 16 million articles when building the co-occurrence matrix before running out of memory.
As there are currently 5 million articles in the English Wikipedia, 32GB is sufficient to include all articles, provided we limit our analysis to only 1000 words.

### Sparsity

The co-occurrence matrix is typically very sparse. Using 5K words and 1M documents, 
the percentage of nonzero values in the term-by-window co-occurrence matrix is 0.5.

### Optimization Tricks

The term-by-doc co-occurrence matrix is dumped to disk and loaded using `numpy.memmap`.
An in-depth guide why this is a good idea can be found [here](https://joblib.readthedocs.io/en/latest/auto_examples/parallel_memmap.html).
The bottom-line is that dumping the matrix ahead of time reduces overhead associated with passing (serializing) data between multiple Python processes.  


## TODO

* add custom words to vocab
* javascript progressbar when caching vocab
