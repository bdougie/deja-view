# Weekly Discussions Metrics Workflow Guide

## Overview

The Weekly Discussions Metrics workflow automatically analyzes GitHub Discussions and generates comprehensive reports with community health insights.

## 🔄 Automation Schedule

**Default Schedule:** Every Monday at 9:00 AM UTC  
**Target Repository:** `continuedev/continue` (configurable)  
**Analysis Period:** 4 weeks (configurable)  
**Mentions:** @bdougie (configurable)

## 🚀 Features

### Automated Analysis
- **Week-over-week growth tracking** with trend analysis
- **Unanswered Q&A identification** for support backlog management
- **Engagement metrics** including upvotes and answer rates
- **Category distribution** for resource planning
- **Priority alerts** for high support loads (>20 unanswered discussions)

### Report Generation
- **Markdown reports** saved to `reports/` folder with date stamps
- **JSON data export** for further analysis
- **GitHub issue creation** with executive summary
- **Automatic @mentions** for stakeholder notification

### Smart Alerting
- 🚨 **High Priority**: >20 unanswered discussions
- ⚠️ **Medium Priority**: 10-20 unanswered discussions  
- ✅ **Low Priority**: <10 unanswered discussions
- 📈 **Growth Alerts**: >20% week-over-week change

## 🛠️ Manual Triggering

You can manually trigger the workflow with custom parameters:

1. Go to **Actions** → **Weekly Discussions Metrics Report**
2. Click **Run workflow**
3. Configure parameters:
   - **Repository**: `owner/repo` format (default: `continuedev/continue`)
   - **Weeks Back**: Analysis period in weeks (default: `4`)
   - **Mention User**: GitHub username to @mention (default: `bdougie`)

## 📊 Sample Output

### GitHub Issue Executive Summary
```
📊 Weekly Discussions Metrics: continuedev/continue (2025-W34)

Repository: continuedev/continue
Week Of: 2025-W34
Trend: 📈 Strong Growth
Priority: 🚨 High Priority

| Metric | Value | Change |
|--------|-------|---------|
| Total Discussions | 69 | Over 4 weeks |
| This Week | 26 | New discussions |
| Week-over-Week | +23.8% | 📈 Strong Growth |
| Unanswered Q&A/Help | 28 | Need attention |
| Answer Rate | 22.2% | Community health |
| Avg Upvotes | 1.4 | Per discussion |
```

### Automatic Actions
- ✅ **Creates GitHub issue** with comprehensive metrics
- 📁 **Saves report** to `reports/discussions-metrics-{repo}-{date}.md`
- 💾 **Commits changes** to the feature branch
- 🔔 **@mentions specified user** for notification
- 🏷️ **Auto-labels** with `discussions-metrics`, `weekly-report`, `community-health`

## 📋 Issue Labels

The workflow automatically applies these labels to created issues:
- `discussions-metrics` - Identifies automated metrics issues
- `weekly-report` - Weekly recurring analysis
- `community-health` - Community management insights

## 🔧 Customization

### Environment Variables
The workflow uses these GitHub secrets/variables:
- `GITHUB_TOKEN` - Automatically provided by GitHub Actions
- Repository permissions: `contents: read`, `issues: write`

### Workflow Configuration
Key settings in `.github/workflows/weekly-discussions-metrics.yml`:

```yaml
schedule:
  - cron: '0 9 * * 1'  # Monday 9 AM UTC

workflow_dispatch:
  inputs:
    repository: 'continuedev/continue'
    weeks_back: '4'
    mention_user: 'bdougie'
```

### Priority Thresholds
You can adjust these in the workflow file:
- **High Priority**: >20 unanswered discussions
- **Medium Priority**: 10-20 unanswered discussions
- **Growth Alert**: >±20% week-over-week change

## 📈 Use Cases

### Community Managers
- **Weekly health checks** with automated reporting
- **Support backlog monitoring** with priority alerts
- **Engagement trend tracking** over time
- **Stakeholder updates** via @mentions

### Project Maintainers
- **Resource planning** based on discussion volume
- **Support gap identification** through answer rates
- **Community growth insights** with trend analysis

### Organizations
- **Multi-repository monitoring** by changing target repo
- **Automated reporting** for leadership updates
- **Community health dashboards** using generated data

## 🚨 Alert Scenarios

### High Priority Alert (>20 unanswered)
Creates additional comment:
> 🚨 **High Priority Alert**: This repository has 28 unanswered discussions that may need attention.
> 
> Consider:
> - Reviewing recent unanswered Help discussions  
> - Scaling community moderation resources
> - Updating documentation for common questions

### Growth Spike Alert (>20% change)
Includes in summary:
> 📈 **Significant Growth**: Consider scaling moderation resources

## 🔄 Next Steps

After each report:
1. **Review the GitHub issue** for key insights
2. **Check unanswered discussions** if priority is high
3. **Plan resource allocation** based on trends
4. **Update documentation** for common questions
5. **Monitor next week's report** for improvements

## 📝 Report Archive

All reports are automatically saved to:
- `reports/discussions-metrics-{owner-repo}-{YYYY-MM-DD}.md`
- Includes full analysis, recommendations, and actionable insights
- Linked from GitHub issues for easy access

---

*Workflow powered by [deja-view](https://github.com/bdougie/deja-view) discussions metrics*