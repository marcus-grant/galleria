from unittest.mock import Mock, patch
from src.services.template_renderer import TemplateRenderer


def test_template_renderer_initializes_jinja2_environment():
    """Test that renderer initializes Jinja2 environment with template directory"""
    renderer = TemplateRenderer()
    
    assert renderer.env is not None
    assert renderer.env.loader is not None


def test_template_renderer_calls_correct_template_for_gallery():
    """Test that render_gallery calls the correct template with provided data"""
    renderer = TemplateRenderer()
    
    # Mock the template
    mock_template = Mock()
    mock_template.render.return_value = "<html>Gallery HTML</html>"
    
    # Mock the environment to return our mock template
    with patch.object(renderer.env, 'get_template', return_value=mock_template) as mock_get:
        photo_data = {"photos": [{"filename": "test.jpg"}]}
        html = renderer.render_gallery(photo_data)
        
        # Verify correct template was requested
        mock_get.assert_called_once_with("gallery.j2.html")
        
        # Verify template was rendered with data plus generated PICS_BASE_URL
        call_args = mock_template.render.call_args[0][0]
        assert 'PICS_BASE_URL' in call_args
        assert call_args['PICS_BASE_URL'] is not None  # Should be generated, not None
        
        # Verify we got the rendered result
        assert html == "<html>Gallery HTML</html>"


def test_template_renderer_saves_rendered_html_to_file():
    """Test that renderer can save rendered HTML to output directory"""
    renderer = TemplateRenderer()
    
    # Mock file operations
    mock_open = Mock()
    mock_file = Mock()
    mock_open.return_value.__enter__ = Mock(return_value=mock_file)
    mock_open.return_value.__exit__ = Mock(return_value=None)
    
    with patch('builtins.open', mock_open):
        with patch('pathlib.Path.mkdir') as mock_mkdir:
            renderer.save_html("<html>Test</html>", "prod/site/gallery.html")
            
            # Verify directory was created
            mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
            
            # Verify file was opened for writing
            mock_open.assert_called_once_with("prod/site/gallery.html", "w")
            
            # Verify HTML was written
            mock_file.write.assert_called_once_with("<html>Test</html>")


def test_template_renderer_generates_pics_base_url_for_dual_bucket():
    """Test that renderer generates correct PICS_BASE_URL for dual bucket setup"""
    renderer = TemplateRenderer()
    
    # Mock dual bucket settings
    with patch('src.services.template_renderer.settings') as mock_settings:
        mock_settings.S3_PICS_ENDPOINT = "https://fsn1.your-objectstorage.com"
        mock_settings.S3_PICS_ACCESS_KEY = "access_key"
        mock_settings.S3_PICS_SECRET_KEY = "secret_key"
        mock_settings.S3_PICS_BUCKET = "galleria-pics"
        mock_settings.S3_PICS_REGION = "eu-central-1"
        
        # Mock is_dual_bucket_configured to return True
        with patch('src.services.template_renderer.is_dual_bucket_configured', return_value=True):
            mock_template = Mock()
            mock_template.render.return_value = "<html>Gallery HTML</html>"
            
            with patch.object(renderer.env, 'get_template', return_value=mock_template):
                photo_data = {"photos": [{"filename": "test.jpg"}]}
                renderer.render_gallery(photo_data)
                
                # Verify PICS_BASE_URL was generated correctly for dual bucket
                call_args = mock_template.render.call_args[0][0]
                expected_url = "https://galleria-pics.fsn1.your-objectstorage.com"
                assert call_args['PICS_BASE_URL'] == expected_url


def test_template_renderer_generates_pics_base_url_for_single_bucket():
    """Test that renderer generates correct PICS_BASE_URL for single bucket setup"""
    renderer = TemplateRenderer()
    
    # Mock single bucket settings (no S3_PICS_* configured)
    with patch('src.services.template_renderer.settings') as mock_settings:
        mock_settings.S3_SITE_ENDPOINT = "https://fsn1.your-objectstorage.com"
        mock_settings.S3_SITE_BUCKET = "galleria-site"
        
        # Mock is_dual_bucket_configured to return False
        with patch('src.services.template_renderer.is_dual_bucket_configured', return_value=False):
            mock_template = Mock()
            mock_template.render.return_value = "<html>Gallery HTML</html>"
            
            with patch.object(renderer.env, 'get_template', return_value=mock_template):
                photo_data = {"photos": [{"filename": "test.jpg"}]}
                renderer.render_gallery(photo_data)
                
                # Verify PICS_BASE_URL was generated correctly for single bucket
                call_args = mock_template.render.call_args[0][0]
                expected_url = "https://galleria-site.fsn1.your-objectstorage.com/pics"
                assert call_args['PICS_BASE_URL'] == expected_url