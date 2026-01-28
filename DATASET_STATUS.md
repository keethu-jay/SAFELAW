# Dataset Status

## Current Data Summary

### Downloaded Documents
- **UK Supreme Court (UKSC)**: 1,593 documents ✅
  - Location: `data/raw_xml/`
  - Format: XML court case files
  - Status: Ready for classification
  
- **Employment Appeal Tribunal (EAT)**: 0 documents ⚠️
  - Status: Not yet downloaded
  - Source: TNA API (needs investigation - no EAT data fetched)

## Next Steps

### 1. Data Classification (Pending)
Once EAT data is available or if proceeding with UKSC data only:

```bash
cd backend/Data\ Preparation/
python dataset_processing.py
```

This will:
- Classify documents as majority/concurring/dissenting using GPT-4o-mini
- Organize files into: `Final Dataset/{Court}/{Verdict}/{files}`
- Target: 50 files per category per court
- **Estimated Cost**: ~$0.10 for 1,593 UKSC files with gpt-4o-mini

### 2. EAT Documents (Optional)
To download Tribunal Court documents:
- Review `tna_api_ingestion.py` in `backend/Data Preparation/`
- Investigate why EAT API endpoint not returning data
- May need to use different API endpoint or manual download

## File Structure After Classification

```
Final Dataset/
├── Supreme Court (uksc)/
│   ├── majority/
│   │   └── [up to 50 documents]
│   ├── concurring/
│   │   └── [up to 50 documents]
│   └── dissenting/
│       └── [up to 50 documents]
└── Tribunal Court (eat)/
    ├── majority/
    ├── concurring/
    └── dissenting/
```

## Configuration

- **GPTSM Model**: Configured for text summarization and highlighting
- **OpenAI API**: gpt-4o-mini verified working
- **Environment**: `.env.local` contains correct Supabase and OpenAI credentials
- **API Cost Calculator**: ~$0.075/1M input tokens, ~$0.30/1M output tokens

## Notes

- All 1,593 UKSC documents are ready in `data/raw_xml/` 
- Data can be processed immediately once ready
- EAT data acquisition status TBD - may require separate API handling
- Project authentication issues resolved - login and API endpoints functional
