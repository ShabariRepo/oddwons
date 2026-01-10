#!/bin/bash

echo "🔗 Starting Stripe webhook forwarder..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "⚠️  Keep this terminal open while testing!"
echo ""
echo "Events being forwarded:"
echo "  • checkout.session.completed"
echo "  • customer.subscription.created"
echo "  • customer.subscription.updated"
echo "  • customer.subscription.deleted"
echo "  • invoice.paid"
echo "  • invoice.payment_failed"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

stripe listen \
  --forward-to localhost:8000/api/v1/billing/webhook \
  --events checkout.session.completed,customer.subscription.created,customer.subscription.deleted,customer.subscription.updated,invoice.paid,invoice.payment_failed
