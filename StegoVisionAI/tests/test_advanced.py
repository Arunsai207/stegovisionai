from io import BytesIO
from PIL import Image
from app.advanced import compare_images, similarity

def png(color, size=(64, 64)):
    b = BytesIO()
    Image.new("RGB", size, color).save(b, "PNG")
    return b.getvalue()

def test_identical_images_are_identified_by_hash():
    data = png((20, 80, 140))
    result = compare_images(data, data)
    assert result["identical_files"] is True
    assert result["image_a"]["sha256"] == result["image_b"]["sha256"]

def test_changed_image_is_compared_without_claiming_tampering():
    result = compare_images(png((20, 80, 140)), png((180, 80, 20)))
    assert result["identical_files"] is False
    assert "limitations" in result
    assert 0 <= result["visual_similarity"] <= 100

def test_similarity_method_is_labeled_as_coarse():
    result = similarity(png((10, 20, 30)), png((10, 20, 30)))
    assert "coarse" in result["interpretation"].lower()
