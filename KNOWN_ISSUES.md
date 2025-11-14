# Known Issues

## Artifact Sharing Between Jobs

**Status:** In Progress
**Issue:** Individual scan job artifacts are not being successfully pulled by the aggregation job.

### Problem
When individual scan jobs push their markdown reports using:
```bash
artifact push workflow scan-results/${SAFE_IMAGE_NAME}.md
```

The final aggregation job cannot pull them:
```bash
artifact pull workflow all-scan-results --destination all-scan-results
```

Error message:
```
Error pulling artifact: failed to generate signed URLs - hub returned 404 status code
```

### Root Cause
The `artifact push workflow` command from matrix jobs may not be persisting artifacts at the workflow level in the expected location, or there's a timing issue where the aggregation job starts before all artifacts are uploaded.

### Current Workaround
The pipeline currently generates a REPORT.md with only the header and footer, missing the individual scan results.

### Potential Solutions

1. **Use job-level artifacts**: Instead of workflow-level, each job could push to its own artifacts, and the aggregation job could iterate through all job IDs to pull them individually.

2. **Use cache instead of artifacts**: Store scan results in Semaphore cache which has better support for sharing between jobs.

3. **Add explicit dependencies**: Make the aggregation job explicitly depend on all scan jobs completing.

4. **Use a different aggregation method**: Have each job append to a single shared file instead of individual files.

### Next Steps
- Test with cache-based approach
- Check Semaphore documentation for workflow artifact behavior with matrix jobs
- Consider using promotion/pipeline chaining instead of blocks

## Downloading Reports

Currently, downloading the REPORT.md requires:
1. Access to Semaphore web UI
2. Navigate to workflow → artifacts
3. Manual download

The API-based download scripts require proper authentication which is redirecting to login page.
