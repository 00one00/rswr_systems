#!/usr/bin/env python3
"""
Script to configure HTTPS for the RS Systems application.

This script helps set up HTTPS by:
1. Checking if SSL certificate is available
2. Configuring environment variables
3. Updating load balancer configuration

Usage:
    python scripts/configure_https.py --domain yourdomain.com --cert-arn arn:aws:acm:...
"""

import os
import sys
import argparse
import subprocess
import json


def check_ssl_certificate(cert_arn):
    """Check if SSL certificate exists and is valid."""
    try:
        result = subprocess.run([
            'aws', 'acm', 'describe-certificate',
            '--certificate-arn', cert_arn,
            '--query', 'Certificate.Status',
            '--output', 'text'
        ], capture_output=True, text=True, check=True)
        
        status = result.stdout.strip()
        return status == 'ISSUED'
    except subprocess.CalledProcessError:
        return False


def configure_environment_variables(domain, https_available=True, force_https=True):
    """Set environment variables for HTTPS configuration."""
    env_vars = {
        'HTTPS_AVAILABLE': str(https_available).lower(),
        'FORCE_HTTPS': str(force_https).lower(),
        'PRODUCTION_DOMAIN': domain
    }
    
    print("Environment variables to set:")
    for key, value in env_vars.items():
        print(f"  {key}={value}")
    
    # Set via EB CLI
    for key, value in env_vars.items():
        try:
            subprocess.run([
                'eb', 'setenv', f'{key}={value}'
            ], check=True)
            print(f"✓ Set {key}={value}")
        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to set {key}: {e}")
            return False
    
    return True


def update_ebextensions_config(domain, cert_arn):
    """Update the .ebextensions config to enable HTTPS listener."""
    config_file = '.ebextensions/08_https_redirect.config'
    
    if not os.path.exists(config_file):
        print(f"Error: {config_file} not found")
        return False
    
    with open(config_file, 'r') as f:
        content = f.read()
    
    # Replace placeholders
    content = content.replace('YOUR_SSL_CERTIFICATE_ARN_HERE', cert_arn)
    content = content.replace('yourdomain.com', domain)
    content = content.replace('www.yourdomain.com', f'www.{domain}')
    
    # Uncomment HTTPS section
    lines = content.split('\n')
    in_https_section = False
    updated_lines = []
    
    for line in lines:
        if '# aws:elbv2:listener:443:' in line:
            in_https_section = True
            updated_lines.append(line[2:])  # Remove "# "
        elif in_https_section and line.startswith('#'):
            if line.strip() == '#':
                updated_lines.append('')
            else:
                updated_lines.append(line[2:])  # Remove "# "
        elif in_https_section and not line.startswith('#') and line.strip() == '':
            in_https_section = False
            updated_lines.append(line)
        else:
            updated_lines.append(line)
    
    with open(config_file, 'w') as f:
        f.write('\n'.join(updated_lines))
    
    print(f"✓ Updated {config_file}")
    return True


def main():
    parser = argparse.ArgumentParser(description='Configure HTTPS for RS Systems')
    parser.add_argument('--domain', required=True, help='Custom domain name')
    parser.add_argument('--cert-arn', required=True, help='SSL certificate ARN')
    parser.add_argument('--no-force', action='store_true', help='Don\'t force HTTPS redirect')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done')
    
    args = parser.parse_args()
    
    print(f"Configuring HTTPS for domain: {args.domain}")
    print(f"Using certificate: {args.cert_arn}")
    
    # Check certificate
    if not check_ssl_certificate(args.cert_arn):
        print("✗ SSL certificate not found or not issued")
        return 1
    
    print("✓ SSL certificate is valid")
    
    if args.dry_run:
        print("\nDry run - would perform the following actions:")
        print("1. Set environment variables for HTTPS")
        print("2. Update .ebextensions configuration")
        print("3. Deploy changes")
        return 0
    
    # Configure environment variables
    if not configure_environment_variables(args.domain, True, not args.no_force):
        return 1
    
    # Update configuration
    if not update_ebextensions_config(args.domain, args.cert_arn):
        return 1
    
    print("\n✓ HTTPS configuration complete!")
    print("\nNext steps:")
    print("1. Run 'eb deploy' to apply changes")
    print("2. Update DNS to point to your load balancer")
    print("3. Test HTTPS functionality")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())