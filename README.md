# tybalt-analysis
Data, python scripts and results for replicating some of the analysis in [Tybalt](https://github.com/greenelab/tybalt).

### Folder structure
- scripts: python code and some plots
- data, models: input data
- results: gene lists and pathway analysis results

### Getting started
Install dependencies:
```
conda env create --force --file environment.yml
source activate tybalt
```

Run scripts:
```
cd scripts

# patient sex
python sex.py

# cancer subtypes
python hgsc_subtypes_tybalt.py
```
