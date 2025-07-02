# Deployment Guide for Fly.io

This guide will help you deploy the Coffee Scraping API to Fly.io.

## Prerequisites

1. **Fly.io CLI**: Install the Fly.io CLI tool
   ```bash
   # macOS
   brew install flyctl
   
   # Windows
   powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"
   
   # Linux
   curl -L https://fly.io/install.sh | sh
   ```

2. **Login to Fly.io**:
   ```bash
   fly auth login
   ```

## Deployment Steps

### 1. Initialize the App (First Time Only)

If this is your first deployment, you'll need to create the app:

```bash
fly apps create icb-backend-v2
```

### 2. Set Environment Variables

The application requires several environment variables to function properly. Set them using Fly.io secrets:

```bash
# Required: Supabase configuration
fly secrets set SUPABASE_URL=your_supabase_url
fly secrets set SUPABASE_KEY=your_supabase_key

# Optional: LLM API keys for enrichment features
fly secrets set OPENAI_API_KEY=your_openai_api_key
fly secrets set DEEPSEEK_API_KEY=your_deepseek_api_key

# Optional: Environment and cache configuration
fly secrets set ENV=prod
fly secrets set CACHE_DIR=/app/cache

# Optional: Scraper configuration
fly secrets set USER_AGENT="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
fly secrets set REQUEST_TIMEOUT=30
```

**Note**: The `SUPABASE_URL` and `SUPABASE_KEY` are required for the application to work. The LLM API keys are optional but needed for product enrichment features.

### 3. Deploy the Application

From the project root directory:

```bash
fly deploy
```

This command will:
- Build the Docker image
- Push it to Fly.io
- Deploy the application

### 4. Check Deployment Status

```bash
fly status
```

### 5. View Logs

```bash
fly logs
```

## Configuration

The application is configured via the `fly.toml` file:

- **App Name**: `icb-backend-v2`
- **Primary Region**: `iad` (Washington DC)
- **Memory**: 1024MB
- **CPU**: 1 shared CPU
- **Port**: 8000
- **Auto-scaling**: Enabled (machines start/stop based on traffic)

## Accessing Your Application

Once deployed, your application will be available at:
- **Production URL**: `https://icb-backend-v2.fly.dev`
- **API Documentation**: `https://icb-backend-v2.fly.dev/docs`
- **Health Check**: `https://icb-backend-v2.fly.dev/health`

## Useful Commands

### View App Information
```bash
fly info
```

### Scale the Application
```bash
# Scale to 2 instances
fly scale count 2

# Scale memory
fly scale memory 2048
```

### Restart the Application
```bash
fly apps restart icb-backend-v2
```

### View Resource Usage
```bash
fly status
```

### SSH into the Container (for debugging)
```bash
fly ssh console
```

## Environment Variables

The application supports the following environment variables:

- `HOST`: Server host (default: 0.0.0.0)
- `PORT`: Server port (default: 8000)
- `RELOAD`: Enable auto-reload (default: false)
- `LOG_LEVEL`: Logging level (default: info)

## Troubleshooting

### Common Issues

1. **Build Failures**: Check the build logs with `fly logs`
2. **Health Check Failures**: Ensure the `/health` endpoint is working
3. **Memory Issues**: Increase memory allocation in `fly.toml`
4. **Port Issues**: Verify the port configuration matches between `fly.toml` and your application

### Debugging

1. **View Real-time Logs**:
   ```bash
   fly logs --follow
   ```

2. **Check Application Status**:
   ```bash
   fly status
   ```

3. **SSH into Container**:
   ```bash
   fly ssh console
   ```

## Updating the Application

To update your deployed application:

1. Make your code changes
2. Commit and push to your repository
3. Run `fly deploy` again

The deployment will automatically update the running application.

## Cost Optimization

The current configuration uses:
- **Auto-scaling**: Machines start/stop based on traffic
- **Shared CPU**: More cost-effective for this workload
- **1GB Memory**: Sufficient for the scraping operations

You can adjust these settings in `fly.toml` based on your needs and budget. 