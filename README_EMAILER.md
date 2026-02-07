# Gmail Draft Creator for Spotify Playlist Contacts

This tool reads a CSV file of email addresses and creates Gmail drafts using contact information from the Spotify Playlist Contacts PDF. Each draft includes all available playlist information (name, curator, genres, Spotify link, follower count, etc.).

## Features

- Parses Spotify Playlist Contacts PDF to extract contact information
- Reads CSV files with flexible column detection
- Matches CSV emails to PDF contact data
- Creates Gmail drafts with personalized content
- Includes all available playlist information in each email
- Supports custom email templates and messages

## Setup

### 1. Install Dependencies

```bash
pip3 install -r requirements.txt
```

### 2. Extract PDF Text

The PDF needs to be converted to text first:

```bash
pdftotext Spotify_Playlist_Contacts_3000.pdf playlist_contacts.txt
```

If `pdftotext` is not installed:

```bash
sudo apt install poppler-utils  # Ubuntu/Debian
```

### 3. Set Up Gmail API Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Gmail API:
   - Go to "APIs & Services" > "Library"
   - Search for "Gmail API"
   - Click "Enable"
4. Create OAuth 2.0 credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Choose "Desktop app" as application type
   - Download the credentials file
   - Save it as `credentials.json` in this directory

## Usage

### Basic Usage

```bash
python3 create_email_drafts.py your_emails.csv
```

### With Options

```bash
python3 create_email_drafts.py your_emails.csv \
    --artist-name "Your Artist Name" \
    --custom-message "Your custom message here" \
    --custom-subject "Custom Subject Line" \
    --limit 10 \
    --dry-run
```

### Options

- `csv_file` - Path to CSV file with email addresses (required)
- `--pdf-text` - Path to extracted PDF text file (default: `playlist_contacts.txt`)
- `--email-column` - CSV column name containing emails (auto-detected if not specified)
- `--artist-name` - Artist name to include in emails
- `--custom-message` - Custom message to include in email body
- `--custom-subject` - Custom email subject (uses playlist name if not specified)
- `--credentials` - Gmail API credentials file (default: `credentials.json`)
- `--token` - Gmail API token file (default: `token.json`)
- `--dry-run` - Parse and preview without creating drafts
- `--limit` - Limit number of drafts to create (for testing)

### CSV File Format

The CSV file should contain email addresses. The tool will auto-detect the email column by looking for columns named:
- `email`
- `e-mail`
- `mail`
- `contact`
- `address`

Or any column that contains email addresses.

Example CSV:

```csv
email,name,notes
contact1@example.com,John Doe,Playlist curator
contact2@example.com,Jane Smith,Music blogger
```

### Dry Run (Preview)

Before creating actual drafts, you can preview what will be created:

```bash
python3 create_email_drafts.py your_emails.csv --dry-run --limit 5
```

## Email Template

The generated emails include:

- Personalized greeting (using curator name if available)
- Playlist name
- Genres
- Follower count
- Spotify playlist link
- Artist name (if provided)
- Custom message (if provided)
- Additional links (Instagram, etc.)

## Workflow

1. **Extract PDF**: Convert PDF to text format
2. **Prepare CSV**: Create CSV file with email addresses
3. **Run Script**: Execute the script to create drafts
4. **Review Drafts**: Check drafts in Gmail
5. **Send**: Review and send drafts individually

## Troubleshooting

### "PDF text file not found"
Make sure you've extracted the PDF first:
```bash
pdftotext Spotify_Playlist_Contacts_3000.pdf playlist_contacts.txt
```

### "Credentials file not found"
Download `credentials.json` from Google Cloud Console (see Setup step 3).

### "No emails matched to playlist contacts"
The emails in your CSV must match the email addresses in the PDF. Check that:
- Email addresses are spelled correctly
- The PDF contains the contacts you're looking for
- The email column is being detected correctly (use `--email-column` to specify)

### Authentication Issues
On first run, a browser window will open for Google OAuth authentication. Make sure:
- You have internet connection
- You're logged into the correct Google account
- Gmail API is enabled in your Google Cloud project

## Files

- `create_email_drafts.py` - Main script
- `pdf_parser.py` - PDF text parser
- `csv_reader.py` - CSV file reader
- `gmail_drafts.py` - Gmail API integration
- `email_template.py` - Email template generator
- `requirements.txt` - Python dependencies

## Example

```bash
# 1. Extract PDF
pdftotext Spotify_Playlist_Contacts_3000.pdf playlist_contacts.txt

# 2. Create CSV with emails
cat > my_contacts.csv << EOF
email
felix@pro-gamer-gear.de
trackdiggers@gmail.com
EOF

# 3. Run with dry-run to preview
python3 create_email_drafts.py my_contacts.csv --dry-run

# 4. Create actual drafts
python3 create_email_drafts.py my_contacts.csv \
    --artist-name "My Band" \
    --custom-message "I'd love to submit my latest track for your consideration."
```

## Notes

- Drafts are created in your Gmail account's drafts folder
- You can review and edit drafts before sending
- The tool matches emails exactly (case-insensitive)
- If an email in CSV doesn't match PDF, it will be skipped with a warning
