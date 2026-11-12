import os
import json
import random
import re
from typing import List, Tuple, Dict, Any
import numpy as np
import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, precision_recall_fscore_support

RANDOM_SEED = 42
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

BANKS = ["SBI", "HDFC", "ICICI", "Axis Bank", "PNB", "Bank of Baroda", "Kotak", "Canara Bank", "Union Bank"]
DOMAINS = [
    "sbi-kyc-update.top", "hdfc-secure-verify.xyz", "pnb-netbanking-login.site",
    "icici-pan-link.online", "kyc-verification-help.icu", "bank-portal-update.live",
    "wb-bill-refund.xyz", "parivahan-challan-pay.top", "indiapost-parcel-hold.buzz"
]
VPAS = ["fraud@ybl", "refund.dept@paytm", "prize.winner@okaxis", "support.desk@apl", "cashback@ibl"]
PHONES = ["+919876543210", "+918765432109", "+919988776655", "+917890123456", "+919123456789"]

def generate_message_dataset(n_per_category: int = 400) -> Tuple[List[str], List[str]]:
    """
    Generates >= 3,600 realistic, contextual, balanced synthetic messages
    in English and Hinglish covering 9 categories, with hard negatives.
    """
    data: List[Tuple[str, str]] = []

    # 1. KYC_FRAUD
    kyc_templates_en = [
        "Dear {bank} customer, your NetBanking access and debit card will be blocked today due to pending KYC. Update immediately at http://{domain}/login to avoid penalty.",
        "URGENT: Your {bank} account #{acct} KYC has expired. Click http://{domain}/kyc to upload PAN and Aadhaar or account will be permanently suspended.",
        "Dear User, your account with {bank} is suspended. Update your KYC details now at http://{domain}/verify to restore access within 24 hours.",
        "Alert: Incomplete KYC document detected for your {bank} savings account. Kindly update PAN card at http://{domain}/update today.",
        "Your {bank} mobile banking has been deactivated due to non-compliance of KYC. Re-activate by logging in at http://{domain}/auth.",
        "Important notification from {bank}: Submit KYC verification before midnight or daily transaction limit will be reduced to zero. Link: http://{domain}/step1.",
    ]
    kyc_templates_hi = [
        "Priya {bank} grahak, aapka KYC expire ho chuka hai. Turant http://{domain}/login par update karein warna aapka account aaj hi block ho jayega.",
        "{bank} alert: Aapka PAN card account se link nahi hai. Aaj hi http://{domain}/kyc par jao aur KYC submit karo warna legal action hoga.",
        "Aapka {bank} khata freeze kar diya gaya hai. Account chalu rakhne ke liye is link par apna KYC update karein: http://{domain}/update.",
        "Dhayan dein! {bank} NetBanking band hone wali hai. 24 ghante ke andar http://{domain}/verify par jakar KYC complete karein.",
        "Aapka ATM card block ho gaya hai. Dobara chalu karne ke liye KYC form bharein: http://{domain}/atm.",
    ]

    for _ in range(n_per_category):
        bank = random.choice(BANKS)
        domain = random.choice(DOMAINS)
        acct = random.randint(1000, 9999)
        tmpl = random.choice(kyc_templates_en if random.random() > 0.4 else kyc_templates_hi)
        msg = tmpl.format(bank=bank, domain=domain, acct=acct)
        data.append((msg, "KYC_FRAUD"))

    # 2. LOTTERY
    lottery_templates_en = [
        "Congratulations! Your mobile number won cash prize of Rs {amount:,} in KBC Season Lucky Draw! Call WhatsApp Manager at {phone} to claim your prize.",
        "Dear Customer, you have been selected as lucky winner for Tata Safari SUV / Cash reward of Rs {amount:,}. Contact official coordinator on {phone}.",
        "BIG WIN! You have won Rs {amount:,} in International Mobile Lottery. Send processing fee Rs 2,500 via UPI to {vpa} to disburse your winning funds.",
        "Congratulations! Your Flipkart Order #{acct} won an Apple iPhone 15 Pro Max. Pay courier delivery fee Rs 999 to {vpa} to dispatch package.",
        "You won Rs {amount:,} reward points redemption. Claim instant cash prize by contacting lottery desk at {phone} with your reference #{acct}.",
    ]
    lottery_templates_hi = [
        "Badhai ho! Aapke mobile number ne KBC Lucky Draw mein Rs {amount:,} jeete hain. Inaam lene ke liye turant WhatsApp karein {phone} par.",
        "Aapka number Tata Motors lucky contest mein first prize ke liye chuna gaya hai. Gaadi ya cash lene ke liye manager se baat karein {phone}.",
        "Congratulations! Aapko Rs {amount:,} ka cash prize mila hai. File charge Rs 1,500 UPI ID {vpa} par bhej kar apna check paayein.",
        "Aapne jita hai 25 Lakh ka lottery! Claim karne ke liye lottery officer {phone} par sampark karein.",
    ]

    for _ in range(n_per_category):
        amount = random.choice([500000, 1000000, 2500000, 3500000])
        phone = random.choice(PHONES)
        vpa = random.choice(VPAS)
        acct = random.randint(10000, 99999)
        tmpl = random.choice(lottery_templates_en if random.random() > 0.4 else lottery_templates_hi)
        msg = tmpl.format(amount=amount, phone=phone, vpa=vpa, acct=acct)
        data.append((msg, "LOTTERY"))

    # 3. REFUND_SCAM
    refund_templates_en = [
        "Dear customer, your electricity bill excess payment refund of Rs {amount:,} is approved. Click http://{domain}/refund to credit into your bank account.",
        "Income Tax Dept: Tax refund of Rs {amount:,} has been sanctioned for FY 2025-26. Verify account details at http://{domain}/itr to receive money.",
        "Amazon Refund Alert: Return for order #{acct} processed. Accept collect request of Rs {amount:,} on PhonePe / GPay from {vpa} to receive refund.",
        "Dear User, your duplicate payment of Rs {amount:,} is pending reversal. Click http://{domain}/reversal and enter your UPI PIN to accept credit.",
        "Payment gateway reversal: Rs {amount:,} is waiting to be deposited. Open UPI app and approve pending request to credit your wallet.",
    ]
    refund_templates_hi = [
        "Priya grahak, aapka bijli bill ka refund Rs {amount:,} pending hai. Apne khate mein paise paane ke liye http://{domain}/refund par click karein.",
        "Income Tax vibhag se suchna: Aapka Rs {amount:,} ka refund pass ho gaya hai. Turant link http://{domain}/tax par click karke credit lein.",
        "Aapka payment fail ho gaya tha, Rs {amount:,} refund lene ke liye UPI collect request accept karein aur PIN enter karein.",
        "Amazon refund lene ke liye is link par apna UPI ID aur bank verify karein: http://{domain}/cashback.",
    ]

    for _ in range(n_per_category):
        amount = random.randint(850, 9500)
        domain = random.choice(DOMAINS)
        vpa = random.choice(VPAS)
        acct = random.randint(10000, 99999)
        tmpl = random.choice(refund_templates_en if random.random() > 0.4 else refund_templates_hi)
        msg = tmpl.format(amount=amount, domain=domain, vpa=vpa, acct=acct)
        data.append((msg, "REFUND_SCAM"))

    # 4. JOB_SCAM
    job_templates_en = [
        "Part-time online work opportunity! Earn Rs 3,000 to 8,000 daily by liking YouTube videos and rating hotels on Google Maps. Contact HR on WhatsApp {phone}.",
        "Work from Home job hiring! Daily payout Rs 2,500 - 5,000. No experience needed. Simple data entry / reviewing tasks. Message HR manager at {phone}.",
        "Amazon / Flipkart part-time job offer: Earn up to Rs 50,000 per month from your phone. Zero initial investment. Start today: WhatsApp {phone}.",
        "Freelance typing and reviewing tasks available. Get paid Rs 500 per task directly to UPI. Contact hiring team at {phone} to begin.",
        "Urgent requirement: Online social media promoter. Earn daily Rs 4,500. Message hiring coordinator on WhatsApp {phone} for immediate onboarding.",
    ]
    job_templates_hi = [
        "Ghar baithe kamayein Rs 3,000 se 7,000 rozana YouTube video like karke aur reviews dekar. Turant WhatsApp karein {phone} par.",
        "Part-time job ka shandaar mauka! Mobile se 2 ghante kaam karke 4,000 kamayein. Koi registration fee nahi. Contact HR: {phone}.",
        "Online work from home naukri: Daily salary seedhe bank khate mein. Abhi WhatsApp karein {phone} par.",
        "Aapko part time job ke liye select kiya gaya hai. Per day payout Rs 3,500. Joining ke liye message karein {phone}.",
    ]

    for _ in range(n_per_category):
        phone = random.choice(PHONES)
        tmpl = random.choice(job_templates_en if random.random() > 0.4 else job_templates_hi)
        msg = tmpl.format(phone=phone)
        data.append((msg, "JOB_SCAM"))

    # 5. FAKE_CUSTOMER_CARE
    care_templates_en = [
        "PhonePe Support: Did you face UPI transaction failure or wrong transfer? Call 24x7 toll-free helpline executive at {phone} for instant refund.",
        "Google Pay Customer Care: For pending transactions, cashback issues or refund assistance, speak to verified support agent at {phone}.",
        "SBI Customer Helpline: Facing NetBanking or debit card issue? Connect immediately with our support desk at {phone} for fast resolution.",
        "Paytm Wallet Helpdesk: If money debited but not credited, call our emergency support center at {phone} to resolve in 5 minutes.",
        "Airtel Payments Bank Care: For account unblock or transaction disputes, call our verified support number {phone}.",
    ]
    care_templates_hi = [
        "PhonePe grahak seva: Agar aapka transaction fail hua hai ya paise fas gaye hain toh turant customer care {phone} par call karein.",
        "Google Pay helpline number: Kisi bhi UPI samasya ya refund ke liye hamare support number {phone} par sampark karein.",
        "SBI customer support: Khata freeze ya UPI failure ke liye hamare 24 ghante chalu number {phone} par baat karein.",
        "Paytm sahayata kendra: Failed transaction ka turant refund paane ke liye is helpline {phone} par call karein.",
    ]

    for _ in range(n_per_category):
        phone = random.choice(PHONES)
        tmpl = random.choice(care_templates_en if random.random() > 0.4 else care_templates_hi)
        msg = tmpl.format(phone=phone)
        data.append((msg, "FAKE_CUSTOMER_CARE"))

    # 6. COLLECT_REQUEST
    collect_templates_en = [
        "Ram Store has sent you a collect request for Rs {amount:,} on PhonePe. Click here to approve and enter your UPI PIN to receive money.",
        "Payment alert: You have received a payment request of Rs {amount:,} from {vpa}. Approve request to credit cashback into your account.",
        "Paytm Collect Request: Request for Rs {amount:,} pending your approval. Enter secret UPI PIN to complete receiving the reward.",
        "Incoming fund transfer: Rs {amount:,} waiting for verification. Approve UPI request from {vpa} to release funds to your bank.",
        "Google Pay Notice: Rs {amount:,} cashback collect request initiated. Click approve and enter UPI PIN to deposit into wallet.",
    ]
    collect_templates_hi = [
        "Aapko {vpa} se Rs {amount:,} ka collect request mila hai. Paise receive karne ke liye request approve karein aur apna UPI PIN dalein.",
        "PhonePe collect request: Rs {amount:,} paane ke liye turant approve karein aur 4/6 digit ka PIN enter karein.",
        "Cashback lene ke liye UPI app kholein aur pending collect request Rs {amount:,} par click karke apna secret PIN darj karein.",
        "Payment receive karne ke liye is request ko accept karein aur UPI PIN enter karein: Rs {amount:,} from {vpa}.",
    ]

    for _ in range(n_per_category):
        amount = random.randint(1200, 15000)
        vpa = random.choice(VPAS)
        tmpl = random.choice(collect_templates_en if random.random() > 0.4 else collect_templates_hi)
        msg = tmpl.format(amount=amount, vpa=vpa)
        data.append((msg, "COLLECT_REQUEST"))

    # 7. LOAN_SCAM
    loan_templates_en = [
        "Pre-approved personal loan of Rs {amount:,} sanctioned at 1.5% interest! Zero CIBIL check, no documents required. Download APK at http://{domain}/loan to disburse.",
        "Congratulations! Your loan application of Rs {amount:,} is approved. Pay file processing fee Rs 1,499 via UPI to {vpa} to release funds.",
        "Dhani Instant Credit: Rs {amount:,} ready in your wallet. Pay GST stamp verification fee Rs 999 to {vpa} to disburse immediately.",
        "Get instant cash loan up to Rs {amount:,} in 5 minutes directly in your bank account. Apply online now: http://{domain}/apply.",
        "Special Festive Loan Offer: Rs {amount:,} instant loan with no salary slip. Download loan app: http://{domain}/app.",
    ]
    loan_templates_hi = [
        "Aapka Rs {amount:,} ka loan approve ho chuka hai. Bina kisi document ke 10 minute me paise paayein. APK download karein: http://{domain}/loan.",
        "Badhai ho! Aapko Rs {amount:,} ka instant loan mila hai. File charge Rs 1,200 UPI ID {vpa} par transfer karein aur paise paayein.",
        "Aadhaar card par instant Rs {amount:,} ka loan paayein bina CIBIL score ke. Abhi apply karein: http://{domain}/apply.",
        "Bina guarantee ke Rs {amount:,} ka personal loan turant apne bank khate mein lein. Link: http://{domain}/quickloan.",
    ]

    for _ in range(n_per_category):
        amount = random.choice([100000, 250000, 500000, 1000000])
        domain = random.choice(DOMAINS)
        vpa = random.choice(VPAS)
        tmpl = random.choice(loan_templates_en if random.random() > 0.4 else loan_templates_hi)
        msg = tmpl.format(amount=amount, domain=domain, vpa=vpa)
        data.append((msg, "LOAN_SCAM"))

    # 8. OTHER
    other_templates_en = [
        "India Post: Your parcel package #{acct} is on hold due to wrong address. Update your address at http://{domain}/delivery within 12 hours or item will be returned.",
        "Traffic Police e-Challan Notice: Unpaid challan of Rs {amount} pending on vehicle DL01AB{acct}. Pay today at http://{domain}/challan to avoid arrest warrant.",
        "Electricity Department: Your power connection will be disconnected tonight at 9:30 PM due to unpaid bill. Call electricity officer at {phone} immediately.",
        "Courier delivery alert: Package delivery failed. Reschedule delivery date and pay redelivery fee Rs 5 at http://{domain}/shipment.",
        "WhatsApp subscription warning: Your account will expire today. Update payment information at http://{domain}/wa to retain chats.",
    ]
    other_templates_hi = [
        "India Post alert: Aapka parcel delivery galat address ke karan ruk gaya hai. 24 ghante me address verify karein: http://{domain}/parcel.",
        "Traffic e-challan alert: Aapke vahan par Rs {amount} ka challan baki hai. Court notice se bachne ke liye aaj hi bharein: http://{domain}/challan.",
        "Bijli vibhag suchna: Aapka bijli connection aaj raat 9:30 baje kaat diya jayega. Bill payment verify karne ke liye officer {phone} par call karein.",
        "Courier delivery fail ho gaya hai. Dobara delivery ke liye link par click karein: http://{domain}/courier.",
    ]

    for _ in range(n_per_category):
        amount = random.choice([500, 1000, 1500, 2000])
        domain = random.choice(DOMAINS)
        phone = random.choice(PHONES)
        acct = random.randint(1000, 9999)
        tmpl = random.choice(other_templates_en if random.random() > 0.4 else other_templates_hi)
        msg = tmpl.format(amount=amount, domain=domain, phone=phone, acct=acct)
        data.append((msg, "OTHER"))

    # 9. NONE (Hard negatives: Genuine bank OTPs, bank debit/credit alerts, delivery alerts, customer care, personal chats)
    legit_templates = [
        # Genuine OTPs
        "{otp} is your OTP for transaction of INR {amount:.2f} at {merchant} on {bank} Card ending {acct}. Valid for 10 mins. Do not share OTP with anyone.",
        "{otp} is your secret One Time Password (OTP) for login to {bank} NetBanking. Bank NEVER asks for OTP/password. Never share it with anyone.",
        "Dear Customer, {otp} is your verification code to authenticate UPI registration on your mobile. Do not share this OTP with anyone.",
        "Use OTP {otp} to complete payment of Rs {amount:.2f} for your order at Swiggy. Valid for 5 minutes. PayGuard: Do not disclose OTP.",
        "Your OTP for Aadhaar authentication is {otp}. Generated at {bank}. Do not disclose to anyone for security reasons.",
        # Genuine Transaction Debits / Credits
        "Dear Customer, INR {amount:.2f} debited from A/C XX{acct} on 12-Nov-26 by UPI/{vpa}/Ref {ref}. If not done by you, SMS BLOCK to 567676.",
        "A/C XX{acct} credited with INR {amount:.2f} on 12-Nov-26 by UPI/{vpa}. Available balance INR {bal:.2f}. - {bank}",
        "Sent INR {amount:.2f} successfully from {bank} account XX{acct} to {vpa} on 12-Nov-2026. UPI Ref: {ref}.",
        "Received INR {amount:.2f} in your {bank} A/C XX{acct} from Rohit Kumar via UPI. Updated balance: INR {bal:.2f}.",
        # Genuine Delivery Notifications
        "Your Amazon package with tracking #{ref} is out for delivery today. Delivery associate: Manoj Kumar ({phone}). Share delivery code {otp} only at handover.",
        "Your Flipkart shipment containing order #{acct} will be delivered today by 7 PM. Track your live order in the Flipkart app.",
        "Your Zomato delivery partner has picked up your food order and is heading towards your location. Estimated arrival in 15 minutes.",
        # Genuine Service Alerts
        "Dear Airtel customer, your monthly recharge pack of Rs 299 expires on 15-Nov-2026. Recharge on Airtel Thanks app or airtel.in to continue services.",
        "Your {bank} credit card statement for statement cycle Nov 2026 is generated. Total due: INR {amount:.2f}. Min due: INR 500. Pay via official mobile app.",
        "Thank you for contacting customer support. Your complaint ticket #{acct} has been resolved. Rate our service on the official app.",
        # Normal Personal Conversations (English & Hinglish)
        "Hey are you coming to college tomorrow? Let me know so we can submit the project together.",
        "Mummy ne bola hai aate waqt dahi aur doodh le aana market se.",
        "I sent the meeting notes and presentation on your email. Please review when you have time.",
        "Bhai kal shaam ko cricket khelne chalenge ground pe. 5 baje ready rehna.",
        "Can you send me the address of the restaurant where we are having dinner tonight?",
        "Please bring my notebook that I left at your place last weekend.",
        "Flight is on time. Will land in Delhi around 8 PM. See you at terminal 3.",
    ]

    merchants = ["Swiggy", "Zomato", "Amazon", "Flipkart", "IRCTC", "Uber", "BookMyShow"]
    for _ in range(n_per_category):
        bank = random.choice(BANKS)
        otp = random.randint(100000, 999999)
        amount = random.choice([150.0, 399.0, 1250.0, 4500.0, 12000.0])
        acct = random.randint(1000, 9999)
        ref = random.randint(100000000000, 999999999999)
        bal = random.randint(5000, 85000)
        phone = random.choice(PHONES)
        merchant = random.choice(merchants)
        vpa = random.choice(["shop@okaxis", "friend@ybl", "swiggy@icici", "uber@hdfcbank"])
        tmpl = random.choice(legit_templates)
        msg = tmpl.format(bank=bank, otp=otp, amount=amount, acct=acct, ref=ref, bal=bal, phone=phone, merchant=merchant, vpa=vpa)
        data.append((msg, "NONE"))

    # Shuffle dataset
    random.shuffle(data)
    texts = [t[0] for t in data]
    labels = [t[1] for t in data]
    return texts, labels

