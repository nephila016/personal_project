# Spec Review — Issues Found & Fixes Applied

## CRITICAL Issues (would cause bugs or data loss)

### 1. Orders table missing `delivery_address` column
**Spec:** 02, 05  
**Problem:** The order flow (spec 05) allows customers to "Change Address" for a single order, but the `orders` table (spec 02) has no `delivery_address` column. The changed address would be lost — the system would always use the profile address.  
**Fix:** Add `delivery_address TEXT NOT NULL` to `orders` table, populated from customer profile at order time (or overridden if customer changes it).

### 2. No way to distinguish who canceled an order
**Spec:** 02, 03  
**Problem:** When an order is canceled, `order_status_log.changed_by_admin_id` is `NULL` for both customer-initiated and system-initiated cancels. No way to know if the customer or the system canceled.  
**Fix:** Add `canceled_by VARCHAR(20)` to `orders` table: `'customer'`, `'admin'`, or `'system'`. Also add `changed_by_customer_id` to `order_status_log`.

### 3. Bottle returns don't add back to admin stock
**Spec:** 04  
**Problem:** The admin stock formula is `received - delivered`. But returned bottles are *empty* bottles — they shouldn't add to deliverable stock. The spec doesn't make this clear, and doesn't track the empty bottle lifecycle (admin collects empties → sends back to supplier).  
**Fix:** Clarify in spec 04 that `admin_stock` = full bottles only. Add a section documenting the full vs empty bottle distinction. Returns track customer accountability, not restockable inventory.

### 4. Duplicate order prevention missing
**Spec:** 05  
**Problem:** If a customer double-taps "Confirm", two identical orders could be created. No debouncing or idempotency mechanism.  
**Fix:** Add a `pending_order_cooldown` check: reject if customer has an identical order (same bottle count) created within the last 60 seconds. Document in spec 05.

### 5. Conversation state lost on bot restart
**Spec:** 05, 07  
**Problem:** `ConversationHandler` stores state in memory by default. If the bot process restarts, all in-progress conversations (registration, orders) are lost. Users get stuck.  
**Fix:** Add `persistence=PicklePersistence` or PostgreSQL-backed persistence to bot setup. Document in spec 07 and 08.

---

## HIGH Issues (poor UX or significant gaps)

### 6. Phone validation too strict
**Spec:** 05  
**Problem:** Regex `^\+?[0-9]{7,15}$` rejects common formats like `(123) 456-7890`, `+1 234-567-8900`, `123-456-7890`. Real users will fail validation repeatedly.  
**Fix:** Strip non-digit characters (except leading +) before validation. Store normalized form. Show example format in prompt.

### 7. No delivery notes / instructions on orders
**Spec:** 02, 05  
**Problem:** Customers can't say "leave at door", "call before coming", "gate code: 1234". Common in delivery apps.  
**Fix:** Add `delivery_notes TEXT NULLABLE` to `orders` table. Add optional step in order flow after bottle count: "Any delivery instructions? (or skip)".

### 8. No order rate limiting for customers
**Spec:** 05  
**Problem:** A customer could spam 100 pending orders. No limit on concurrent pending orders.  
**Fix:** Add config `MAX_PENDING_ORDERS_PER_CUSTOMER = 3`. Check before creating order. "You already have 3 pending orders. Please wait or cancel one."

### 9. Bot `/pending` shows unbounded list
**Spec:** 05  
**Problem:** If there are 100 pending orders, the bot sends a massive message. Telegram messages have a 4096 character limit.  
**Fix:** Paginate: show 5 orders per page with [Next Page] [Prev Page] buttons. Same for `/myorders`.

### 10. Missing `/reorder` command
**Spec:** 05  
**Problem:** Repeat customers (the majority) must go through the full order flow every time. No quick reorder.  
**Fix:** Add `/reorder` — repeats last delivered order with one confirmation tap.

### 11. Missing bot menu commands setup
**Spec:** 05, 07  
**Problem:** Telegram supports `setMyCommands` to show a menu when users type `/`. Not mentioned anywhere. Without it, users don't discover commands.  
**Fix:** Add `BotCommand` registration in `bot/main.py` startup. Different command menus for customers vs admins (Telegram supports scoped commands).

### 12. Missing admin daily summary notification
**Spec:** 05  
**Problem:** Admins have no proactive morning summary. They must manually check `/pending` and `/stock`.  
**Fix:** Add optional scheduled notification (configurable time): "Good morning! You have {n} pending orders, {m} active. Stock: {s} bottles."

### 13. `/switchmode` command undocumented
**Spec:** 05  
**Problem:** Section 7 mentions `/switchmode` for dual-role users, but it's not in the command overview table.  
**Fix:** Add to command table. Also add `/switchmode` handler file.

---

## MEDIUM Issues (improvements)

