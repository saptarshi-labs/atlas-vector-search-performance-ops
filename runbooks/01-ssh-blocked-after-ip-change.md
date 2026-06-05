# Incident 01: SSH to the VM stopped working after the ISP changed my IP

## Issue

SSH to the freshly provisioned Azure VM timed out instead of connecting:

```
ssh: connect to host vm-vsearch-project.centralindia.cloudapp.azure.com port 22: Connection timed out
```

A timeout (not "connection refused") points to a firewall dropping packets rather than the VM rejecting them.

## Root Cause

The home ISP rotated the laptop's public IP between `terraform apply` (which baked the then-current IP into the NSG SSH rule as a `/32`) and the first SSH attempt. The NSG was still allowing SSH only from the previous IP, so packets from the new IP were silently dropped at the network layer.

## Troubleshooting Steps

1. Checked the laptop's current public IPv4:

   ```
   curl.exe -4 ifconfig.me
   ```

   Returned a different IP than expected.

2. Compared it to the IP recorded in the project's `terraform.tfvars`:

   ```
   Select-String -Path infra\terraform.tfvars -Pattern "my_ip"
   ```

   The IP there was the old one. Clear mismatch.

3. Confirmed the VM itself was running, so the VM was not the problem:

   ```
   az vm list --output table
   ```

## Resolution

Updated `my_ip` in `infra/terraform.tfvars` to the new IP plus `/32` and ran `terraform apply`. One resource changed in place (the NSG security rule), took roughly ten seconds. SSH worked immediately afterwards.

## Prevention

A `/32` source is tight and breaks every time the ISP rotates the IP. Options: widen the allowed range for the project (for example a `/16`), or use a dynamic-DNS based allowlist so the rule follows the IP. For now the fix is just to re-run `curl.exe -4 ifconfig.me` and `terraform apply` whenever SSH starts timing out.

Note: real public IP addresses and the ISP name are intentionally left out of this document, since the repository is public.
