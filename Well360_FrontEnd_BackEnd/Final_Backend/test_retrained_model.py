"""
Quick test script to verify the retrained hydration model
"""
import os
import random
from hydration.imagePredict_mobilenet import predict_single

# Get some random test images
data_dir = "data"
test_images = []

for cls in ["Dehydrate", "Normal"]:
    cls_path = os.path.join(data_dir, cls)
    images = [os.path.join(cls_path, f) for f in os.listdir(cls_path) 
              if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    test_images.extend(random.sample(images, min(3, len(images))))

print("Testing retrained hydration model...\n")
print("=" * 60)

for img_path in test_images:
    print(f"\n📸 Image: {os.path.basename(img_path)}")
    print(f"   Actual class: {os.path.dirname(img_path).split(os.sep)[-1]}")
    
    result = predict_single(img_path)
    
    if "error" in result:
        print(f"   ❌ Error: {result['error']}")
    else:
        print(f"   🔍 Prediction: {result['prediction']}")
        print(f"   💧 Hydration Score: {result['hydration_score']}/100")
        print(f"   📊 Confidence: {result['confidence']:.2%}")
        print(f"   💾 Saved to: {os.path.basename(result['saved_image_path'])}")

print("\n" + "=" * 60)
print("✅ Model test complete!")
