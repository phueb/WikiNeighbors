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

* use appdirs to cache pre-built vocabularies for auto-completion


