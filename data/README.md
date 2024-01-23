# Data Versioning with dvc

## Add data (run also if it is already tracked)
```dvc add data/FILENAME```

## Commit data
Commit first the data and then the dvc file
```git add data/FILENAME```
```git commit -m "Add data"```

## Push data
```dvc push```