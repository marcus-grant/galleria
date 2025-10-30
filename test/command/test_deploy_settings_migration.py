"""Tests for deploy command settings migration from S3_PUBLIC_*/S3_SITE_* to S3_SITE_*/S3_PICS_*."""
import pytest
from unittest.mock import Mock, patch
from click.testing import CliRunner

from src.command.deploy import deploy


class TestDeploySettingsMigration:
    """Test deploy command with new S3_SITE_*/S3_PICS_* settings structure."""
    
    def test_is_dual_bucket_configured_with_new_pics_settings(self):
        """Test is_dual_bucket_configured() detects dual mode with new S3_PICS_* settings."""
        from src.command.deploy import is_dual_bucket_configured
        
        mock_settings = Mock()
        # New structure: S3_PICS_* settings indicate dual bucket mode
        mock_settings.S3_PICS_ENDPOINT = "https://pics.s3.example.com"
        mock_settings.S3_PICS_ACCESS_KEY = "pics-access-key"
        mock_settings.S3_PICS_SECRET_KEY = "pics-secret-key"
        mock_settings.S3_PICS_BUCKET = "my-pics-bucket"
        mock_settings.S3_PICS_REGION = "us-east-1"
        
        with patch.dict('sys.modules', {'settings': mock_settings}):
            result = is_dual_bucket_configured()
            
        assert result is True
    
    def test_is_dual_bucket_configured_with_incomplete_pics_settings(self):
        """Test is_dual_bucket_configured() returns False with incomplete S3_PICS_* settings."""
        from src.command.deploy import is_dual_bucket_configured
        
        mock_settings = Mock()
        # Incomplete S3_PICS_* settings - missing some required fields
        mock_settings.S3_PICS_ENDPOINT = "https://pics.s3.example.com"
        mock_settings.S3_PICS_ACCESS_KEY = "pics-access-key"
        mock_settings.S3_PICS_SECRET_KEY = None  # Missing
        mock_settings.S3_PICS_BUCKET = "my-pics-bucket"
        mock_settings.S3_PICS_REGION = "us-east-1"
        
        with patch.dict('sys.modules', {'settings': mock_settings}):
            result = is_dual_bucket_configured()
            
        assert result is False
    
    def test_is_dual_bucket_configured_single_bucket_mode(self):
        """Test is_dual_bucket_configured() returns False for single bucket mode."""
        from src.command.deploy import is_dual_bucket_configured
        
        mock_settings = Mock()
        # No S3_PICS_* settings - indicates single bucket mode
        mock_settings.S3_PICS_ENDPOINT = None
        mock_settings.S3_PICS_ACCESS_KEY = None
        mock_settings.S3_PICS_SECRET_KEY = None
        mock_settings.S3_PICS_BUCKET = None
        mock_settings.S3_PICS_REGION = None
        
        with patch.dict('sys.modules', {'settings': mock_settings}):
            result = is_dual_bucket_configured()
            
        assert result is False
    
    def test_deploy_single_bucket_mode_with_new_settings(self, tmp_path):
        """Test deploy command in single bucket mode using S3_SITE_* for site deployment."""
        runner = CliRunner()
        
        # Create directory structure
        prod_pics = tmp_path / "prod" / "pics"
        prod_pics.mkdir(parents=True)
        prod_site = tmp_path / "prod" / "site"
        prod_site.mkdir(parents=True)
        
        mock_settings = Mock()
        mock_settings.BASE_DIR = tmp_path
        # Single bucket mode: Only S3_SITE_* configured (no S3_PICS_*)
        mock_settings.S3_SITE_ENDPOINT = "https://s3.example.com"
        mock_settings.S3_SITE_ACCESS_KEY = "site-access-key"
        mock_settings.S3_SITE_SECRET_KEY = "site-secret-key"
        mock_settings.S3_SITE_BUCKET = "my-site-bucket"
        mock_settings.S3_SITE_REGION = "us-east-1"
        # No S3_PICS_* settings
        mock_settings.S3_PICS_ENDPOINT = None
        mock_settings.S3_PICS_ACCESS_KEY = None
        mock_settings.S3_PICS_SECRET_KEY = None
        mock_settings.S3_PICS_BUCKET = None
        mock_settings.S3_PICS_REGION = None
        
        with patch.dict('sys.modules', {'settings': mock_settings}):
            with patch('src.command.deploy.validate_s3_config', return_value=(True, "")):
                with patch('src.command.deploy.get_s3_client') as mock_get_client:
                    mock_client = Mock()
                    mock_get_client.return_value = mock_client
                    
                    with patch('src.command.deploy.examine_bucket_cors') as mock_cors:
                        mock_cors.return_value = {
                            'success': True,
                            'configured': True,
                            'needs_update': False
                        }
                        
                        with patch('src.command.deploy.deploy_directory_to_s3') as mock_deploy:
                            mock_deploy.return_value = {
                                'success': True,
                                'total_files': 3,
                                'uploaded_files': 3,
                                'skipped_files': 0,
                                'failed_files': 0,
                                'errors': []
                            }
                            
                            result = runner.invoke(deploy)
                            
                            assert result.exit_code == 0
                            assert "single bucket mode" in result.output
                            assert f"Bucket: {mock_settings.S3_SITE_BUCKET}" in result.output
                            # Both photos and site deployed to same bucket
                            assert mock_deploy.call_count == 2
                            # Verify photos deployment uses 'photos' prefix
                            photos_call = mock_deploy.call_args_list[0]
                            assert photos_call[1]['prefix'] == 'photos'
                            assert photos_call[1]['bucket'] == mock_settings.S3_SITE_BUCKET
                            # Verify site deployment uses empty prefix
                            site_call = mock_deploy.call_args_list[1]
                            assert site_call[1]['prefix'] == ''
                            assert site_call[1]['bucket'] == mock_settings.S3_SITE_BUCKET
    
    def test_deploy_dual_bucket_mode_with_new_settings(self, tmp_path):
        """Test deploy command in dual bucket mode using S3_SITE_* for site and S3_PICS_* for photos."""
        runner = CliRunner()
        
        # Create directory structure
        prod_pics = tmp_path / "prod" / "pics"
        prod_pics.mkdir(parents=True)
        prod_site = tmp_path / "prod" / "site"
        prod_site.mkdir(parents=True)
        
        mock_settings = Mock()
        mock_settings.BASE_DIR = tmp_path
        # Dual bucket mode: Both S3_SITE_* and S3_PICS_* configured
        mock_settings.S3_SITE_ENDPOINT = "https://site.s3.example.com"
        mock_settings.S3_SITE_ACCESS_KEY = "site-access-key"
        mock_settings.S3_SITE_SECRET_KEY = "site-secret-key"
        mock_settings.S3_SITE_BUCKET = "my-site-bucket"
        mock_settings.S3_SITE_REGION = "us-east-1"
        mock_settings.S3_PICS_ENDPOINT = "https://pics.s3.example.com"
        mock_settings.S3_PICS_ACCESS_KEY = "pics-access-key"
        mock_settings.S3_PICS_SECRET_KEY = "pics-secret-key"
        mock_settings.S3_PICS_BUCKET = "my-pics-bucket"
        mock_settings.S3_PICS_REGION = "us-west-2"
        
        mock_pics_client = Mock()
        mock_site_client = Mock()
        
        with patch.dict('sys.modules', {'settings': mock_settings}):
            with patch('src.command.deploy.validate_s3_config', return_value=(True, "")):
                with patch('src.command.deploy.get_s3_client') as mock_get_client:
                    # Mock different clients for pics and site buckets
                    mock_get_client.side_effect = [mock_pics_client, mock_site_client]
                    
                    with patch('src.command.deploy.examine_bucket_cors') as mock_cors:
                        mock_cors.return_value = {
                            'success': True,
                            'configured': True,
                            'needs_update': False
                        }
                        
                        with patch('src.command.deploy.deploy_directory_to_s3') as mock_deploy:
                            mock_deploy.return_value = {
                                'success': True,
                                'total_files': 3,
                                'uploaded_files': 3,
                                'skipped_files': 0,
                                'failed_files': 0,
                                'errors': []
                            }
                            
                            result = runner.invoke(deploy)
                            
                            assert result.exit_code == 0
                            assert "dual bucket mode" in result.output
                            assert f"Photos bucket: {mock_settings.S3_PICS_BUCKET}" in result.output
                            assert f"Site bucket: {mock_settings.S3_SITE_BUCKET}" in result.output
                            # Both photos and site deployed
                            assert mock_deploy.call_count == 2
                            # Verify photos deployment to pics bucket with no prefix
                            photos_call = mock_deploy.call_args_list[0]
                            assert photos_call[1]['client'] == mock_pics_client
                            assert photos_call[1]['prefix'] == ''
                            assert photos_call[1]['bucket'] == mock_settings.S3_PICS_BUCKET
                            # Verify site deployment to site bucket
                            site_call = mock_deploy.call_args_list[1]
                            assert site_call[1]['client'] == mock_site_client
                            assert site_call[1]['bucket'] == mock_settings.S3_SITE_BUCKET
    
    def test_deploy_photos_only_dual_bucket_mode(self, tmp_path):
        """Test deploy --photos-only in dual bucket mode uses S3_PICS_* settings."""
        runner = CliRunner()
        
        prod_pics = tmp_path / "prod" / "pics"
        prod_pics.mkdir(parents=True)
        
        mock_settings = Mock()
        mock_settings.BASE_DIR = tmp_path
        # Dual bucket mode configuration
        mock_settings.S3_SITE_ENDPOINT = "https://site.s3.example.com"
        mock_settings.S3_SITE_ACCESS_KEY = "site-access-key"
        mock_settings.S3_SITE_SECRET_KEY = "site-secret-key"
        mock_settings.S3_SITE_BUCKET = "my-site-bucket"
        mock_settings.S3_SITE_REGION = "us-east-1"
        mock_settings.S3_PICS_ENDPOINT = "https://pics.s3.example.com"
        mock_settings.S3_PICS_ACCESS_KEY = "pics-access-key"
        mock_settings.S3_PICS_SECRET_KEY = "pics-secret-key"
        mock_settings.S3_PICS_BUCKET = "my-pics-bucket"
        mock_settings.S3_PICS_REGION = "us-west-2"
        
        mock_pics_client = Mock()
        mock_site_client = Mock()
        
        with patch.dict('sys.modules', {'settings': mock_settings}):
            with patch('src.command.deploy.validate_s3_config', return_value=(True, "")):
                with patch('src.command.deploy.get_s3_client') as mock_get_client:
                    mock_get_client.side_effect = [mock_pics_client, mock_site_client]
                    
                    with patch('src.command.deploy.examine_bucket_cors') as mock_cors:
                        mock_cors.return_value = {
                            'success': True,
                            'configured': True,
                            'needs_update': False
                        }
                        
                        with patch('src.command.deploy.deploy_directory_to_s3') as mock_deploy:
                            mock_deploy.return_value = {
                                'success': True,
                                'total_files': 5,
                                'uploaded_files': 5,
                                'skipped_files': 0,
                                'failed_files': 0,
                                'errors': []
                            }
                            
                            result = runner.invoke(deploy, ['--photos-only'])
                            
                            assert result.exit_code == 0
                            # Only photos deployment
                            assert mock_deploy.call_count == 1
                            # Photos go to pics bucket with no prefix
                            photos_call = mock_deploy.call_args_list[0]
                            assert photos_call[1]['client'] == mock_pics_client
                            assert photos_call[1]['bucket'] == mock_settings.S3_PICS_BUCKET
                            assert photos_call[1]['prefix'] == ''
    
    def test_deploy_site_only_dual_bucket_mode(self, tmp_path):
        """Test deploy --site-only in dual bucket mode uses S3_SITE_* settings."""
        runner = CliRunner()
        
        prod_site = tmp_path / "prod" / "site"
        prod_site.mkdir(parents=True)
        
        mock_settings = Mock()
        mock_settings.BASE_DIR = tmp_path
        # Dual bucket mode configuration
        mock_settings.S3_SITE_ENDPOINT = "https://site.s3.example.com"
        mock_settings.S3_SITE_ACCESS_KEY = "site-access-key"
        mock_settings.S3_SITE_SECRET_KEY = "site-secret-key"
        mock_settings.S3_SITE_BUCKET = "my-site-bucket"
        mock_settings.S3_SITE_REGION = "us-east-1"
        mock_settings.S3_PICS_ENDPOINT = "https://pics.s3.example.com"
        mock_settings.S3_PICS_ACCESS_KEY = "pics-access-key"
        mock_settings.S3_PICS_SECRET_KEY = "pics-secret-key"
        mock_settings.S3_PICS_BUCKET = "my-pics-bucket"
        mock_settings.S3_PICS_REGION = "us-west-2"
        
        mock_pics_client = Mock()
        mock_site_client = Mock()
        
        with patch.dict('sys.modules', {'settings': mock_settings}):
            with patch('src.command.deploy.validate_s3_config', return_value=(True, "")):
                with patch('src.command.deploy.get_s3_client') as mock_get_client:
                    mock_get_client.side_effect = [mock_pics_client, mock_site_client]
                    
                    with patch('src.command.deploy.examine_bucket_cors') as mock_cors:
                        mock_cors.return_value = {
                            'success': True,
                            'configured': True,
                            'needs_update': False
                        }
                        
                        with patch('src.command.deploy.deploy_directory_to_s3') as mock_deploy:
                            mock_deploy.return_value = {
                                'success': True,
                                'total_files': 3,
                                'uploaded_files': 3,
                                'skipped_files': 0,
                                'failed_files': 0,
                                'errors': []
                            }
                            
                            result = runner.invoke(deploy, ['--site-only'])
                            
                            assert result.exit_code == 0
                            # Only site deployment
                            assert mock_deploy.call_count == 1
                            # Site goes to site bucket
                            site_call = mock_deploy.call_args_list[0]
                            assert site_call[1]['client'] == mock_site_client
                            assert site_call[1]['bucket'] == mock_settings.S3_SITE_BUCKET
                            assert site_call[1]['prefix'] == ''


