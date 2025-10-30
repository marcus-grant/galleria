"""Integration tests for efficient batch processing metadata."""
import pytest
import json
from pathlib import Path
from PIL import Image

from src.services.file_processing import process_dual_photo_collection


class TestBatchMetadataEfficiency:
    """Test that batch processing generates efficient partial metadata files."""
    
    def test_partial_files_contain_only_current_batch(self, tmp_path):
        """Test that partial metadata files contain only photos from current batch, not cumulative."""
        # Create test directories
        full_dir = tmp_path / "full"
        web_dir = tmp_path / "web"
        output_dir = tmp_path / "output"
        
        full_dir.mkdir()
        web_dir.mkdir()
        output_dir.mkdir()
        
        # Create 6 photos to span 2 batches (batch size 3)
        photo_names = [f"IMG_{i:03d}.jpg" for i in range(1, 7)]
        for name in photo_names:
            Image.new('RGB', (100, 100)).save(full_dir / name)
            Image.new('RGB', (50, 50)).save(web_dir / name)
        
        # Process with batch size 3
        result = process_dual_photo_collection(
            full_dir, web_dir, output_dir, 
            collection_name="test",
            batch_size=3
        )
        
        # Verify processing succeeded
        assert result["total_processed"] == 6
        
        # Check partial files exist
        partial1 = output_dir / "gallery-metadata.part001.json"
        partial2 = output_dir / "gallery-metadata.part002.json"
        
        assert partial1.exists(), "First partial file should exist"
        assert partial2.exists(), "Second partial file should exist"
        
        # Load partial metadata
        with open(partial1) as f:
            batch1_data = json.load(f)
        with open(partial2) as f:
            batch2_data = json.load(f)
        
        # CRITICAL TEST: Each partial should contain only 3 photos, not cumulative
        assert len(batch1_data["photos"]) == 3, "First batch should contain exactly 3 photos, not cumulative"
        assert len(batch2_data["photos"]) == 3, "Second batch should contain exactly 3 photos, not cumulative"
        
        # Verify photo paths are in correct batches (sorted order)
        batch1_paths = [Path(photo["original_path"]).name for photo in batch1_data["photos"]]
        batch2_paths = [Path(photo["original_path"]).name for photo in batch2_data["photos"]]
        
        expected_batch1 = ["IMG_001.jpg", "IMG_002.jpg", "IMG_003.jpg"]
        expected_batch2 = ["IMG_004.jpg", "IMG_005.jpg", "IMG_006.jpg"]
        
        assert batch1_paths == expected_batch1, f"Batch 1 should contain {expected_batch1}, got {batch1_paths}"
        assert batch2_paths == expected_batch2, f"Batch 2 should contain {expected_batch2}, got {batch2_paths}"
    
    def test_merging_partials_produces_complete_metadata(self, tmp_path):
        """Test that merging partial files produces same result as single-pass processing."""
        pytest.skip("Function merge_partial_metadata_files() not yet implemented")
        
        # This test will be implemented once merge function exists
        # Should verify that:
        # 1. merge_partial_metadata_files() combines all partials correctly
        # 2. Final metadata contains all 6 photos
        # 3. Photo order and data integrity is preserved
    
    def test_batch_processing_performance_is_linear(self, tmp_path):
        """Test that processing time scales linearly, not quadratically."""
        pytest.skip("Performance optimization not yet implemented")
        
        # This test will measure processing time for different photo counts
        # and verify O(N) scaling instead of O(N²)
    
    def test_resume_functionality_with_existing_partials(self, tmp_path):
        """Test that resume flag properly continues from existing partial files."""
        pytest.skip("Resume functionality not yet implemented")
        
        # This test will verify:
        # 1. Resume detects existing partials
        # 2. Continues processing from last complete batch
        # 3. Final result is same as single-pass processing