from typing import Dict, Any, Tuple

MESSAGE_SCAM_KNOWLEDGE: Dict[str, Dict[str, str]] = {
    "KYC_FRAUD": {
        "title": "KYC Expiry / Account Blocking Threat",
        "explanation": "The sender falsely claims your bank account, SIM card, or PAN/Aadhaar KYC has expired and threatens suspension if you don't click a link or call immediately.",
        "what_scammers_do": "Scammers harvest your NetBanking passwords, Aadhaar details, and OTPs via spoofed phishing sites to drain your bank accounts.",
        "recommended_action": "Do not click any link or call numbers in the message. Official banks never update KYC via SMS links. Visit your official bank branch or legitimate mobile app.",
    },
    "LOTTERY": {
        "title": "Lottery / Prize / Reward Fraud",
        "explanation": "The message announces that your phone number won a massive lottery (e.g. KBC, Kaun Banega Crorepati, Lucky Draw) or an expensive smartphone.",
        "what_scammers_do": "Scammers convince you to pay an advance 'processing fee', 'TDS tax', or 'registration charge' before releasing a non-existent prize, then disappear.",
        "recommended_action": "Never pay money to receive a prize. If you didn't buy a lottery ticket, you cannot win one. Block and report the sender.",
    },
    "REFUND_SCAM": {
        "title": "Deceptive Refund / Overpayment Trap",
        "explanation": "The message claims a refund is waiting for you (e.g. electricity bill excess, electricity department, tax refund, or e-commerce return) and asks you to accept money via link or UPI.",
        "what_scammers_do": "Scammers send a UPI 'Collect Request' or ask you to scan a QR code and enter your UPI PIN. Entering your UPI PIN sends your money to them rather than receiving a refund.",
        "recommended_action": "Remember: You NEVER need to enter your UPI PIN or accept a collect request to receive money. Decline any incoming requests immediately.",
    },
    "JOB_SCAM": {
        "title": "Work-From-Home / Part-Time Job Scam",
        "explanation": "Offers effortless high-paying part-time jobs (e.g. liking YouTube videos, reviewing hotels, rating movies) promising ₹3,000–₹10,000 daily.",
        "what_scammers_do": "After paying small initial amounts to build false trust, scammers demand larger 'prepaid task deposits' or 'crypto investment fees' that cannot be withdrawn.",
        "recommended_action": "Legitimate employers never ask candidates to pay money for tasks or equipment. Stop all communication immediately.",
    },
    "FAKE_CUSTOMER_CARE": {
        "title": "Impersonated Customer Support Helpline",
        "explanation": "Provides a fake customer care helpline for banks, delivery services, or payment wallets (Google Pay, PhonePe, Paytm).",
        "what_scammers_do": "The fraudster impersonating a support executive instructs you to install remote access apps (AnyDesk, TeamViewer) or send test UPI amounts.",
        "recommended_action": "Never search customer care numbers on public search engines or social media. Always use the official verified app.",
    },
    "COLLECT_REQUEST": {
        "title": "Deceptive UPI Collect Request",
        "explanation": "Contains instructions or links to approve an incoming payment request under the false promise of receiving funds or cashbacks.",
        "what_scammers_do": "Deceives you into entering your UPI PIN on your phone, authorizing money to be debited directly from your account.",
        "recommended_action": "Reject the collect request in your UPI application. Entering your PIN always debits funds.",
    },
    "LOAN_SCAM": {
        "title": "Pre-Approved Loan / Instant Credit Trap",
        "explanation": "Offers instantaneous collateral-free loans with zero verification and very low interest rates.",
        "what_scammers_do": "Demands an upfront 'file processing charge' or 'GST deposit' and steals your contacts/photos via malicious APK apps.",
        "recommended_action": "Do not download unknown APK apps. Genuine lenders do not disburse personal loans via random WhatsApp/SMS links.",
    },
    "OTHER": {
        "title": "Suspicious Social Engineering",
        "explanation": "The message uses coercive urgency, unverified links, or requests for sensitive private information.",
        "what_scammers_do": "Attempts to lure you into unauthorized transactions or credential disclosure.",
        "recommended_action": "Exercise caution. Do not click unknown links or share credentials with unverified contacts.",
    },
    "NONE": {
        "title": "Standard Legitimate Communication",
        "explanation": "No suspicious phishing or coercive fraud indicators were detected in this message.",
        "what_scammers_do": "N/A - Message appears to be genuine notification or conversation.",
        "recommended_action": "Safe to proceed. As always, remain vigilant and never share your banking PIN or OTP with anyone.",
    },
}

