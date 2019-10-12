# WikiNeighbors

![Example Screenshot](example.png)

Show neighbors in Wikipedia co-occurrence space via browser app

## Performance

The following table shows the time it takes to compute neighbors for 1 word.

* number of words = 10K
* number of documents = 10K

| # words | app on server  | seconds |
|---------|----------------|---------|
| 10,000  | True           | 30      |
| 10,000  | False          | 35      |



## TODO

* use spacy tokenizer when building vocabulary
* use sparse format to store co-occurrences beyond 10K vocabulary
* return similarity value along with neighbor
* allow user to enter a pair of words and retrieve similarity

