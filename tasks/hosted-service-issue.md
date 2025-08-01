# Feature: Hosted SaaS Version on Fly.io

## Overview
Create a hosted version of Deja View that allows users to use the service without managing their own Chroma API keys. Deploy as a multi-tenant SaaS on Fly.io.

## Motivation
- Many users want to try the service without setting up Chroma Cloud
- Reduce friction for GitHub Action adoption
- Enable monetization through tiered pricing
- Provide better user experience with centralized management

## Proposed Architecture

### Multi-Tenant Design
- Single Chroma instance with per-repository collections
- Collection naming: `repo_{user_id}_{owner}_{repo}`
- Complete data isolation between users
- PostgreSQL for user management and metadata

### Authentication
- GitHub App for authentication (not OAuth)
- JWT tokens for API access
- Installation-based permissions
- Support for organizations

### Key Components
1. **Database Models**
   - User (GitHub ID, installation ID, subscription tier)
   - Repository (owner, repo, collection name, indexed date)
   - Usage (API calls, repositories indexed)

2. **Service Layer**
   - Extended `SimilarityService` with tenant awareness
   - Collection lifecycle management
   - Rate limiting per tier

3. **API Changes**
   - Authentication middleware
   - Tenant resolution from JWT
   - Modified endpoints to use user context

4. **Deployment**
   - Fly.io with PostgreSQL
   - Environment-based configuration
   - Secrets management for keys

## Implementation Plan

### Phase 1: MVP
- [ ] Basic multi-tenant support
- [ ] GitHub App authentication
- [ ] Simple web UI for repository management
- [ ] Free tier with 3 repositories, 100 issues each

### Phase 2: Production Ready
- [ ] Subscription tiers (Free, Pro, Enterprise)
- [ ] Rate limiting and usage tracking
- [ ] Billing integration (Stripe)
- [ ] Admin dashboard

### Phase 3: Advanced Features
- [ ] GitHub webhooks for real-time updates
- [ ] Team/organization support
- [ ] API keys for programmatic access
- [ ] Analytics and insights

## Configuration

### Environment Variables
```
DATABASE_URL=postgres://...
CHROMA_API_KEY=<hosted-key>
CHROMA_TENANT=<hosted-tenant>
GITHUB_APP_ID=<app-id>
GITHUB_APP_PRIVATE_KEY=<private-key>
JWT_SECRET=<secret>
```

### Subscription Tiers
| Tier | Repositories | Issues/Repo | API Calls/Min |
|------|-------------|-------------|---------------|
| Free | 3 | 100 | 10 |
| Pro | 50 | 1,000 | 100 |
| Enterprise | 500 | 10,000 | 1,000 |

## Security Considerations
- Data isolation via separate Chroma collections
- Repository access validation
- Encrypted storage of GitHub tokens
- Rate limiting to prevent abuse
- Regular security audits

## Migration Path
- Existing users can continue self-hosting
- Import tool for migrating self-hosted data
- Maintain backward compatibility

## Success Metrics
- Number of active users
- Repositories indexed
- API usage patterns
- Conversion rate to paid tiers

## Questions to Resolve
1. Pricing model - per repo or per user?
2. How to handle private repositories?
3. Webhook strategy for real-time updates?
4. Free tier limits?
5. Data retention policy?

## References
- [Fly.io PostgreSQL](https://fly.io/docs/postgres/)
- [GitHub Apps Documentation](https://docs.github.com/en/developers/apps)
- [Chroma Multi-tenancy Best Practices](https://docs.trychroma.com/guides)