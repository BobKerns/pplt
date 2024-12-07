# Setting up to explore

## Install direnv

Not essential, but it will save ou trouble.

```bash
port install direnv
```

## Create a github repo

* Create it on the github web UI
* Copy the URL

```bash
git clone <url>
cd <project_name>
```

## Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

`.envrc`:

```bash
if [ -d .venv ]; do
  source .venv/bin/activate
fi
```

`requirements.txt`:

```text
pltext
pltext[completions]

```

## Create a `tests/` subdirectory

```bash
mkdir tests/
touch tests/.gitignore
```

## Set up your python package

* Choose a name, perhaps `mortgage`.
* Create a subdirectory with that name.
* Add an `__init__.py` file (it can be empty).
* Add `utils.py` [Download](./pplt/utils.py)
