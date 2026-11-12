// frontend/e2e/payguard.spec.js
import { test, expect } from '@playwright/test';

test.describe('PayGuard AI – End-to-End Prevention Flows', () => {

  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test('Flow 1: Phishing Link -> HIGH Warning Modal with Gated Bypass', async ({ page }) => {
    // 1. Check Link tab is active
    await page.getByTestId('tab-link').click();

    // 2. Input malicious phishing URL
    const urlInput = page.getByTestId('url-input');
    await urlInput.fill('http://paytm-secure-login.xyz/verify?id=123');

    // 3. Click Analyze Threat
    await page.getByTestId('analyze-url-btn').click();

    // 4. Critical Warning Modal must appear
    const modal = page.getByTestId('warning-modal');
    await expect(modal).toBeVisible({ timeout: 10000 });
    await expect(modal).toContainText('CRITICAL FRAUD ALERT');

    // 5. Verify gated proceed button is disabled by default
    const proceedBtn = page.getByTestId('proceed-payment-btn');
    await expect(proceedBtn).toBeDisabled();

    // 6. Click Cancel Payment (Primary Safe Action)
    const cancelBtn = page.getByTestId('cancel-payment-btn');
    await cancelBtn.click();
    await expect(modal).not.toBeVisible();

    // 7. Verify Result Card shows HIGH RISK
    const resultCard = page.getByTestId('result-card');
    await expect(resultCard).toBeVisible();
    await expect(resultCard).toContainText('HIGH RISK');
    await expect(resultCard).toContainText('Do not proceed');
  });

  test('Flow 2: Malicious QR Payload -> HIGH Risk Result', async ({ page }) => {
    // 1. Switch to Scan QR tab
    await page.getByTestId('tab-qr').click();

    // 2. Pick the Deceptive Collect Fraud sample from the list
    await page.getByRole('button', { name: /Malicious: Urgent Collect Trap/i }).click();

    // 3. Verify decoded payload is displayed BEFORE analysis
    await expect(page.getByText('Decoded UPI Payload')).toBeVisible();
    await expect(page.getByText('VIP Support')).toBeVisible();

    // 4. Click Analyze QR Code
    await page.getByTestId('analyze-qr-btn').click();

    // 5. Warning modal or high risk card appears
    const modal = page.getByTestId('warning-modal');
    await expect(modal).toBeVisible({ timeout: 10000 });
    await page.getByTestId('cancel-payment-btn').click();

    const resultCard = page.getByTestId('result-card');
    await expect(resultCard).toBeVisible();
    await expect(resultCard).toContainText('HIGH RISK');
  });

  test('Flow 3: Normal Transaction -> LOW Risk Safe Verdict', async ({ page }) => {
    // 1. Switch to Check Transaction tab
    await page.getByTestId('tab-txn').click();

    // 2. Pick safe daytime grocery sample
    await page.getByRole('button', { name: /Safe: Typical Grocery/i }).click();

    // 3. Submit transaction
    await page.getByTestId('analyze-txn-btn').click();

    // 4. Result card must show LOW RISK
    const resultCard = page.getByTestId('result-card');
    await expect(resultCard).toBeVisible({ timeout: 10000 });
    await expect(resultCard).toContainText('LOW RISK');
    await expect(resultCard).toContainText('Safe to proceed');
  });

  test('Flow 4: Anomalous Transaction -> HIGH Risk Anomaly Alert', async ({ page }) => {
    // 1. Switch to Check Transaction tab
    await page.getByTestId('tab-txn').click();

    // 2. Pick extreme night refund sample
    await page.getByRole('button', { name: /High Anomaly: ₹49,999 Night Refund/i }).click();

    // 3. Submit transaction
    await page.getByTestId('analyze-txn-btn').click();

    // 4. Warning modal appears
    const modal = page.getByTestId('warning-modal');
    await expect(modal).toBeVisible({ timeout: 10000 });
    await page.getByTestId('cancel-payment-btn').click();

    // 5. Result card shows HIGH RISK with anomaly signals
    const resultCard = page.getByTestId('result-card');
    await expect(resultCard).toContainText('HIGH RISK');
    await expect(resultCard).toContainText('Do not proceed');
  });

  test('Flow 5: History Audit Log displays evaluated items', async ({ page }) => {
    // 1. Switch to History tab
    await page.getByTestId('tab-history').click();

    // 2. Table and charts are rendered
    await expect(page.getByText('Risk Level Distribution')).toBeVisible();
    await expect(page.getByText('Threat Score Trend (Timeline)')).toBeVisible();

    // 3. Table should contain records
    const table = page.locator('table');
    await expect(table).toBeVisible();
    const rows = table.locator('tbody tr');
    await expect(rows.first()).toBeVisible();
  });
});