VOICE_SCAM_KNOWLEDGE: Dict[str, Dict[str, str]] = {
    "BANK_IMPERSONATION": {
        "title": "Bank Officer / Manager Impersonation",
        "explanation": "Caller impersonates bank staff (e.g. SBI, HDFC, ICICI, RBI) claiming your debit card, NetBanking, or KYC requires immediate renewal.",
        "what_scammers_do": "Coerces the victim into reading out SMS OTPs or sharing card details under the threat of immediate account freezing.",
        "recommended_action": "Hang up immediately. Bank staff are strictly forbidden from asking for passwords, OTPs, or CVVs over the phone. Call your branch directly.",
    },
    "POLICE_OR_GOVERNMENT_IMPERSONATION": {
        "title": "Law Enforcement / Police Impersonation",
        "explanation": "Caller claims to be from Delhi Police, Mumbai Crime Branch, Customs, or CBI, alleging a parcel or phone number registered in your name is involved in criminal activity.",
        "what_scammers_do": "Intimidates victims with legal consequences, fabricated case files, and video calls to extort large sums under the guise of 'clearance deposits'.",
        "recommended_action": "Government agencies never conduct investigations or demand financial payments over phone calls or WhatsApp video calls. Disconnect and report to cybercrime.gov.in (1930).",
    },
    "DIGITAL_ARREST": {
        "title": "Digital Arrest Coercion Scam",
        "explanation": "Caller falsely claims you are under 'Digital Arrest' and orders you to stay on the call or camera without informing family members or lawyers.",
        "what_scammers_do": "Creates psychological panic to prevent you from seeking help, forcing you to transfer your life savings to a 'secure government verification account'.",
        "recommended_action": "There is NO legal concept of 'Digital Arrest' in Indian law. Hang up immediately. Talk to trusted family members and call 1930.",
    },
    "OTP_FRAUD": {
        "title": "Direct OTP / Banking Credential Theft",
        "explanation": "Caller directly asks you to share a one-time password (OTP), UPI PIN, or ATM PIN received on your mobile device.",
        "what_scammers_do": "Uses the OTP to authenticate an unauthorized financial debit or register your payment wallet on their device.",
        "recommended_action": "NEVER share your OTP with anyone. Banks and official service providers explicitly state: 'Do not share OTP with anyone, including bank staff'.",
    },
    "FAKE_CUSTOMER_CARE": {
        "title": "Deceptive Customer Support Helpline",
        "explanation": "Caller poses as a customer support agent resolving an e-commerce, courier, or telecom issue.",
        "what_scammers_do": "Asks you to transfer small token amounts or install remote screen-sharing tools to 'resolve' your pending request.",
        "recommended_action": "Hang up and only contact support through verified applications or the merchant's official portal.",
    },
    "LOAN_SCAM": {
        "title": "Loan Approval Advance Fee Fraud",
        "explanation": "Caller offers instant approval for personal or business loans without credit checks, requiring an advance insurance or file fee.",
        "what_scammers_do": "Collects advance fees through UPI and vanishes without disbursing any loan.",
        "recommended_action": "Do not pay any upfront fees for loan disbursement. Genuine banks deduct fees from the disbursed loan amount.",
    },
    "INVESTMENT_SCAM": {
        "title": "Guaranteed High-Return Investment Fraud",
        "explanation": "Caller promises unrealistically high, risk-free returns on stock tips, forex trading, or crypto schemes.",
        "what_scammers_do": "Channels victims into fraudulent trading portals that display fake profits, then locks withdrawals until more money is sent.",
        "recommended_action": "Never transfer money to individuals promising guaranteed stock or crypto returns. Check SEBI registration.",
    },
    "PAYMENT_FRAUD": {
        "title": "Urgent Coercive Payment Request",
        "explanation": "Demands immediate fund transfers under false pretenses such as accidental deposits or electricity bill disconnection.",
        "what_scammers_do": "Fabricates urgent crises to rush the victim into transferring funds before checking account balances.",
        "recommended_action": "Verify your own bank balance in your official app before reacting. Do not send money under pressure.",
    },
    "REMOTE_ACCESS_SCAM": {
        "title": "Remote Access / Screen Sharing Trap",
        "explanation": "Caller requests installation of remote desktop software like AnyDesk, TeamViewer, RustDesk, or QuickSupport to 'assist' you.",
        "what_scammers_do": "Once connected, scammers view your phone screen while you open banking apps, capture your credentials, and initiate unauthorized transfers.",
        "recommended_action": "Never install remote access applications on instruction from any incoming caller. Uninstall the app immediately if already downloaded.",
    },
    "OTHER": {
        "title": "Suspicious Caller Tactics",
        "explanation": "The conversation exhibits high-pressure manipulation, secrecy demands, or unverified claims.",
        "what_scammers_do": "Exploits psychological trust or fear to solicit money or information.",
        "recommended_action": "Do not share personal or banking details. Disconnect the call and verify independently.",
    },
    "NONE": {
        "title": "Normal Conversation",
        "explanation": "No fraud indicators, credential theft, or impersonation were detected in this call.",
        "what_scammers_do": "N/A - Conversation appears typical and benign.",
        "recommended_action": "Safe. Remember standard security hygiene: never share PINs or passwords with callers.",
    },
}

def get_message_explanation(category: str, score: int) -> Tuple[str, str]:
    """Returns (explanation, recommended_action) for a message scam category."""
    cat_data = MESSAGE_SCAM_KNOWLEDGE.get(category, MESSAGE_SCAM_KNOWLEDGE["OTHER"])
    if score >= 70:
        expl = f"CRITICAL RISK: {cat_data['explanation']} {cat_data['what_scammers_do']}"
    elif score >= 40:
        expl = f"SUSPICIOUS: {cat_data['explanation']}"
    else:
        expl = cat_data["explanation"]
    return expl, cat_data["recommended_action"]

def get_voice_explanation(category: str, score: int) -> Tuple[str, str]:
    """Returns (explanation, recommended_action) for a voice scam category."""
    cat_data = VOICE_SCAM_KNOWLEDGE.get(category, VOICE_SCAM_KNOWLEDGE["OTHER"])
    if score >= 70:
        expl = f"DANGER: {cat_data['explanation']} {cat_data['what_scammers_do']}"
    elif score >= 40:
        expl = f"CAUTION: {cat_data['explanation']}"
    else:
        expl = cat_data["explanation"]
    return expl, cat_data["recommended_action"]