class TestSettingsValidation:
    """Test S3 settings validation with new naming structure."""
    
    def test_validate_s3_config_with_site_settings_only(self):
        """Test validate_s3_config works with only S3_SITE_* settings (single bucket mode)."""
        from src.command.upload_photos import validate_s3_config
        
        mock_settings = Mock()
        # Only S3_SITE_* settings configured
        mock_settings.S3_SITE_ENDPOINT = "https://s3.example.com"
        mock_settings.S3_SITE_ACCESS_KEY = "site-access-key"
        mock_settings.S3_SITE_SECRET_KEY = "site-secret-key"
        mock_settings.S3_SITE_BUCKET = "my-site-bucket"
        mock_settings.S3_SITE_REGION = "us-east-1"
        
        is_valid, error_msg = validate_s3_config(mock_settings)
        
        assert is_valid is True
        assert error_msg == ""
    
    def test_validate_s3_config_with_incomplete_site_settings(self):
        """Test validate_s3_config fails with incomplete S3_SITE_* settings."""
        from src.command.upload_photos import validate_s3_config
        
        mock_settings = Mock()
        # Incomplete S3_SITE_* settings
        mock_settings.S3_SITE_ENDPOINT = "https://s3.example.com"
        mock_settings.S3_SITE_ACCESS_KEY = None  # Missing
        mock_settings.S3_SITE_SECRET_KEY = "site-secret-key"
        mock_settings.S3_SITE_BUCKET = "my-site-bucket"
        mock_settings.S3_SITE_REGION = "us-east-1"
        # No S3_PUBLIC_* settings either (so no fallback)
        mock_settings.S3_PUBLIC_ENDPOINT = None
        mock_settings.S3_PUBLIC_ACCESS_KEY = None
        mock_settings.S3_PUBLIC_SECRET_KEY = None
        mock_settings.S3_PUBLIC_BUCKET = None
        mock_settings.S3_PUBLIC_REGION = None
        
        is_valid, error_msg = validate_s3_config(mock_settings)
        
        assert is_valid is False
        assert "S3_SITE_ACCESS_KEY" in error_msg or "S3_PUBLIC_ACCESS_KEY" in error_msg