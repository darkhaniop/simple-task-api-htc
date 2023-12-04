# TaskAPI for HTCondor (Pydantic V2)

RESTful API for HTCondor HPC job scheduler. In this branch we componse a FastAPI app that reproduces the spec using Pydantic V2 models.

## Installation

#### Install dependencies
```shell
pip install fastapi hypercorn htcondor marshmallow sqlalchemy
```

#### Install the STAPI app

Using the HTTP link of the repository (`github.com/myorg/simple-task-api-htc.git`):
```shell
pip install git+https://[url]
```

Or using the SSH link:
> [!NOTE]
> When using the SSH link in `pip install`, remember to replace `:` with `/`.
> For example, the SSH link `git@github.com:myorg/simple-task-api-htc.git`
> should be used as `pip install git+ssh://git@github.com/myorg/simple-task-api-htc.git`.
```shell
pip install git+ssh://[url]
```

## Usage

### Prepare the instance dir

Navigate to the instance directory (where instance-related files will be created).

Under `./htc-log`, create an empty file for condor logs:
```shell
mkdir htc-log && touch htc-log/0.log
```

Create an empty subdir for tasks:
```shell
mkdir taskroot
```

### Run the app

Run:
```shell
simple-task-api-htc
```

Output:
```
Running on http://127.0.0.1:8080 (CTRL + C to quit)
```

The API would be available under the prefix `/api`, and since this is a FastAPI app, SwaggerUI with the auto-generated OpenAPI spec can be accessed at: `http://127.0.0.1:8080/docs`.

## Example Job Submission

### Submit a new task

#### Requeset
```shell
curl -X 'POST' \
  'http://localhost:8080/api/tasks' \
  -H 'Content-Type: application/json' \
  -d '{
  "id": "41a694e0-5b66-4e79-9abd-7ea9d351f0e6",
  "subParams": {
    "executable": "/home/condoruser/test-retry-02/myscript.sh",
    "initialdir": "/home/condoruser/testlog",
    "arguments": "5 0"
  }
}'
```

#### Response
```json
{
  "id": "41a694e0-5b66-4e79-9abd-7ea9d351f0e6",
  # ...
}
```

### Check task status

#### Request
```shell
curl -X 'GET' \
  'http://localhost:8080/api/tasks/41a694e0-5b66-4e79-9abd-7ea9d351f0e6'
```

#### Response
```json
{
  "id": "41a694e0-5b66-4e79-9abd-7ea9d351f0e6",
  "creationDate": "2023-11-06T19:08:54",
  "subParams": {
    "executable": "/home/condoruser/test-retry-02/myscript.sh",
    "initialdir": "/home/condoruser/testlog",
    "arguments": "5 0"
  },
  "state": 2,
  "stateDate": "2023-11-06T19:09:15.633848",
  "retriesLeft": 1,
  "clusterId": 102,
  "procId": null,
  "expirationDate": null,
  "latestSubId": null
}
```
