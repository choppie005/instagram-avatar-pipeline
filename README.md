# Instagram AI Avatar Pipeline

Fully automated pipeline that generates finance/business Instagram Reels using AI avatar personas. Generates scripts (Gemini), creates avatar videos with voice (HeyGen), and posts to Instagram — all on autopilot.

## Architecture

```
Gemini (script) → HeyGen (avatar video + TTS) → Instagram (post Reel)
```

**4 AI personas**, each with a unique avatar, voice, and topic focus:

| Persona | Niche | Schedule |
|---------|-------|----------|
| Arjun Kapoor | Investing & wealth building | Mon, Wed, Fri |
| Priya Sharma | Freelancing & online business | Tue, Thu, Sat |
| Neha Verma | Budgeting & saving | Mon, Thu |
| Rohan Mehta | Crypto & DeFi | Wed, Sat |

## Setup

### Prerequisites

- Python 3.11+
- API keys: Gemini, HeyGen, Instagram (Meta Graph API)

### Install

```bash
git clone https://github.com/choppie005/instagram-avatar-pipeline.git
cd instagram-avatar-pipeline
pip install -r requirements.txt
```

### Configure

```bash
cp config/.env.example config/.env
```

Edit `config/.env` and add your API keys:

```
GEMINI_API_KEY=your_key
HEYGEN_API_KEY=your_key
INSTAGRAM_ACCESS_TOKEN=your_token
INSTAGRAM_USER_ID=your_id
DISCORD_WEBHOOK_URL=your_webhook  # optional
CRON_SECRET=your_secret           # optional, secures the /api/run endpoint
```

### Run locally

```bash
python src/pipeline.py
```

### Run with cron (local)

```bash
# Run daily at 9:00 AM
0 9 * * * cd /path/to/instagram-avatar-pipeline && python src/pipeline.py
```

## Deploy to Vercel

### Install Vercel CLI

```bash
npm i -g vercel
```

### Build & Deploy

```bash
vercel --prod
```

### Environment Variables

Set these in Vercel Dashboard → Project Settings → Environment Variables:

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | Yes | Google AI Studio API key |
| `HEYGEN_API_KEY` | Yes | HeyGen API key |
| `INSTAGRAM_ACCESS_TOKEN` | Yes | Meta Graph API long-lived token |
| `INSTAGRAM_USER_ID` | Yes | Instagram Business account ID |
| `DISCORD_WEBHOOK_URL` | No | Discord webhook for failure alerts |
| `CRON_SECRET` | No | Secret to secure the cron endpoint |

### Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/run` | GET | Trigger the pipeline (called by Vercel Cron daily at 3:00 AM UTC) |

### Vercel Cron

The pipeline runs automatically via Vercel Cron (configured in `vercel.json`). Schedule: `0 3 * * *` (daily at 3:00 AM UTC / 8:30 AM IST).

To change the schedule, edit the `crons` field in `vercel.json`.

## Project Structure

```
├── api/
│   ├── run.py              # Vercel serverless function (pipeline trigger)
│   └── health.py           # Health check endpoint
├── config/
│   ├── personas.json       # Persona definitions (avatars, voices, topics)
│   └── .env.example        # API key template
├── src/
│   ├── pipeline.py         # Main orchestrator (local cron)
│   ├── script_generator.py # Gemini API — script + caption generation
│   ├── video_generator.py  # HeyGen API — avatar video with TTS
│   ├── instagram_poster.py # Meta Graph API — post Reels
│   ├── persona_selector.py # Select today's personas and topics
│   └── content_log.py      # Track posted content
├── data/
│   └── content_log.json    # Content history
├── vercel.json             # Vercel deployment config + cron
└── requirements.txt        # Python dependencies
```

## Cost

~$24/month (HeyGen Creator plan). Gemini API and Instagram posting are free.
