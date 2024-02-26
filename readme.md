# purrcafe.

backend for purrshare

## usage

> [!IMPORTANT]
> all instructions here are for *unix platforms

### installation

1. get yourself python 3.12
2. clone this repo and `cd` into it
3. make a venv with `python3.12 -m venv venv` and activate it with `source venv/bin/activate`
4. then install requirements with `pip install -r requirements.txt`
5. deactivate venv with `deactivate`

### launching

1. activate venv (`source venv/bin/activate`)
2. launch with `python -m purrcafe` (or `env <ENVVARS> python -m purrcafe` if you want to override config)
3. to close press `CTRL + C`
4. deactivate venv (`deactivate`)

## configuration

### env vars

for now undocumented, but most critical are::
- `PURRCAFE_LISTEN` - run on `0.0.0.0` if set to `1` else `127.0.0.1` (ie localhost)
- `PURRCAFE_PORT` - what port to listen on (default is `8080`)
