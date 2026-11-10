# Optional Oracle Cloud Always Free host — availability caveats

This is a possible no-monthly-compute-cost host for Paperclip, not a guaranteed always-on service.

## Published Always Free capacity

Oracle's current Always Free documentation lists OCI Ampere A1 Compute in the home region. The monthly allowance is 1,500 OCPU-hours and 9,000 GB-hours, equivalent to up to 2 OCPUs and 12 GB RAM when run continuously for a typical month. The account also has a limited block-volume allowance. Check the Oracle Console and ensure every selected resource is explicitly labelled **Always Free eligible** before provisioning.

Source: https://docs.oracle.com/fr-fr/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm

## Important risks

- Always Free capacity is not guaranteed in every home-region availability domain. Oracle may report "out of host capacity"; do not upgrade to a paid account just to work around it.
- Oracle may reclaim an Always Free compute instance if, for seven days, its 95th-percentile CPU use is below 20%, network use is below 20%, and (for A1) memory use is below 20%. A quiet Paperclip controller can fall into this category. Do not add artificial load just to defeat reclamation.
- Accounts left unused for 30 days or more may become eligible for suspension or termination.
- Free Tier enrollment requires identity verification with a supported credit/debit card. Oracle says it may place a temporary authorization hold that is removed by the bank; it says the card is not charged unless the account is upgraded. Do not proceed unless you are comfortable providing this verification method.
- Oracle documents one Free Trial or Always Free account per person. Do not create duplicate accounts.
- Keep within the published Always Free quota. Do not upgrade to Pay As You Go; configure compartment quotas where available and avoid every non-Always-Free resource.

Sources:
- https://www.oracle.com/fr/cloud/free/faq/
- https://docs.oracle.com/fr-fr/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm

## Recommendation for Boonta

Treat Oracle A1 as an optional experiment, not a production uptime guarantee. If capacity is unavailable or the instance is reclaimed, Paperclip routines stop. The existing GitHub Actions schedule remains the reliable cloud scheduler until a separately reviewed cutover.

For dependable Paperclip uptime, use an already-owned always-on machine or a paid VPS (the official Paperclip guide currently quotes roughly US$5–10/month for a small VPS). A Mac running only when convenient is sufficient for manual Paperclip use, but not for continuous scheduled agent work.

## Safe provisioning checklist

1. Select the home region deliberately; Always Free compute is provisioned there.
2. Create only an A1 instance within the displayed Always Free limits (no additional paid resources).
3. Do not upgrade the account. If the console cannot provision free capacity, stop.
4. Configure Oracle compartment quotas and alerts to prevent unintended over-quota resources.
5. Keep PostgreSQL and Paperclip data on persistent block storage within the Always Free allowance.
6. Restrict access with a private Tailscale Serve endpoint or equivalent; do not expose Paperclip or PostgreSQL publicly without a reviewed security setup.
7. Back up both Paperclip volumes off-host. A single Oracle instance is not a backup.
8. Keep the Paperclip routine disabled until one manual Free-tier agent run, exact-head PR checks and recovery/resume test succeed.
