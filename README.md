# YAML Generator

This project creates YAML configuration files for the MME module based on a JSON template.

## Requirements

- Python3 should be installed.
- Install the python module requirements by running this command after pulling the project:
```
pip install -r requirements.txt
```

## Usage

- Ensure the TAC list and IPs are up-to-date in the <code>ips.py</code> file. 
- To start YAML generation, make sure the contents of <code>mme_list_production.csv</code> is correct, then run the bash script:
```
./run.sh mme_list_production.csv
```

## Format

The format of the <code>mme_list_production.csv</code> file should be as below:

```
MME name	OM	S1MME	S11	DB	TAC
```

For example:
```
srv13-mme-2-tac2-secondary	192.168.101.21	192.168.102.99	192.168.63.99	192.168.88.99	2
```

Multiple TACs for one MME should be seperated by dash. For example <code>11-12-14</code>
```
srv14-mme-7-TAC11-12-14-Primary		192.168.101.46	192.168.102.136	192.168.63.136	192.168.88.136	11-12-14
```
