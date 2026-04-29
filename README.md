# Multi-Provider URL Scraper

A Python tool that scrapes search results from Google using multiple API providers with automatic fallback and load balancing.

## Supported Providers

- **Oxylabs** - Real-time proxy API
- **ScrapingBee** - JavaScript rendering and parsing
- **ScraperAPI** - Residential proxy service
- **ZenRows** - Proxy and scraping service
- **Apify** - Actor-based scraping
- **Scrapestack** - Web scraping API

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/godlylucid/Url-Parser-.git
   cd Url-Parser-
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Create configuration file**
   ```bash
   cp .env.example .env
   ```

## Configuration

### Setting up API Keys

Edit the `.env` file and add your API keys:

```env
# Oxylabs (username:password pairs)
OXYLABS_KEYS=your_username:your_password,user2:pass2

# Single key providers (comma-separated)
SCRAPINGBEE_KEYS=your_key_1,your_key_2
SCRAPERAPI_KEYS=your_key_1,your_key_2
ZENROWS_KEYS=your_key_1,your_key_2
APIFY_KEYS=your_key_1,your_key_2
SCRAPESTACK_KEYS=your_key_1,your_key_2

# Optional settings
GEO_LOCATION=California,United States
MAX_REQUESTS=5000
```

**Important:** Never commit the `.env` file to Git. It's automatically ignored by `.gitignore`.

### Key Format Examples

```env
# Oxylabs (username:password)
OXYLABS_KEYS=user1:pass123,user2:pass456

# Other providers (comma-separated keys)
SCRAPINGBEE_KEYS=abc123def456,xyz789uvw012
```

## Usage

1. **Create `queries.txt`** with your search queries:
   ```
   python programming
   web scraping
   github copilot
   ```

2. **Run the scraper**
   ```bash
   python scraper.py
   ```

3. **Check results** in `results.txt`

## Features

- ✅ **Multi-Provider Support** - Automatic fallback if one provider fails
- ✅ **Load Balancing** - Distributes requests across multiple API keys
- ✅ **Rate Limiting** - Configurable delays between requests
- ✅ **Usage Tracking** - Detailed summary of API usage per provider
- ✅ **Secure Configuration** - Environment-based API key management
- ✅ **Error Handling** - Robust error recovery and logging
- ✅ **Geo-Targeting** - Configurable geographic location for searches

## Security

### Best Practices

1. **Never hardcode credentials** - Always use environment variables
2. **Never commit `.env` file** - It's in `.gitignore` for a reason
3. **Keep API keys secret** - Only share `.env.example` template
4. **Rotate keys regularly** - If exposed, revoke immediately
5. **Use `.env.local` for local development** - Keep it out of version control

### If API Keys Were Exposed

If you see hardcoded credentials in the code:

1. **Immediately revoke** all exposed API keys on their respective platforms
2. **Clean git history** if keys were committed:
   ```bash
   # Using git-filter-branch (caution: rewrites history)
   git filter-branch --force --index-filter \
     'git rm --cached --ignore-unmatch scraper.py' \
     --prune-empty --tag-name-filter cat -- --all
   git push origin --force --all
   ```

## Configuration Files

| File | Purpose | Version Control |
|------|---------|------------------|
| `.env` | Actual API keys | ❌ Never commit (in `.gitignore`) |
| `.env.example` | Configuration template | ✅ Commit this |
| `scraper.py` | Main script | ✅ Commit this |
| `requirements.txt` | Python dependencies | ✅ Commit this |

## Logging

The script logs all activity to console with timestamps:

```
2026-04-29 12:34:56,789 - INFO - Loaded 5 queries from 'queries.txt'
2026-04-29 12:34:57,890 - INFO - Trying: Oxylabs
2026-04-29 12:35:00,123 - INFO - Waiting 2.3s...
```

## Troubleshooting

### No API keys found

```
[ERROR] No valid API keys found in any provider!
Please configure your .env file with at least one API key.
See .env.example for the correct format.
```

**Solution:** Make sure `.env` file exists and has at least one valid API key.

### Query file not found

```
[ERROR] 'queries.txt' not found!
Create a queries.txt file with one dork/query per line.
```

**Solution:** Create `queries.txt` with your search queries (one per line).

### All providers failed

Check:
- API keys are valid and active
- Internet connection is working
- Rate limits haven't been exceeded
- Provider accounts have sufficient credits

## License

MIT License - See LICENSE file for details

## Disclaimer

This tool is for educational and research purposes only. Ensure you comply with:
- Terms of service of all API providers
- robots.txt and legal requirements of websites being scraped
- Data privacy regulations (GDPR, CCPA, etc.)

The author assumes no responsibility for misuse.
