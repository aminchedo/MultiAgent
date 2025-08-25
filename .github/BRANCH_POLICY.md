# Branch Management Policy

## Overview
This document outlines the branch management strategy for the MultiAgent repository to maintain a clean and organized codebase.

## Branch Strategy

### Main Branch (`main`)
- **Protected branch** - all changes must go through Pull Requests
- **Always deployable** - main branch should always be in a working state
- **Source of truth** - all feature branches should be created from main

### Feature Branches
- **Naming Convention**: `cursor/feature-description-shortid`
- **Lifecycle**: Create → Develop → PR → Merge → Auto-delete
- **Maximum lifetime**: 30 days (will be flagged for review)

## Automated Cleanup Process

### When Branches Are Deleted
1. **Immediately after PR merge** - merged branches are automatically deleted
2. **Weekly cleanup** - Sundays at 2 AM UTC for any missed branches  
3. **Manual trigger** - Can be run on-demand via GitHub Actions

### Cleanup Criteria
✅ Branch is fully merged into main  
✅ Branch follows naming convention `cursor/*`  
✅ No open PRs reference the branch  
✅ Branch is older than 1 day (safety buffer)  

### Protected Branches
❌ `main` - Never deleted  
❌ `develop` - If it exists  
❌ Branches with open PRs  
❌ Recently created branches (< 24 hours)  

## Manual Branch Management

### Cleanup Commands
```bash
# List merged branches
git branch -r --merged main | grep -v "main\|HEAD"

# Delete specific branch
git push --delete origin branch-name

# Bulk cleanup (use with caution)
git branch -r --merged main | grep -v "main\|HEAD" | sed 's/origin\///' | xargs -n 1 git push --delete origin

# Clean local tracking
git remote prune origin
```

### Emergency Recovery
```bash
# If branch was deleted accidentally
git reflog
git checkout -b recovered-branch <commit-hash>
git push origin recovered-branch
```

## Best Practices

### For Developers
1. **Keep branches focused** - One feature per branch
2. **Regular updates** - Rebase/merge from main frequently  
3. **Clean commits** - Use meaningful commit messages
4. **Test before PR** - Ensure functionality works
5. **Delete local branches** after merge

### For Maintainers
1. **Review PR thoroughly** before merging
2. **Squash commits** when appropriate
3. **Update main** regularly with latest changes
4. **Monitor automation** - Check cleanup workflow logs
5. **Communicate changes** - Document breaking changes

## Automation Configuration

### GitHub Actions Workflow
- **File**: `.github/workflows/cleanup-merged-branches.yml`
- **Triggers**: PR close, weekly schedule, manual
- **Permissions**: Read repository, delete branches
- **Notifications**: PR comments with cleanup summary

### Workflow Status
- ✅ **Active** - Automated cleanup is running
- 📊 **Monitoring** - Weekly reports on branch health
- 🔧 **Maintenance** - Regular updates to improve efficiency

## Repository Health Metrics

### Current Status (Last Updated)
- **Active Branches**: `git branch -r | wc -l`
- **Merged & Cleaned**: 29 branches removed in latest cleanup
- **Main Branch Health**: ✅ Clean and up-to-date
- **Last Cleanup**: Automated via GitHub Actions

### Monthly Goals
- 🎯 Keep total branches under 10
- 🎯 Average branch lifetime under 7 days
- 🎯 Zero stale branches older than 30 days
- 🎯 100% automated cleanup success rate

## Support

### Issues with Automation
1. Check GitHub Actions logs
2. Verify branch permissions
3. Contact repository maintainers
4. Review this policy document

### Policy Updates
This policy is living document and will be updated as the project evolves.

---
*Last updated: $(date)*  
*Automated cleanup active: ✅*