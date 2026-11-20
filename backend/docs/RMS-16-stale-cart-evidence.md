# RMS-16 / issue #22

Checkout revalidates every locked item, rejecting the whole order on unavailable/missing dishes with 409 UNAVAILABLE_ITEMS and item IDs/names. No Order/OrderItem/retry rows are created. Direct API has the same mandatory service check. UI reloads and flags stale lines, preserves valid quantities, offers Remove unavailable dishes, and requires fresh confirmation/new retry identity. No automatic partial order.

PostgreSQL test adds two dishes to cart, makes one unavailable, checks repeated direct API rejection and zero rows, verifies the other quantity remains, removes stale item and confirms the valid order. Actual execution recorded in PR; browser/release acceptance remains separate.
