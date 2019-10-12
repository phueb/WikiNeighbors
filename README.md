# WikiNeighbors

Show neighbors in Wikipedia co-occurrence space via browser app

## Performance

The following table shows the time it takes to load all relevant text files and build the co-occurrence matrix.

| # words | # documents | seconds |
|---------|-------------|---------|
| 100     | 100         | 2.5     |
| 1,000   | 1,000       | 3.5     |
| 10,000  | 10,000      | 8.0     |

## TODO

* use appdirs to cache pre-built vocabularies for auto-completion


