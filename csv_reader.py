#!/usr/bin/env python3
"""
Read and parse CSV files containing email addresses and additional data.
"""

import csv
from typing import List, Dict, Optional
from pathlib import Path


class CSVReader:
    """Read and parse CSV files with email addresses."""
    
    def __init__(self, csv_file: str):
        self.csv_file = Path(csv_file)
        self.rows: List[Dict[str, str]] = []
    
    def read(self) -> List[Dict[str, str]]:
        """Read CSV file and return list of dictionaries."""
        if not self.csv_file.exists():
            raise FileNotFoundError(f"CSV file not found: {self.csv_file}")
        
        rows = []
        with open(self.csv_file, 'r', encoding='utf-8', errors='ignore') as f:
            # Try to detect delimiter
            sample = f.read(1024)
            f.seek(0)
            sniffer = csv.Sniffer()
            delimiter = sniffer.sniff(sample).delimiter
            
            reader = csv.DictReader(f, delimiter=delimiter)
            
            for row in reader:
                # Clean up values
                cleaned_row = {k.strip(): v.strip() if v else '' for k, v in row.items()}
                rows.append(cleaned_row)
        
        self.rows = rows
        return rows
    
    def get_email_column(self) -> Optional[str]:
        """Auto-detect email column name."""
        if not self.rows:
            return None
        
        # Common email column names
        email_keywords = ['email', 'e-mail', 'mail', 'contact', 'address']
        
        for col in self.rows[0].keys():
            col_lower = col.lower()
            if any(keyword in col_lower for keyword in email_keywords):
                return col
        
        # If no match, check if any column contains email addresses
        for col in self.rows[0].keys():
            for row in self.rows[:5]:  # Check first 5 rows
                if '@' in str(row.get(col, '')):
                    return col
        
        return None
    
    def get_emails(self, email_column: Optional[str] = None) -> List[str]:
        """Extract email addresses from CSV."""
        if not self.rows:
            return []
        
        if email_column is None:
            email_column = self.get_email_column()
        
        if not email_column:
            raise ValueError("Could not determine email column. Please specify email_column parameter.")
        
        emails = []
        for row in self.rows:
            email = row.get(email_column, '').strip()
            if email and '@' in email:
                emails.append(email)
        
        return emails
    
    def get_row_by_email(self, email: str) -> Optional[Dict[str, str]]:
        """Get a row by email address."""
        email_lower = email.lower().strip()
        email_column = self.get_email_column()
        
        if not email_column:
            return None
        
        for row in self.rows:
            if row.get(email_column, '').lower().strip() == email_lower:
                return row
        
        return None


if __name__ == '__main__':
    # Test with a sample CSV
    import sys
    if len(sys.argv) > 1:
        reader = CSVReader(sys.argv[1])
        rows = reader.read()
        print(f"Read {len(rows)} rows")
        print(f"Columns: {list(rows[0].keys()) if rows else 'No rows'}")
        email_col = reader.get_email_column()
        print(f"Email column: {email_col}")
        if email_col:
            emails = reader.get_emails()
            print(f"Found {len(emails)} email addresses")
            print(f"Sample emails: {emails[:5]}")
