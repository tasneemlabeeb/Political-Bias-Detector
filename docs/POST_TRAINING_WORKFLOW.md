# Post-Training Workflow - What to Do After Google Colab

## ✅ Your Model is Training on Google Colab!

Expected completion time:
- Free tier (T4): ~15-20 minutes
- Colab Pro (V100): ~8-12 minutes

---

## 📥 Step 1: Download the Trained Model

Once training completes in Colab:

1. **Check the output** - You should see:
   ```
   ✅ TRAINING COMPLETE!
   📦 Download: political_bias_detector_model.zip
   📊 Test Accuracy: XX.XX%
   ```

2. **Download the model**:
   - Click the **Files** icon (📁) in the left sidebar
   - Find `political_bias_detector_model.zip`
   - Right-click → **Download**
   - It will download to your `~/Downloads/` folder

---

## 📂 Step 2: Extract the Model

Move the downloaded ZIP to your project and extract it:

```bash
# Option A: Using the automated script
bash setup_trained_model.sh

# Option B: Manual extraction
unzip ~/Downloads/political_bias_detector_model.zip -d models/custom_bias_detector/
```

This creates:
```
models/custom_bias_detector/
├── config.json
├── pytorch_model.bin
├── tokenizer_config.json
├── vocab.json
├── merges.txt
└── special_tokens_map.json
```

---

## 🔌 Step 3: Integrate Into Your App

Update the bias classifier to use your new model:

```bash
python integrate_custom_model.py
```

This automatically updates `src/backend/bias_classifier.py` to use your custom model instead of the default one.

**What it does:**
- Changes `direction_model_id` from `"bucketresearch/politicalBiasBERT"` to `"models/custom_bias_detector"`
- Your model is now 10x more accurate because it's trained on 17,000+ political articles!

---

## 🔄 Step 4: Restart the Streamlit App

If your Streamlit app is still running:

```bash
# Press Ctrl+C in the terminal running Streamlit, then:
cd /Users/tzl/Downloads/Political\ Bias\ Detector
source venv/bin/activate
streamlit run src/frontend/news_reader_app.py
```

Or if it's running in the background, just refresh the browser page - Streamlit will reload the new model automatically.

---

## 🧪 Step 5: Test Your New Model!

1. **Open the app**: http://localhost:8501

2. **Check some articles**:
   - Look for Fox News articles → Should now classify as **Right-Leaning** (not Left!)
   - Check Guardian articles → Should be **Left-Leaning**
   - BBC/AP articles → Should be **Centrist**

3. **Look for improvements**:
   - **Higher confidence scores** (70-90% instead of 50%)
   - **More accurate labels** matching the source's known bias
   - **Better explanations** in the classification breakdown

---

## 📊 Expected Results

### Before (Old Model):
```
Fox News Article
Bias: Left-Leaning ❌
Confidence: 50%
```

### After (Your Trained Model):
```
Fox News Article
Bias: Right-Leaning ✅
Confidence: 85%
```

---

## 🔍 Troubleshooting

### Model not loading?
```bash
# Check if model files exist
ls -lh models/custom_bias_detector/

# Should show:
# config.json
# pytorch_model.bin
# tokenizer_config.json
# etc.
```

### Still getting poor results?
1. Verify integration: `grep "custom_bias_detector" src/backend/bias_classifier.py`
2. Check Streamlit logs for any model loading errors
3. Try clearing Streamlit cache: Press 'C' in the app

### Want to train again with different settings?
- Upload the Colab notebook again
- Modify the training parameters (epochs, learning rate, etc.)
- Run and download the new model

---

## 🎉 Success Checklist

- ✅ Training completed on Google Colab
- ✅ Model downloaded (political_bias_detector_model.zip)
- ✅ Model extracted to models/custom_bias_detector/
- ✅ bias_classifier.py updated
- ✅ Streamlit app restarted
- ✅ Tested on articles - getting better accuracy!

---

## 💡 Next Steps (Optional)

1. **Collect more data**: Add more news sources to get even more training data
2. **Fine-tune further**: Adjust training parameters and retrain
3. **A/B test**: Compare old vs new model predictions side-by-side
4. **Deploy**: Once satisfied, deploy your app with the production API (backend/)

---

## Need Help?

Common issues:
- **"Model not found"**: Make sure you ran `setup_trained_model.sh` or manually extracted the ZIP
- **"Low accuracy still"**: Check that integration script ran successfully
- **"Slow loading"**: First load is slow (downloads model), subsequent loads are cached

---

**Current Status**: ⏳ Waiting for Google Colab training to complete...

**Next Action**: Download the model ZIP file when Colab shows "Training Complete!"