def generate_voice_dataset(n_per_category: int = 150) -> Tuple[List[str], List[str]]:
    """
    Generates realistic voice conversation transcripts across all 11 voice scam categories.
    """
    data: List[Tuple[str, str]] = []

    # 1. BANK_IMPERSONATION
    bank_imp_samples = [
        "Hello, I am calling from State Bank of India main branch. Your debit card and NetBanking services are expiring today. Please share your account number and the verification code sent to your phone to renew.",
        "Namaste, main HDFC Bank head office se senior manager bol raha hoon. Aapke account mein unauthorized international transaction attempt hua hai. Turant card details verify kijiye.",
        "Good morning, this is ICICI Bank security department. Your KYC has lapsed and your account will be frozen within 2 hours. Kindly verify your identity by providing your NetBanking credentials.",
        "Main RBI verification cell se call kar raha hoon. Aapke khate mein suspicious activity dekhi gayi hai. Turant apna bank verification confirm kijiye.",
    ]
    for _ in range(n_per_category):
        data.append((random.choice(bank_imp_samples) + f" Reference case id {random.randint(1000,9999)}.", "BANK_IMPERSONATION"))

    # 2. POLICE_OR_GOVERNMENT_IMPERSONATION
    police_samples = [
        "I am Officer Vikram Sharma from Delhi Crime Branch. A courier parcel registered under your Aadhaar containing illegal narcotics and fake passports was seized at Mumbai airport.",
        "This is Deputy Commissioner from Customs Department. An international parcel in your name contains 16 fake credit cards and contraband. You must clarify this matter immediately.",
        "Main CBI headquarters New Delhi se bol raha hoon. Aapke naam par Money Laundering ka case darj hua hai. Aapko turant investigation join karni hogi.",
        "Attention, this is Telecom Regulatory Authority and Mumbai Police. Your mobile number is linked to illegal harassment calls and will be disconnected in 2 hours.",
    ]
    for _ in range(n_per_category):
        data.append((random.choice(police_samples) + f" Case record #{random.randint(1000,9999)}.", "POLICE_OR_GOVERNMENT_IMPERSONATION"))

    # 3. DIGITAL_ARREST
    digital_arrest_samples = [
        "You are placed under Digital Arrest by Supreme Court orders. You cannot disconnect this call or switch off your camera. Do not inform family or anyone. Transfer funds to RBI escrow account for verification.",
        "Aap is waqt Digital Arrest mein hain. Jab tak hamari inquiry complete nahi hoti aap room se bahar nahi jayenge aur phone disconnect nahi karenge. Hamare official verification account mein security deposit transfer karein.",
        "Digital arrest protocol has been activated for your National Identity. You must remain on video call continuously. Any attempt to contact outsiders will lead to immediate SWAT dispatch.",
        "Listen carefully, you are in digital arrest. Do not tell your wife or children. Go to your bank or open mobile app and transfer the funds to the legal clearance account.",
    ]
    for _ in range(n_per_category):
        data.append((random.choice(digital_arrest_samples), "DIGITAL_ARREST"))

    # 4. OTP_FRAUD
    otp_fraud_samples = [
        "Sir, I have just triggered a security token to your mobile number. Please read out the 6-digit OTP so I can cancel the fraudulent transaction on your credit card.",
        "Madam, aapke phone par ek One Time Password aaya hoga. Jaldi se OTP bata dijiye warna account se 50,000 rupaye kat jayenge.",
        "To approve your cashback reward, please state the OTP received on your SMS. Quickly, it is valid only for 60 seconds.",
        "Main customer care se hoon. Refund complete karne ke liye jo 4-digit PIN ya OTP aaya hai wo share karein.",
    ]
    for _ in range(n_per_category):
        data.append((random.choice(otp_fraud_samples), "OTP_FRAUD"))

    # 5. FAKE_CUSTOMER_CARE
    fake_care_samples = [
        "Hello sir, you raised a complaint regarding failed Google Pay transaction of Rs 5,000. I am calling from Google Pay technical team to assist in instant refund.",
        "PhonePe support here. Regarding your refund ticket, I will guide you through our merchant portal to reverse the money into your primary account.",
        "Airtel Payments customer care calling. Your UPI transaction got stuck due to server error. We will issue a direct reversal link now.",
    ]
    for _ in range(n_per_category):
        data.append((random.choice(fake_care_samples), "FAKE_CUSTOMER_CARE"))

    # 6. LOAN_SCAM
    loan_samples = [
        "Congratulations sir, your pre-approved loan of 5 Lakh rupees is sanctioned at 2 percent interest rate. You only have to pay a file processing fee of 2,500 rupees via UPI to disburse.",
        "Aapka 2 lakh ka personal loan approve ho gaya hai bina kisi income proof ke. Registration charges 1,500 transfer kijiye aur aadhe ghante mein paise khate mein.",
        "Instant credit approval from NBFC. Transfer 1,999 GST clearance deposit to get loan amount in your bank.",
    ]
    for _ in range(n_per_category):
        data.append((random.choice(loan_samples), "LOAN_SCAM"))

    # 7. INVESTMENT_SCAM
    invest_samples = [
        "Hello madam, I am calling from VIP Stock Trading Desk. We provide daily insider stock tips with guaranteed 300 percent return in one week. Start with just 10,000 rupees.",
        "Hamara crypto arbitrage trading pool join karein. Rozana 15 percent guaranteed profit milta hai. Aapko bas hamare platform par deposit karna hai.",
        "Invest in our foreign exchange gold scheme. 100 percent risk free returns guaranteed by SEBI licensed experts.",
    ]
    for _ in range(n_per_category):
        data.append((random.choice(invest_samples), "INVESTMENT_SCAM"))

    # 8. PAYMENT_FRAUD
    pay_fraud_samples = [
        "I have accidentally sent 25,000 rupees to your UPI account instead of my brother's account. Please check your SMS and return my money immediately to my UPI ID.",
        "Electricity department alert: Your meter will be disconnected today at 10 PM. You must clear the outstanding charge of 3,450 rupees right now over the phone.",
        "Main military army officer bol raha hoon. Mujhe aapka purana sofa khareedna hai OLX se. Main advance bhej raha hoon, aap UPI request accept karein.",
    ]
    for _ in range(n_per_category):
        data.append((random.choice(pay_fraud_samples), "PAYMENT_FRAUD"))

    # 9. REMOTE_ACCESS_SCAM
    remote_samples = [
        "Sir, to fix your mobile banking error, please go to Google Play Store and download AnyDesk or TeamViewer QuickSupport application.",
        "Apne phone mein AnyDesk app install kijiye aur jo 9 digit ka code screen par dikh raha hai wo mujhe batayein taaki main error theek kar sakoon.",
        "Please install RustDesk remote tool so our technician can verify your device security settings and clear the virus.",
        "Screen share start kijiye aur apna banking app open karein taaki hum transaction debug kar sakein.",
    ]
    for _ in range(n_per_category):
        data.append((random.choice(remote_samples), "REMOTE_ACCESS_SCAM"))

    # 10. OTHER
    other_voice_samples = [
        "This is courier services calling. Your parcel has customs clearance problem. Pay clearance duty immediately or customs will file charges.",
        "Aapka traffic court summons issue ho gaya hai. Fine pay karein turant.",
        "Your WhatsApp account verification code has been compromised. Please listen to security instructions.",
    ]
    for _ in range(n_per_category):
        data.append((random.choice(other_voice_samples), "OTHER"))

    # 11. NONE (Genuine calls: delivery agents, bank relationship calls without credential theft, friend chats)
    none_voice_samples = [
        "Hello sir, I am your Amazon delivery agent Manoj. I am standing outside your apartment gate. Please come down to collect your package.",
        "Hi doctor, I am calling to confirm my dental appointment scheduled for tomorrow at 4 PM. Is the doctor available?",
        "Good afternoon Mr. Sharma, this is HDFC Bank relationship manager calling to check if you are satisfied with your credit card rewards. No personal details needed.",
        "Hey Rohan, are we meeting at the cafe in Connaught Place this evening? Let me know once you leave office.",
        "Bhaiya Zomato se delivery boy bol raha hoon. Aapka address nahi mil raha hai, landmark bata denge please?",
        "Mom called to ask what time you will reach home for dinner. She made your favorite biryani today.",
        "Hi, calling from Airtel broadband service. Your technician visit for fiber installation is confirmed for tomorrow morning 11 AM.",
    ]
    for _ in range(n_per_category):
        data.append((random.choice(none_voice_samples), "NONE"))

    random.shuffle(data)
    texts = [t[0] for t in data]
    labels = [t[1] for t in data]
    return texts, labels

