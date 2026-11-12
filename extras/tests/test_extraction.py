import pytest
from extras.app.analyzers.extraction import (
    extract_urls,
    extract_upi_ids,
    extract_phone_numbers,
    extract_all_entities,
    is_valid_upi_vpa,
    normalize_phone,
)
from extras.app.config import mask_upi_id, mask_phone_number, mask_pii_in_text

def test_extract_urls():
    text = "Please check http://sbi-kyc-update.top/login or visit www.secure-bank.site/portal. Also see https://paytm.com."
    urls = extract_urls(text)
    assert len(urls) == 3
    assert "http://sbi-kyc-update.top/login" in urls
    assert "http://www.secure-bank.site/portal" in urls
    assert "https://paytm.com" in urls

def test_extract_urls_punctuation_stripping():
    text = "Visit http://phishing.xyz/auth, then read http://terms.site."
    urls = extract_urls(text)
    assert "http://phishing.xyz/auth" in urls
    assert "http://terms.site" in urls

def test_upi_vs_email_distinction():
    # Legitimate UPI IDs
    assert is_valid_upi_vpa("fraud", "ybl") is True
    assert is_valid_upi_vpa("merchant", "okaxis") is True
    assert is_valid_upi_vpa("shop", "paytm") is True
    assert is_valid_upi_vpa("9876543210", "upi") is True

    # Regular Email Addresses must NOT be identified as UPI VPAs
    assert is_valid_upi_vpa("john.doe", "gmail.com") is False
    assert is_valid_upi_vpa("contact", "company.org") is False
    assert is_valid_upi_vpa("support", "hdfcbank.net") is False
    assert is_valid_upi_vpa("billing", "service.io") is False
    assert is_valid_upi_vpa("admin", "amazon.in") is False

def test_extract_upi_ids_from_text():
    text = "Send refund request to refund.desk@paytm or contact us at fraud@ybl. Do NOT email support@google.com."
    upi_ids = extract_upi_ids(text)
    assert "refund.desk@paytm" in upi_ids
    assert "fraud@ybl" in upi_ids
    assert not any("google.com" in u for u in upi_ids)

def test_extract_phone_numbers():
    text = "Call officer on +919876543210 or alternate 918765432109 or direct 9988776655. Intl: +1 800 555 0199."
    phones = extract_phone_numbers(text)
    assert "+919876543210" in phones
    assert "+918765432109" in phones
    assert "+919988776655" in phones
    assert any("800" in p for p in phones)

def test_normalize_phone():
    assert normalize_phone("9876543210") == "+919876543210"
    assert normalize_phone("09876543210") == "+919876543210"
    assert normalize_phone("+91-9876543210") == "+919876543210"

def test_pii_masking():
    assert mask_upi_id("fraud@ybl") == "fr***@ybl"
    assert mask_upi_id("user.name123@okaxis") == "us***@okaxis"

    masked_phone = mask_phone_number("+919876543210")
    assert "****" in masked_phone
    assert "3210" in masked_phone

    text = "Payment sent to scammer@ybl with phone +919876543210"
    masked_text = mask_pii_in_text(text)
    assert "sc***@ybl" in masked_text
    assert "9876543210" not in masked_text

def test_extract_all_entities():
    sample = "Urgent: Pay Rs 500 to fee@okaxis or visit http://scam.top or call 9876543210."
    res = extract_all_entities(sample)
    assert "http://scam.top" in res["urls"]
    assert "fee@okaxis" in res["upi_ids"]
    assert "+919876543210" in res["phone_numbers"]

