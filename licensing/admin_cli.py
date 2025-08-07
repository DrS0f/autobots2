#!/usr/bin/env python3
"""
Admin CLI for iOS Instagram Automation License Server
Usage: python admin_cli.py --help
"""

import click
import requests
import json
import os
from datetime import datetime, timezone
from typing import Optional


class LicenseAdminClient:
    def __init__(self, base_url: str, admin_token: str):
        self.base_url = base_url.rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json"
        }
    
    def issue_license(
        self,
        customer_id: str,
        plan: str = "basic",
        features: list = None,
        device_id: Optional[str] = None,
        duration_days: int = 30,
        grace_days: int = 7
    ):
        """Issue a new license"""
        if features is None:
            features = ["basic_automation"]
        
        data = {
            "customer_id": customer_id,
            "plan": plan,
            "features": features,
            "device_id": device_id,
            "duration_days": duration_days,
            "grace_days": grace_days
        }
        
        response = requests.post(f"{self.base_url}/auth/issue", headers=self.headers, json=data)
        response.raise_for_status()
        return response.json()
    
    def revoke_license(self, license_key: str, reason: str = "Revoked by admin"):
        """Revoke a license"""
        data = {
            "license_key": license_key,
            "reason": reason
        }
        
        response = requests.post(f"{self.base_url}/auth/revoke", headers=self.headers, json=data)
        response.raise_for_status()
        return response.json()
    
    def list_licenses(self):
        """List all licenses"""
        response = requests.get(f"{self.base_url}/admin/licenses", headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def extend_license(self, license_key: str, additional_days: int):
        """Extend a license"""
        params = {
            "license_key": license_key,
            "additional_days": additional_days
        }
        
        response = requests.post(f"{self.base_url}/admin/extend", headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()
    
    def verify_license(self, license_key: str, device_id: Optional[str] = None):
        """Verify a license (public endpoint)"""
        params = {"license_key": license_key}
        if device_id:
            params["device_id"] = device_id
        
        response = requests.get(f"{self.base_url}/auth/verify", params=params)
        response.raise_for_status()
        return response.json()


@click.group()
@click.option("--url", default="http://localhost:8002", help="License server URL")
@click.option("--token", default=None, help="Admin token (or set LICENSE_ADMIN_TOKEN env var)")
@click.pass_context
def cli(ctx, url, token):
    """iOS Instagram Automation License Admin CLI"""
    if not token:
        token = os.environ.get("LICENSE_ADMIN_TOKEN", "admin-token-change-this")
    
    ctx.ensure_object(dict)
    ctx.obj["client"] = LicenseAdminClient(url, token)


@cli.command()
@click.argument("customer_id")
@click.option("--plan", default="basic", help="License plan")
@click.option("--features", multiple=True, default=["basic_automation"], help="License features")
@click.option("--device-id", help="Bind to specific device ID")
@click.option("--duration", default=30, help="Duration in days")
@click.option("--grace", default=7, help="Grace period in days")
@click.pass_context
def issue(ctx, customer_id, plan, features, device_id, duration, grace):
    """Issue a new license"""
    try:
        result = ctx.obj["client"].issue_license(
            customer_id=customer_id,
            plan=plan,
            features=list(features),
            device_id=device_id,
            duration_days=duration,
            grace_days=grace
        )
        
        click.echo("✅ License issued successfully!")
        click.echo(f"Customer ID: {result['customer_id']}")
        click.echo(f"Plan: {result['plan']}")
        click.echo(f"Features: {', '.join(result['features'])}")
        click.echo(f"Expires: {result['expires_at']}")
        click.echo(f"Grace Days: {result['grace_days']}")
        click.echo(f"\n🔑 License Key:")
        click.echo(f"{result['license_key']}")
        
    except requests.RequestException as e:
        click.echo(f"❌ Error: {e}", err=True)


@cli.command()
@click.argument("license_key")
@click.option("--reason", default="Revoked by admin", help="Revocation reason")
@click.pass_context
def revoke(ctx, license_key, reason):
    """Revoke a license"""
    try:
        result = ctx.obj["client"].revoke_license(license_key, reason)
        click.echo("✅ License revoked successfully!")
        click.echo(f"Message: {result['message']}")
        
    except requests.RequestException as e:
        click.echo(f"❌ Error: {e}", err=True)


@cli.command()
@click.argument("license_key")
@click.argument("additional_days", type=int)
@click.pass_context
def extend(ctx, license_key, additional_days):
    """Extend a license by additional days"""
    try:
        result = ctx.obj["client"].extend_license(license_key, additional_days)
        click.echo("✅ License extended successfully!")
        click.echo(f"Message: {result['message']}")
        
    except requests.RequestException as e:
        click.echo(f"❌ Error: {e}", err=True)


@cli.command()
@click.pass_context
def list(ctx):
    """List all licenses"""
    try:
        licenses = ctx.obj["client"].list_licenses()
        
        if not licenses:
            click.echo("No licenses found.")
            return
        
        click.echo(f"Found {len(licenses)} license(s):\n")
        
        for license_obj in licenses:
            status = "🟢 ACTIVE" if license_obj.get("is_active") else "🔴 REVOKED"
            expires_at = license_obj.get("expires_at", "")
            if expires_at:
                expires_dt = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
                now = datetime.now(timezone.utc)
                if expires_dt < now:
                    status += " (EXPIRED)"
            
            click.echo(f"Customer: {license_obj.get('customer_id')}")
            click.echo(f"Plan: {license_obj.get('plan')}")
            click.echo(f"Features: {', '.join(license_obj.get('features', []))}")
            click.echo(f"Status: {status}")
            click.echo(f"Expires: {expires_at}")
            click.echo(f"Grace Days: {license_obj.get('grace_days', 0)}")
            if license_obj.get("device_id"):
                click.echo(f"Device ID: {license_obj.get('device_id')}")
            click.echo("-" * 50)
        
    except requests.RequestException as e:
        click.echo(f"❌ Error: {e}", err=True)


@cli.command()
@click.argument("license_key")
@click.option("--device-id", help="Device ID to verify against")
@click.pass_context
def verify(ctx, license_key, device_id):
    """Verify a license"""
    try:
        result = ctx.obj["client"].verify_license(license_key, device_id)
        
        if result.get("valid"):
            click.echo("✅ License is VALID!")
            click.echo(f"Customer ID: {result.get('customer_id')}")
            click.echo(f"Plan: {result.get('plan')}")
            click.echo(f"Features: {', '.join(result.get('features', []))}")
            click.echo(f"Expires: {result.get('expires_at')}")
            click.echo(f"Time to expiry: {result.get('time_to_expiry_hours')} hours")
            
            if result.get("in_grace_period"):
                click.echo("⚠️  License is in GRACE PERIOD")
        else:
            click.echo("❌ License is INVALID!")
            
        click.echo(f"Message: {result.get('message')}")
        
    except requests.RequestException as e:
        click.echo(f"❌ Error: {e}", err=True)


if __name__ == "__main__":
    cli()