def train_and_evaluate_message_model():
    """Trains the message scam classifier and saves evaluation metrics & plots."""
    print("Generating message classification dataset (>= 3,600 samples)...")
    texts, labels = generate_message_dataset(n_per_category=420)
    print(f"Total message samples generated: {len(texts)}")

    # Stratified Train/Test Split (80/20)
    X_train, X_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.20, random_state=RANDOM_SEED, stratify=labels
    )

    print(f"Training on {len(X_train)} samples, testing on {len(X_test)} samples...")

    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(
            ngram_range=(1, 2),
            max_features=8000,
            sublinear_tf=True,
            strip_accents="unicode",
        )),
        ("clf", LogisticRegression(
            C=3.0,
            max_iter=1000,
            class_weight="balanced",
            random_state=RANDOM_SEED,
        )),
    ])

    pipeline.fit(X_train, y_train)
    y_pred = pipeline.predict(X_test)

    # Evaluate
    acc = float(accuracy_score(y_test, y_pred))
    p_macro, r_macro, f1_macro, _ = precision_recall_fscore_support(y_test, y_pred, average="macro")
    p_weight, r_weight, f1_weight, _ = precision_recall_fscore_support(y_test, y_pred, average="weighted")
    clf_report = classification_report(y_test, y_pred, output_dict=True)

    classes = sorted(list(set(labels)))
    cm = confusion_matrix(y_test, y_pred, labels=classes)

    print(f"Message Model Accuracy: {acc * 100:.2f}% | Macro F1: {f1_macro:.4f}")

    # Plot Confusion Matrix
    plt.figure(figsize=(10, 8))
    plt.imshow(cm, interpolation="nearest", cmap=plt.cm.Blues)
    plt.title("PayGuard AI - Message Scam Classifier Confusion Matrix (Synthetic Dataset)")
    plt.colorbar()
    tick_marks = np.arange(len(classes))
    plt.xticks(tick_marks, classes, rotation=45, ha="right", fontsize=9)
    plt.yticks(tick_marks, classes, fontsize=9)

    thresh = cm.max() / 2.0
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            plt.text(
                j, i, format(cm[i, j], "d"),
                horizontalalignment="center",
                color="white" if cm[i, j] > thresh else "black",
                fontsize=8,
            )

    plt.ylabel("True Label")
    plt.xlabel("Predicted Label")
    plt.tight_layout()

    os.makedirs("extras/ml", exist_ok=True)
    os.makedirs("extras/ml/models", exist_ok=True)

    cm_path = "extras/ml/confusion_matrix.png"
    plt.savefig(cm_path, dpi=200)
    plt.close()
    print(f"Saved confusion matrix plot to {cm_path}")

    metrics = {
        "dataset_type": "Synthetic (Context-balanced English, Hindi, Hinglish with hard negatives)",
        "random_seed": RANDOM_SEED,
        "n_samples": len(texts),
        "n_train": len(X_train),
        "n_test": len(X_test),
        "accuracy": round(acc, 4),
        "precision_macro": round(float(p_macro), 4),
        "recall_macro": round(float(r_macro), 4),
        "f1_macro": round(float(f1_macro), 4),
        "precision_weighted": round(float(p_weight), 4),
        "recall_weighted": round(float(r_weight), 4),
        "f1_weighted": round(float(f1_weight), 4),
        "classes": classes,
        "classification_report": clf_report,
    }

    metrics_path = "extras/ml/metrics.json"
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    print(f"Saved evaluation metrics to {metrics_path}")

    model_path = "extras/ml/models/message_model.joblib"
    joblib.dump(pipeline, model_path)
    print(f"Saved message model pipeline to {model_path}")

