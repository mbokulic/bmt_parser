A parser for the [Blue Mountain periodicals data](https://github.com/Princeton-CDH/bluemountain-transcriptions)

# installing
`git clone` this repository and `cd` into it

Install a Python virtual environment (optional) and run it
```bash
virtualenv -p python3 venv
source venv/bin/activate
```

Install Python libraries
```bash
pip3 install -r requirements.txt
```

Download a periodical you want to parse, you will need to change the bash script to download the one you want and the output dir.
```bash
source download_from_github.sh
```

# how to use
For a partial documentation, try

```bash
python3 -m bmt_parser -h
```
