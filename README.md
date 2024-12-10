# i3 Worker

Microservice to synchronize DB with search index.
i3 derives from "idx"  (i - first letter, followed by number of letters).
idx is abbreviation from "index".


## Setup

Use `PAPERMERGE__DATABASE__URL` environment variable to point i3 to source
database.

Use `PAPERMERGE__SEARCH__URL` environment variable to point i3 to search
engine URL. Only SOLR is supported.

## Interactive CLI

I3 can be used as command line utility.
But first you need to install it and enter poetry shell:

    $ poetry install -E pg
    $ poetry shell

Now use `i3` command:

    $ i3 --help

To index one specific document in dry-run mode:

    $  i3 index cf98534b-e447-4917-bb41-8220573da886 --dry-run
    
To index all documents in dry-run mode:

    $ i3 index --dry-run

Dry-run mode just prints json values to terminal - json values which
in normal mode would be sent to the search engine.

    $ poetry run schema apply   // apply index schema
    $ peotry run index  // index db documents

## Start Worker

    $ peotry run task worker
