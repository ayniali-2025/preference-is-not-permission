# GitHub upload instructions

1. In the existing repository select the `pinp-v1.3-update` branch. Confirm the displayed name **before** uploading.
2. Unzip this package locally. Upload the **contents** of `PINP_v1.3_GitHub_UPLOAD` to the repository root using **Add file > Upload files**. The README will replace the working branch README (the original remains on `main` and the archive branch). GitHub's web upload may not handle nested folders reliably: prefer Git command line or GitHub Desktop to retain paths. 
3. Review the diff and confirm the archive branch remains unchanged.
4. Run `python -m pip install -r requirements-analysis.txt && python analysis/verify_release.py` locally or in CI.
5. Review manuscript publicity/anonymity rules before uploading the PDF or adding a preprint link. The PDF is **not** included.
6. Open a pull request `pinp-v1.3-update` → `main` and merge only after checks/review.

Git CLI option (from cloned repo, on `pinp-v1.3-update` branch):

```bash
cp -r /path/to/PINP_v1.3_GitHub_UPLOAD/. .
git status
git add README.md requirements-analysis.txt requirements-experiment.txt analysis docs experiments protocols results
git diff --cached --stat
git commit -m "Add frozen PINP v1.3 confirmatory research archive"
git push -u origin pinp-v1.3-update
```

**Do not execute the historical notebook top-to-bottom without reviewing it:** earlier cells can overwrite output paths or load different experimental versions. Do not force-push or rewrite historical tags.
