# Installation Guide

This guide explains how to install the WordLift Gemini CLI Extension.

## Method 1: Install from GitHub (Recommended)

Install directly from the GitHub repository:

```bash
gemini extensions install https://github.com/wordlift/wordlift-gemini-cli-extension.git
```

This will automatically:
1. Clone the repository
2. Install it as an extension
3. Make it available in your Gemini CLI

## Method 2: Install from Local Clone

If you've cloned the repository locally:

```bash
git clone https://github.com/wordlift/wordlift-gemini-cli-extension.git
cd wordlift-gemini-cli-extension
gemini extensions link .
```

## Post-Installation Setup

### 1. Create Virtual Environment

Navigate to the extension directory and set up Python dependencies:

```bash
# Find where the extension was installed
gemini extensions list

# Navigate to the extension directory
cd ~/.gemini/extensions/wordlift-gemini-cli-extension  # or wherever it was installed

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Deactivate when done
deactivate
```

### 2. Configure Environment Variables

Create a `.env` file in the extension directory:

```bash
cd ~/.gemini/extensions/wordlift-gemini-cli-extension  # or wherever it was installed
cp .env.example .env
```

Edit `.env` and add your credentials:

```env
WORDLIFT_API_KEY=your_api_key_here
WORDLIFT_BASE_URI=https://data.wordlift.io/wl1505540
WORDLIFT_API_ENDPOINT=https://api.wordlift.io
```

**Getting your WordLift API Key:**
1. Log in to your WordLift account
2. Navigate to Settings → API
3. Copy your API key

### 3. Restart Gemini CLI

After configuration, restart your Gemini CLI session:

```bash
# Exit current session
exit

# Start new session
gemini
```

## Verify Installation

Once installed and configured, test the extension:

```
List available tools
```

You should see the WordLift tools:
- `create_entities`
- `create_or_update_entities`
- `get_entities`
- `patch_entities`
- `delete_entities`
- `upload_turtle_file`

## Troubleshooting

### Extension not found
```bash
gemini extensions list
```
Verify the extension appears in the list.

### Tools not available
1. Check that the virtual environment was created and dependencies installed
2. Verify the `.env` file exists with correct credentials
3. Restart Gemini CLI

### API authentication errors
- Verify your `WORDLIFT_API_KEY` is correct
- Check that your WordLift account is active
- Ensure you have API access enabled

## Updating the Extension

To update to the latest version:

```bash
gemini extensions update wordlift-gemini-cli-extension
```

Or if installed via link:

```bash
cd /path/to/wordlift-gemini-cli-extension
git pull origin main
source venv/bin/activate
pip install -r requirements.txt --upgrade
deactivate
```

## Uninstalling

To remove the extension:

```bash
gemini extensions uninstall wordlift-gemini-cli-extension
```
