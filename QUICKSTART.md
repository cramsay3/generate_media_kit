# Quick Start Guide

## 1. Install Dependencies

```bash
pip3 install -r requirements.txt
```

## 2. Extract PDF to Text

```bash
pdftotext Spotify_Playlist_Contacts_3000.pdf playlist_contacts.txt
```

## 3. Create Your CSV File

Create a CSV file with email addresses. Example:

```csv
email,name,notes
contact1@example.com,John Doe,Playlist curator
contact2@example.com,Jane Smith,Music blogger
```

Save it as `my_contacts.csv`.

## 4. Set Up Gmail API (First Time Only)

1. Go to https://console.cloud.google.com/
2. Create a project
3. Enable Gmail API
4. Create OAuth 2.0 credentials (Desktop app)
5. Download as `credentials.json`

## 5. Test with Dry Run

```bash
python3 create_email_drafts.py my_contacts.csv --dry-run --limit 5
```

## 6. Create Drafts

```bash
python3 create_email_drafts.py my_contacts.csv \
    --artist-name "Your Artist Name" \
    --custom-message "I'd love to submit my latest track for your consideration."
```

## 7. Review and Send

Go to Gmail and check your drafts folder. Review each draft and send individually.

## Troubleshooting

- **"PDF text file not found"**: Run step 2
- **"Credentials file not found"**: Complete step 4
- **"No emails matched"**: Check that emails in CSV match emails in PDF
- **Authentication**: Browser will open on first run for Google OAuth
