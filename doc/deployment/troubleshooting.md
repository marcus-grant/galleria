# Deployment Troubleshooting

## Common Issues

### S3 Endpoint URL Issues

**Problem**: `EndpointConnectionError` with double `https://` in URL

**Solution**: Verify environment variable format. Use either:
- Full URL: `https://bucket-name.region.provider.com`
- Bare hostname: `bucket-name.region.provider.com`

The system handles both formats automatically.

### CORS Configuration

**Problem**: `NoSuchCORSConfiguration` or web access issues

**Solution**: Use `--setup-cors` flag with deploy command:
```bash
uv run python manage.py deploy --setup-cors
```

### Bucket Access Issues

**Problem**: `NoSuchKey` or permission errors

**Solution**: 
1. Verify bucket exists in S3 console
2. Check credentials have proper access
3. Confirm bucket name matches environment variable

### Credential Issues

**Problem**: Authentication failures

**Solution**:
1. Verify environment variables are exported:
   ```bash
   echo $HETZNER_SVARTALFHEIM_S3_WEDDING_ACC_KEY
   echo $HETZNER_SVARTALFHEIM_S3_WEDDING_SEC_KEY
   ```
2. Recreate credentials if needed
3. Update password vault with new values