### 14. `admins` table missing `updated_at`
**Spec:** 02  
**Problem:** `customers` has `updated_at` but `admins` doesn't. Inconsistent; makes it hard to track admin profile changes.  
**Fix:** Add `updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()` to `admins`.

### 15. `global_admins` missing `last_login_at`
**Spec:** 02  
**Problem:** No way to see when a global admin last logged in. Useful for security auditing.  
**Fix:** Add `last_login_at TIMESTAMPTZ NULLABLE` to `global_admins`.

### 16. `bottle_returns` missing `notes`
**Spec:** 02  
**Problem:** `bottle_receipts` has a `notes` field but `bottle_returns` doesn't. Admin might want to note context.  
**Fix:** Add `notes TEXT NULLABLE` to `bottle_returns`.

### 17. Customer phone not unique
**Spec:** 02  
**Problem:** No unique constraint on `customers.phone`. Two customers could register with the same phone, causing confusion in admin `/returns` lookup by phone.  
**Fix:** Add unique constraint. During registration, check and reject duplicates.

### 18. Missing composite index
**Spec:** 02  
**Problem:** Common query pattern `WHERE customer_id = ? AND status = 'pending'` (used by `/cancel`) has no composite index.  
**Fix:** Add `ix_orders_customer_status` on `(customer_id, status)`.

### 19. No web dashboard login rate limiting
**Spec:** 06  
**Problem:** No brute-force protection on `/login`. An attacker could try unlimited password combinations.  
**Fix:** Add Flask-Limiter: 5 attempts per minute per IP on POST `/login`. Account lockout after 10 failed attempts (configurable).

### 20. No CORS configuration documented
**Spec:** 06  
**Problem:** API endpoints don't mention CORS. Same-origin is fine for SSR+AJAX, but should be explicitly configured.  
**Fix:** Add `flask-cors` with default deny (same-origin only). Document in spec 06.

### 21. Seed script creates insecure default password
**Spec:** 08  
**Problem:** `admin` / `changeme` is insecure. No forced password change.  
**Fix:** Either force password change on first login, or generate a random password and print it to console during seed.

### 22. Missing notification failure handling
**Spec:** 03, 05  
**Problem:** If the customer blocks the bot, notifications fail silently. The admin gets no feedback.  
**Fix:** Handle `telegram.error.Forbidden` — log it, mark customer as `notification_blocked=True`. Show warning to admin: "Customer may not receive notifications."

### 23. Stale inline keyboard buttons
**Spec:** 05  
**Problem:** An admin sees [Claim] on an order from the pending list. They go away for an hour, come back, tap [Claim]. The order may already be delivered. The version check catches this, but the UX is jarring.  
**Fix:** When the claim fails, edit the original message to show updated status instead of just showing an error.

### 24. Missing error handling for all conversation handlers
**Spec:** 05  
**Problem:** Timeout is mentioned for registration (10 min) but not for other flows. No consistent timeout/fallback strategy.  
**Fix:** All ConversationHandlers should have: timeout (10 min), `/cancel` fallback, and invalid input re-prompt. Document as a pattern.

### 25. Web API missing export/download
**Spec:** 06  
**Problem:** No CSV/Excel export for orders, customers, or inventory. Common requirement for admin panels.  
**Fix:** Add `GET /api/v1/orders/export?format=csv` (and similar for customers, inventory).

---

## LOW Issues (nice to have)

### 26. No customer feedback/rating after delivery
### 27. No Telegram location sharing for address
### 28. No estimated delivery time
### 29. No webhook vs polling decision documented
### 30. No global admin Telegram integration (web-only)

---

## Summary of Changes to Apply

| Spec | Changes |
|------|---------|
| 02 | Add `delivery_address`, `delivery_notes`, `canceled_by` to orders. Add `updated_at` to admins. Add `last_login_at` to global_admins. Add `notes` to bottle_returns. Add `notification_blocked` to customers. Phone unique constraint. Composite index. |
| 03 | Add `canceled_by` tracking. Add reassignment transition (global admin via web). Notification failure handling. |
| 04 | Clarify full vs empty bottle distinction. Document empty bottle lifecycle. |
| 05 | Add `/reorder`, `/switchmode` to command table. Fix phone validation. Add delivery notes to order flow. Add pagination. Add conversation persistence. Add timeout to all handlers. Add duplicate order prevention. Add bot menu commands. Add daily summary. Rate limit orders. Handle notification failures. |
| 06 | Add rate limiting on login. Add CORS config. Add CSV export endpoints. Add API error for notification failures. |
| 07 | Add conversation persistence file. Add `/reorder` and `/switchmode` handler files. |
| 08 | Fix seed script security. Add conversation persistence to Phase 3. |
| 01 | Add rate limiting to security overview. Mention webhook default. |
