#!/usr/bin/env python3
"""
Non-invasive email validation without sending actual emails.
Validates: syntax, domain existence, MX records, disposable emails, role accounts.
"""

import re
import dns.resolver
import socket
from typing import Dict, List, Optional, Tuple
import csv


class EmailValidator:
    """
    Validate email addresses without sending emails.
    
    Methods:
    1. Syntax validation (regex)
    2. Domain existence (DNS lookup)
    3. MX record check (mail server exists)
    4. Disposable email detection
    5. Role account detection (info@, support@, etc.)
    """
    
    # Common disposable email domains
    DISPOSABLE_DOMAINS = {
        '10minutemail.com', 'guerrillamail.com', 'mailinator.com',
        'tempmail.com', 'throwaway.email', 'temp-mail.org',
        'getnada.com', 'mohmal.com', 'fakeinbox.com',
        'trashmail.com', 'yopmail.com', 'maildrop.cc'
    }
    
    # Common role account prefixes
    ROLE_ACCOUNTS = {
        'info', 'support', 'help', 'contact', 'hello', 'noreply',
        'no-reply', 'donotreply', 'admin', 'administrator',
        'postmaster', 'webmaster', 'abuse', 'sales', 'marketing'
    }
    
    def __init__(self):
        self.validation_cache = {}
    
    def validate_syntax(self, email: str) -> Tuple[bool, Optional[str]]:
        """
        Validate email syntax using RFC 5322 compliant regex.
        
        Returns:
            (is_valid, error_message)
        """
        if not email or not isinstance(email, str):
            return False, "Email is empty or not a string"
        
        email = email.strip().lower()
        
        # Basic regex (not perfect but catches most issues)
        pattern = r'^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$'
        
        if not re.match(pattern, email):
            return False, "Invalid email format"
        
        # Check for common issues
        if email.startswith('.') or email.startswith('@'):
            return False, "Email cannot start with . or @"
        
        if '..' in email:
            return False, "Email cannot contain consecutive dots"
        
        if email.count('@') != 1:
            return False, "Email must contain exactly one @"
        
        local, domain = email.split('@')
        
        if len(local) > 64:
            return False, "Local part too long (max 64 characters)"
        
        if len(domain) > 255:
            return False, "Domain too long (max 255 characters)"
        
        return True, None
    
    def check_domain_exists(self, domain: str) -> Tuple[bool, Optional[str]]:
        """
        Check if domain exists via DNS lookup.
        
        Returns:
            (exists, error_message)
        """
        try:
            socket.gethostbyname(domain)
            return True, None
        except socket.gaierror:
            return False, f"Domain {domain} does not exist"
        except Exception as e:
            return False, f"DNS lookup error: {str(e)}"
    
    def check_mx_record(self, domain: str) -> Tuple[bool, Optional[str], Optional[List[str]]]:
        """
        Check if domain has MX (mail exchange) records.
        
        Returns:
            (has_mx, error_message, mx_records)
        """
        try:
            mx_records = dns.resolver.resolve(domain, 'MX')
            mx_list = [str(mx.exchange).rstrip('.') for mx in mx_records]
            return True, None, mx_list
        except dns.resolver.NoAnswer:
            # No MX record, check for A record (some servers use A record)
            try:
                dns.resolver.resolve(domain, 'A')
                return True, "No MX record, but A record exists", None
            except:
                return False, f"No MX or A records for {domain}", None
        except dns.resolver.NXDOMAIN:
            return False, f"Domain {domain} does not exist", None
        except Exception as e:
            return False, f"DNS error: {str(e)}", None
    
    def is_disposable(self, email: str) -> Tuple[bool, Optional[str]]:
        """
        Check if email is from a disposable email service.
        
        Returns:
            (is_disposable, domain)
        """
        domain = email.split('@')[1].lower()
        if domain in self.DISPOSABLE_DOMAINS:
            return True, domain
        return False, None
    
    def is_role_account(self, email: str) -> Tuple[bool, Optional[str]]:
        """
        Check if email is a role account (info@, support@, etc.).
        
        Returns:
            (is_role_account, role_name)
        """
        local = email.split('@')[0].lower()
        for role in self.ROLE_ACCOUNTS:
            if local == role or local.startswith(role + '+') or local.startswith(role + '.'):
                return True, role
        return False, None
    
    def validate_email(self, email: str, check_mx: bool = True, 
                      check_disposable: bool = True, 
                      check_role: bool = False) -> Dict:
        """
        Comprehensive email validation.
        
        Args:
            email: Email address to validate
            check_mx: Check MX records (requires dnspython)
            check_disposable: Check for disposable email domains
            check_role: Check for role accounts
        
        Returns:
            Dictionary with validation results
        """
        result = {
            'email': email,
            'valid': False,
            'syntax_valid': False,
            'domain_exists': False,
            'has_mx': False,
            'is_disposable': False,
            'is_role_account': False,
            'warnings': [],
            'errors': []
        }
        
        # Check cache
        cache_key = f"{email}_{check_mx}_{check_disposable}_{check_role}"
        if cache_key in self.validation_cache:
            return self.validation_cache[cache_key]
        
        # Syntax validation
        syntax_ok, syntax_error = self.validate_syntax(email)
        result['syntax_valid'] = syntax_ok
        if not syntax_ok:
            result['errors'].append(syntax_error)
            result['valid'] = False
            self.validation_cache[cache_key] = result
            return result
        
        # Extract domain
        domain = email.split('@')[1].lower()
        
        # Domain existence
        domain_exists, domain_error = self.check_domain_exists(domain)
        result['domain_exists'] = domain_exists
        if not domain_exists:
            result['errors'].append(domain_error)
        
        # MX record check
        if check_mx and domain_exists:
            has_mx, mx_error, mx_records = self.check_mx_record(domain)
            result['has_mx'] = has_mx
            if mx_records:
                result['mx_records'] = mx_records
            if not has_mx and mx_error:
                result['warnings'].append(mx_error)
        
        # Disposable email check
        if check_disposable:
            is_disp, disp_domain = self.is_disposable(email)
            result['is_disposable'] = is_disp
            if is_disp:
                result['warnings'].append(f"Disposable email domain: {disp_domain}")
        
        # Role account check
        if check_role:
            is_role, role_name = self.is_role_account(email)
            result['is_role_account'] = is_role
            if is_role:
                result['warnings'].append(f"Role account detected: {role_name}@")
        
        # Overall validity
        result['valid'] = (
            result['syntax_valid'] and 
            result['domain_exists'] and
            (not check_mx or result['has_mx']) and
            (not check_disposable or not result['is_disposable'])
        )
        
        self.validation_cache[cache_key] = result
        return result
    
    def validate_csv(self, csv_file: str, email_column: Optional[str] = None,
                    output_file: Optional[str] = None) -> List[Dict]:
        """
        Validate emails from a CSV file.
        
        Returns:
            List of validation results
        """
        from csv_reader import CSVReader
        
        reader = CSVReader(csv_file)
        rows = reader.read()
        
        if not email_column:
            email_column = reader.get_email_column()
        
        if not email_column:
            raise ValueError("Could not determine email column")
        
        results = []
        for row in rows:
            email = row.get(email_column, '').strip()
            if email:
                validation = self.validate_email(email)
                validation['csv_row'] = row
                results.append(validation)
        
        # Write results if output file specified
        if output_file:
            with open(output_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    'email', 'valid', 'syntax_valid', 'domain_exists', 
                    'has_mx', 'is_disposable', 'is_role_account', 
                    'warnings', 'errors'
                ])
                writer.writeheader()
                for r in results:
                    row_data = {k: v for k, v in r.items() if k != 'csv_row'}
                    row_data['warnings'] = '; '.join(r['warnings'])
                    row_data['errors'] = '; '.join(r['errors'])
                    writer.writerow(row_data)
        
        return results


if __name__ == '__main__':
    import sys
    
    validator = EmailValidator()
    
    if len(sys.argv) > 1:
        # Validate single email
        email = sys.argv[1]
        result = validator.validate_email(email)
        
        print(f"Email: {email}")
        print(f"Valid: {result['valid']}")
        print(f"Syntax: {result['syntax_valid']}")
        print(f"Domain exists: {result['domain_exists']}")
        print(f"Has MX: {result['has_mx']}")
        print(f"Disposable: {result['is_disposable']}")
        if result['warnings']:
            print(f"Warnings: {', '.join(result['warnings'])}")
        if result['errors']:
            print(f"Errors: {', '.join(result['errors'])}")
    else:
        print("Usage: python3 email_validator.py <email>")
        print("Or: python3 email_validator.py <csv_file> --email-column <column>")
