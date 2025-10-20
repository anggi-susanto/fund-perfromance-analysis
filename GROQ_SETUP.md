# 🚀 Quick Setup: Get Your Free Groq API Key

## Why Groq?
- ✅ **Completely FREE** (no credit card needed)
- ✅ **Super FAST** (faster than OpenAI)
- ✅ **No local installation** (cloud-based)
- ✅ **Generous limits** (14,400 requests/day free tier)

---

## Step-by-Step Setup (2 minutes)

### 1. Sign Up for Groq

1. Open your browser and go to: **https://console.groq.com**
2. Click **"Sign Up"** 
3. Sign up with:
   - Email address, OR
   - Google account, OR
   - GitHub account
4. Verify your email (check spam folder if needed)

### 2. Create API Key

1. After logging in, you'll see the Groq Console
2. Click on **"API Keys"** in the left sidebar
3. Click **"Create API Key"** button
4. Give it a name (e.g., "Fund Analysis Dev")
5. Click **"Create"**
6. **Copy the API key** - it looks like: `gsk_...`

⚠️ **Important:** Save this key somewhere safe! You won't be able to see it again.

### 3. Add API Key to .env File

1. Open your `.env` file in the project root
2. Find this line:
   ```
   GROQ_API_KEY=your-groq-api-key-here
   ```
3. Replace `your-groq-api-key-here` with your actual API key:
   ```
   GROQ_API_KEY=gsk_your_actual_key_here
   ```
4. Save the file

### 4. Restart Backend

```bash
cd /Users/albertwired/project/codtest/fund-perfromance-analysis
docker compose restart backend
```

### 5. Test It!

```bash
# Wait 3 seconds for backend to start
sleep 3

# Run the LLM test
docker compose exec backend python test_llm_setup.py
```

You should see:
```
✓ ALL TESTS PASSED!
🎉 Your LLM setup is ready!
```

---

## What Models Are Available?

Groq offers several models for free:

| Model | Speed | Quality | Context Window | Best For |
|-------|-------|---------|----------------|----------|
| **mixtral-8x7b-32768** | Fast | Good | 32K tokens | General use (RECOMMENDED) |
| **llama3-70b-8192** | Very Fast | Excellent | 8K tokens | Short responses |
| **llama3-8b-8192** | Fastest | Good | 8K tokens | Simple queries |

The default is `mixtral-8x7b-32768` - it's a great balance!

---

## Troubleshooting

### Issue: "API key not found"
**Solution:** Make sure you:
1. Copied the entire API key (starts with `gsk_`)
2. Saved the .env file
3. Restarted the backend: `docker compose restart backend`

### Issue: "Rate limit exceeded"
**Solution:** Free tier has limits:
- 30 requests per minute
- 14,400 requests per day
- If you hit this, wait a minute or sign up for a paid plan

### Issue: "Model not found"
**Solution:** Check your model name in .env:
```
GROQ_MODEL=mixtral-8x7b-32768
```

---

## Alternative: Use OpenAI (If You Have Credits)

If you prefer OpenAI and have credits:

1. Edit `.env`:
   ```bash
   # Comment out Groq
   # GROQ_API_KEY=...
   
   # Uncomment OpenAI
   OPENAI_API_KEY=sk-your-openai-key
   LLM_PROVIDER=openai
   ```

2. Restart backend

---

## Next Steps After Setup

Once your LLM is working:

1. ✅ Generate test PDF:
   ```bash
   cd files
   python create_sample_pdf.py
   ```

2. ✅ Test document upload:
   ```bash
   curl -X POST "http://localhost:8000/api/documents/upload" \
     -F "file=@Sample_Fund_Performance_Report.pdf" \
     -F "fund_id=1"
   ```

3. ✅ Test chat:
   ```bash
   curl -X POST "http://localhost:8000/api/chat/query" \
     -H "Content-Type: application/json" \
     -d '{"query": "What is DPI?", "fund_id": 1}'
   ```

---

## Questions?

- Groq Documentation: https://console.groq.com/docs
- Groq Playground: https://console.groq.com/playground
- Check logs: `docker compose logs backend -f`

**Happy coding! 🚀**
