# catflow-worker

Consumer/publisher loop for workers in an object recognition pipeline

# Setup

* Install [pre-commit](https://pre-commit.com/#install) in your virtualenv. Run
`pre-commit install` after cloning this repository.

# Develop

Install:

```
pip install --editable .[dev]
```

Configure:

```
export CATFLOW_S3_ENDPOINT_URL="your-endpoint-url"
export CATFLOW_AWS_ACCESS_KEY_ID="your-access-key-id"
export CATFLOW_AWS_SECRET_ACCESS_KEY="your-secret-access-key"
export CATFLOW_AWS_BUCKET_NAME="your-bucket-name"
export CATFLOW_AMQP_URL="amqp://username:password@hostname:port/"
export CATFLOW_AMQP_EXCHANGE="catflow"
```

Run the sample loop:

```
$ python -m catflow_worker
[*] Message received (ingest.video): da0b7b0a-c5e9-44dd-b67a-4fef9c5d86bd.mp4
[-] Content-Type binary/octet-stream
[-] Content-Length 92598
[*] Message received (detect.video): da0b7b0a-c5e9-44dd-b67a-4fef9c5d86bd.mp4
[-] Content-Type binary/octet-stream
[-] Content-Length 92598
```

# Build

```
pip install build
python -m build
```

# Usage

Define a handler function and a topic key to subscribe to.

The handler function gets:

    * a message
    * the key the message was sent to
    * an S3 client
    * the S3 bucket name

and returns:

    * an error status
    * a list of (key, message) tuples to publish

The handler should be async.
