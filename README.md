# YAML Generator

This project creates YAML configuration files for the MME module based on a JSON template.

## Requirements

- Python3 should be installed.
- Install virtual env package
```
apt-get install python3-venv
```

## Usage

- Create virtual enviroment
```
python3 -m venv env
```

- activate the enviroment
```
source env/bin/activate
```

- Install the requirements
```
pip install -r requirements.txt
```

- To start YAML generation, make sure the contents of <code>5G.csv</code> are correct
```
./YamlGen.py 5G.csv
```
