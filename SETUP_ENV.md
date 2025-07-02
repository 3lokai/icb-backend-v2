# Environment Variables Setup Guide

This guide helps you set up the required environment variables for deploying the Coffee Scraping API to Fly.io.

## Required Environment Variables

### 1. Supabase Configuration (Required)

You need to set up Supabase credentials for the application to work:

```bash
# Set your Supabase URL and API key
fly secrets set SUPABASE_URL=https://your-project.supabase.co
fly secrets set SUPABASE_KEY=your_supabase_anon_key
```

**How to get these values:**
1. Go to your Supabase project dashboard
2. Navigate to Settings → API
3. Copy the "Project URL" and "anon public" key

### 2. Optional Environment Variables

#### LLM API Keys (for product enrichment)
```bash
# OpenAI API key for product enrichment
fly secrets set OPENAI_API_KEY=sk-your-openai-api-key

# DeepSeek API key (alternative to OpenAI)
fly secrets set DEEPSEEK_API_KEY=your-deepseek-api-key
```

#### Environment Configuration
```bash
# Set environment to production
fly secrets set ENV=prod

# Set cache directory (default: /app/cache)
fly secrets set CACHE_DIR=/app/cache
```

#### Scraper Configuration
```bash
# Custom user agent (optional)
fly secrets set USER_AGENT="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

# Request timeout in seconds (default: 30)
fly secrets set REQUEST_TIMEOUT=30
```

## Quick Setup Commands

Run these commands in your terminal to set up all required variables:

```bash
# Required variables (replace with your actual values)
fly secrets set SUPABASE_URL=https://your-project.supabase.co
fly secrets set SUPABASE_KEY=your_supabase_anon_key

# Optional variables (uncomment and set if needed)
# fly secrets set OPENAI_API_KEY=sk-your-openai-api-key
# fly secrets set ENV=prod
```

## Verify Environment Variables

To check what environment variables are currently set:

```bash
fly secrets list
```

## Update Environment Variables

To update an existing environment variable:

```bash
fly secrets set VARIABLE_NAME=new_value
```

## Remove Environment Variables

To remove an environment variable:

```bash
fly secrets unset VARIABLE_NAME
```

## Important Notes

1. **Security**: Environment variables set with `fly secrets` are encrypted and secure
2. **Restart Required**: After setting new environment variables, restart your app:
   ```bash
   fly apps restart icb-backend-v2
   ```
3. **Local Development**: For local development, create a `.env` file in your project root with the same variables
4. **API Keys**: Keep your API keys secure and never commit them to version control

## Troubleshooting

### Application Won't Start
If your application fails to start, check the logs:
```bash
fly logs
```

Common issues:
- Missing `SUPABASE_URL` or `SUPABASE_KEY`
- Invalid API keys
- Network connectivity issues

### Environment Variables Not Loading
If environment variables aren't being loaded:
1. Verify they're set correctly: `fly secrets list`
2. Restart the application: `fly apps restart icb-backend-v2`
3. Check the application logs: `fly logs --follow` 