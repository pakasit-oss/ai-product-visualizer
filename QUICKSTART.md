# Quick Start Guide - 5 Minutes Setup

Get your first AI-generated lifestyle image in 5 minutes!

## Step 1: Install (30 seconds)

```bash
pip install requests
```

That's it! Only one dependency needed.

## Step 2: Get API Key (2 minutes)

1. Go to [Replicate](https://replicate.com)
2. Sign up / Log in
3. Go to [API Tokens](https://replicate.com/account/api-tokens)
4. Copy your token

## Step 3: Configure (1 minute)

Open `config.json` and add your API key:

```json
{
  "replicate": {
    "api_token": "PASTE_YOUR_TOKEN_HERE"
  }
}
```

## Step 4: Add Product Image (30 seconds)

1. Put your product image in `products/` folder
2. Example: `products/my_sandals.jpg`

## Step 5: Configure Product (1 minute)

In `config.json`, update the products section:

```json
{
  "products": [
    {
      "image": "products/my_sandals.jpg",
      "product_type": "brown leather sandals",
      "template": "thai_woman_casual",
      "quality_preset": "balanced",
      "num_outputs": 2,
      "enabled": true
    }
  ]
}
```

## Step 6: Run! (30 seconds)

```bash
python run_workflow.py
```

Wait 30-60 seconds and check `outputs/` folder for your generated images!

---

## Full Example Config

Here's a complete `config.json` example:

```json
{
  "replicate": {
    "api_token": "r8_YOUR_TOKEN_HERE"
  },

  "paths": {
    "input_folder": "products",
    "output_folder": "outputs",
    "results_log": "batch_results.json"
  },

  "generation": {
    "default_template": "thai_woman_casual",
    "quality_preset": "balanced",
    "num_outputs": 2,
    "seed": null
  },

  "batch": {
    "max_workers": 3,
    "sequential": false,
    "timeout": 300,
    "poll_interval": 2
  },

  "products": [
    {
      "image": "products/sandals_brown.jpg",
      "product_type": "brown cross-strap sandals",
      "template": "thai_woman_casual",
      "quality_preset": "balanced",
      "num_outputs": 2,
      "enabled": true
    }
  ]
}
```

---

## What Happens Next?

The script will:
1. ✅ Upload your product image to Replicate
2. ✅ Generate lifestyle photos using AI
3. ✅ Download generated images to `outputs/`
4. ✅ Save results log to `batch_results.json`

---

## Expected Output

```
🎨 Affiliate Product Lifestyle Image Generator
============================================================
📁 Input folder: products
📁 Output folder: outputs

🚀 Starting workflow for 1 product(s)

############################################################
# Processing 1/1
############################################################

============================================================
📦 Product: brown cross-strap sandals
🖼️  Image: products/sandals_brown.jpg
🎨 Template: thai_woman_casual
⚙️  Quality: balanced
============================================================

📸 Creating prediction for: products/sandals_brown.jpg
💬 Prompt: A young Thai woman (18-25) wearing the exact same...
✅ Prediction created: abc123...

⏳ Status: processing (elapsed: 15s)
✅ Generation completed in 28s

⬇️  Downloading image 1/2...
💾 Saved: outputs\sandals_brown_20250110_143052_1.png

⬇️  Downloading image 2/2...
💾 Saved: outputs\sandals_brown_20250110_143052_2.png

🎉 Generated 2 image(s) successfully!

============================================================
📊 WORKFLOW SUMMARY
============================================================
Total products: 1
✅ Successful: 1
❌ Failed: 0
📸 Total images generated: 2

✅ Successful products:
   - brown cross-strap sandals: 2 image(s)

💾 Results saved to: batch_results.json

✅ Workflow completed!
```

---

## Next Steps

### Try Different Templates

Edit `config.json`:

```json
{
  "template": "thai_woman_standing"
}
```

See all templates:
```bash
python prompt_helper.py
```

### Process Multiple Products

Add more products to `config.json`:

```json
{
  "products": [
    {
      "image": "products/sandals.jpg",
      "product_type": "sandals",
      "template": "thai_woman_casual",
      "num_outputs": 2
    },
    {
      "image": "products/bag.jpg",
      "product_type": "leather bag",
      "template": "thai_woman_cafe",
      "num_outputs": 2
    }
  ]
}
```

### Adjust Quality

For better product preservation:
```json
{
  "quality_preset": "preserve_product"
}
```

For faster generation:
```json
{
  "quality_preset": "fast"
}
```

---

## Troubleshooting

### "API Error 401"
→ Check your API token in config.json

### "Image file not found"
→ Verify file exists: `ls products/`

### Product doesn't look right
→ Try quality preset: `"preserve_product"`

---

## Cost

Approximate cost:
- 1 image = ~$0.005-0.01
- 10 images = ~$0.05-0.10
- 100 images = ~$0.50-1.00

Check latest: [Replicate Pricing](https://replicate.com/stability-ai/sdxl/pricing)

---

## Full Documentation

For complete documentation, see:
- `WORKFLOW_GUIDE.md` - Complete workflow guide
- `README.md` - Project overview
- `prompts.json` - All available templates

---

**Ready to scale? Process 10-100 products at once! See `WORKFLOW_GUIDE.md` for advanced batch processing.**
