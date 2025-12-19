# ISSUE-013: Route53 Certificate Validation Import Failure

## Date
2025-12-19

## Symptom
GitHub Actions deployment failed during "Deploy Infrastructure" step with exit code 1:
```
Error: Process completed with exit code 1.
```
The failure occurred when importing existing Route53 validation records for ACM certificate DNS validation.

## Root Cause
Trailing dot mismatch between Route53 API responses and Terraform state keys:

1. **Route53 API** returns record names WITH trailing dot: `_a2c8c647a65c218e47e2bc76275fb092.csvgeneration.com.`
2. **Terraform `dvo.resource_record_name`** may return names WITHOUT trailing dot (varies by provider version)
3. **Import logic** attempted to match keys that didn't align

The dynamic shell-based import logic in `deploy.yml` was fragile:
```bash
# This approach was problematic
terraform import "aws_route53_record.cert_validation[\"${RECORD_NAME}\"]" \
  "${HOSTED_ZONE_ID}_${RECORD_NAME_CLEAN}_CNAME"
```

The key mismatch caused import failures across different deployment scenarios:
- First deployment (no records exist)
- Re-deployment after `destroy.yml` (records exist but not in state)
- Fresh deployment after partial teardown

## Files Modified

### 1. `aws/terraform/route53.tf`
Added `allow_overwrite = true` to handle existing records idempotently:

**Before:**
```terraform
resource "aws_route53_record" "cert_validation" {
  for_each = { for k, v in local.cert_validation_options : k => v[0] }

  zone_id = module.route53.zone_id
  name    = each.value.name
  type    = each.value.type
  records = [each.value.record]
  ttl     = 60
}
```

**After:**
```terraform
resource "aws_route53_record" "cert_validation" {
  for_each = { for k, v in local.cert_validation_options : k => v[0] }

  allow_overwrite = true  # Handles existing records without complex import logic
  zone_id         = module.route53.zone_id
  name            = each.value.name
  type            = each.value.type
  records         = [each.value.record]
  ttl             = 60
}
```

### 2. `.github/workflows/deploy.yml`
Removed entire Route53 cert validation import block (lines 119-158):
- Removed "Cleaning up old Route53 state entries" section
- Removed "Querying Route53 for ACM validation records" section
- Removed the for loop that attempted dynamic imports

**Replaced with:**
```yaml
# Route53 cert validation records are handled by allow_overwrite=true in route53.tf
# No import needed - Terraform will create or update existing records idempotently
```

## Solution
Use Terraform's `allow_overwrite = true` pattern instead of dynamic shell-based imports:

| Scenario | Old Behavior | New Behavior |
|----------|--------------|--------------|
| First deployment | Import fails, then creates | Creates directly |
| Re-deployment (stable) | Import may succeed or fail | No-op (idempotent) |
| After destroy.yml | Import fails on key mismatch | Overwrites cleanly |
| Partial teardown | Import fails | Overwrites cleanly |

## Prevention
1. **Never use dynamic shell imports for DNS records** - Use `allow_overwrite = true` instead
2. **DNS validation records are idempotent** - ACM uses the same validation token for the same domain
3. **Terraform import blocks are static** - They cannot handle dynamic values like validation record names

## Related
- ACM Certificate: `aws_acm_certificate.cloudfront` (us-east-1)
- Hosted Zone: `Z0170225231EL8Z16R4WJ` (csvgeneration.com)
- Terraform docs: [allow_overwrite for Route53](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/route53_record#allow_overwrite)