def train_and_evaluate_voice_model():
    """Trains the voice scam classifier and saves evaluation metrics."""
    print("Generating voice conversation dataset (>= 1,600 samples)...")
    texts, labels = generate_voice_dataset(n_per_category=150)
    print(f"Total voice samples generated: {len(texts)}")

    X_train, X_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.20, random_state=RANDOM_SEED, stratify=labels
    )

    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(
            ngram_range=(1, 2),
            max_features=6000,
            sublinear_tf=True,
            strip_accents="unicode",
        )),
        ("clf", LogisticRegression(
            C=3.0,
            max_iter=1000,
            class_weight="balanced",
            random_state=RANDOM_SEED,
        )),
    ])

    pipeline.fit(X_train, y_train)
    y_pred = pipeline.predict(X_test)

    acc = float(accuracy_score(y_test, y_pred))
    p_macro, r_macro, f1_macro, _ = precision_recall_fscore_support(y_test, y_pred, average="macro")
    clf_report = classification_report(y_test, y_pred, output_dict=True)

    print(f"Voice Model Accuracy: {acc * 100:.2f}% | Macro F1: {f1_macro:.4f}")

    metrics = {
        "dataset_type": "Synthetic Voice Transcripts (English, Hindi, Hinglish)",
        "random_seed": RANDOM_SEED,
        "n_samples": len(texts),
        "accuracy": round(acc, 4),
        "f1_macro": round(float(f1_macro), 4),
        "classification_report": clf_report,
    }

    with open("extras/ml/voice_metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    joblib.dump(pipeline, "extras/ml/models/voice_model.joblib")
    print("Saved voice model pipeline to extras/ml/models/voice_model.joblib")

if __name__ == "__main__":
    train_and_evaluate_message_model()
    train_and_evaluate_voice_model()
    print("All ML models trained and evaluated successfully!")

