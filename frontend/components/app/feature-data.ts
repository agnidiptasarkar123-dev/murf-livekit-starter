export type FeatureCategory = 'schemes' | 'fraud' | 'banking' | 'helpline';

export interface FeatureItem {
  id: string;
  category: FeatureCategory;
  subCategory: string;
  title: string;
  description: string;
  fullDetails: string;
}

export const featureData: FeatureItem[] = [
  // Govt Schemes
  { 
    id: 's1', 
    category: 'schemes', 
    subCategory: 'Banking Access', 
    title: 'PM Jan Dhan Yojana', 
    description: 'National mission for financial inclusion to ensure access to financial services like basic savings accounts, remittance, credit, insurance, and pension in an affordable manner.',
    fullDetails: 'Pradhan Mantri Jan Dhan Yojana (PMJDY) provides universal access to banking facilities with at least one basic banking account for every household. Key benefits include no minimum balance requirement, free RuPay debit card, and built-in accident insurance cover of ₹2 lakh. You can open an account at any bank branch or Business Correspondent (Bank Mitra) outlet with basic KYC documents like Aadhaar.'
  },
  { 
    id: 's2', 
    category: 'schemes', 
    subCategory: 'Credit & Loans', 
    title: 'Mudra Yojana (PMMY)', 
    description: 'Provides loans up to 10 lakhs to non-corporate, non-farm small/micro enterprises.',
    fullDetails: 'Pradhan Mantri Mudra Yojana (PMMY) helps small business owners get loans without collateral. It has three categories: Shishu (loans up to ₹50,000 for startups), Kishore (₹50,000 to ₹5 lakh), and Tarun (₹5 lakh to ₹10 lakh). This is ideal for street vendors, shopkeepers, and small-scale manufacturers. Apply at any commercial bank, RRB, small finance bank, or NBFC.'
  },
  { 
    id: 's3', 
    category: 'schemes', 
    subCategory: 'Pension', 
    title: 'Atal Pension Yojana', 
    description: 'A pension scheme primarily focused on the unorganized sector workers, providing a guaranteed minimum pension.',
    fullDetails: 'Atal Pension Yojana (APY) provides a guaranteed minimum monthly pension ranging from ₹1,000 to ₹5,000 after age 60, depending on the contributions made. It is open to all bank account holders aged 18 to 40 years. The earlier you join, the lower your monthly contribution. If the subscriber dies, the spouse continues to receive the pension.'
  },
  { 
    id: 's4', 
    category: 'schemes', 
    subCategory: 'Housing', 
    title: 'PM Awas Yojana', 
    description: 'Provides affordable housing subsidies to the urban and rural poor.',
    fullDetails: 'Pradhan Mantri Awas Yojana (PMAY) aims to provide "Housing for All". It offers upfront interest subsidies on housing loans for purchasing, constructing, or upgrading a house. Beneficiaries are categorized into EWS, LIG, and MIG. The subsidy is credited directly to the loan account, reducing the EMI burden.'
  },
  { 
    id: 's5', 
    category: 'schemes', 
    subCategory: 'Women-focused', 
    title: 'PM Ujjwala Yojana', 
    description: 'Provides LPG connection subsidies to women from below poverty line (BPL) households.',
    fullDetails: 'Pradhan Mantri Ujjwala Yojana safeguards the health of women and children by providing them with clean cooking fuel (LPG). It offers a deposit-free LPG connection in the name of an adult woman of a BPL household. Applicants need an Aadhaar card, ration card, and bank account details.'
  },
  { 
    id: 's6', 
    category: 'schemes', 
    subCategory: 'Pension', 
    title: 'PM Vaya Vandana Yojana', 
    description: 'A pension scheme exclusively for senior citizens providing an assured return.',
    fullDetails: 'Pradhan Mantri Vaya Vandana Yojana (PMVVY) is meant for senior citizens aged 60 and above. Operated by LIC, it offers a guaranteed payout of pension at a specified rate for 10 years. It provides regular income security and allows for a loan up to 75% of the purchase price after 3 years for emergencies.'
  },
  { 
    id: 's7', 
    category: 'schemes', 
    subCategory: 'Insurance', 
    title: 'PM Fasal Bima Yojana', 
    description: 'Crop insurance service for farmers for their yields, aiming to stabilize farmer income.',
    fullDetails: 'Pradhan Mantri Fasal Bima Yojana (PMFBY) protects farmers against crop failure due to natural calamities, pests, or diseases. Farmers pay a very low uniform premium (2% for Kharif crops, 1.5% for Rabi, 5% for commercial/horticultural crops), and the government covers the rest. This ensures financial stability for farmers during bad agricultural seasons.'
  },
  { 
    id: 's8', 
    category: 'schemes', 
    subCategory: 'Insurance', 
    title: 'PM Suraksha Bima Yojana', 
    description: 'Accident insurance scheme offering accidental death and disability cover at a very low premium.',
    fullDetails: 'Pradhan Mantri Suraksha Bima Yojana (PMSBY) is an accident insurance scheme offering a cover of ₹2 lakh for accidental death and full disability, and ₹1 lakh for partial disability, for an annual premium of just ₹20. It is available to people between 18 and 70 years with a bank account, through auto-debit.'
  },
  { 
    id: 's9', 
    category: 'schemes', 
    subCategory: 'Pension', 
    title: 'National Pension System (NPS)', 
    description: 'A voluntary, defined contribution retirement savings scheme.',
    fullDetails: 'NPS is a highly regulated, low-cost retirement savings scheme. You contribute regularly during your working life and can withdraw a portion as a lump sum upon retirement, while the rest is used to buy an annuity that provides a regular monthly pension. It also offers significant tax benefits under Section 80C and 80CCD(1B).'
  },

  // Fraud Protection
  { 
    id: 'f1', 
    category: 'fraud', 
    subCategory: 'Call Scams', 
    title: 'Fake Loan Approval Calls', 
    description: 'Scammers call offering instant loan approvals but demand an upfront "processing fee". Never pay to get a loan.',
    fullDetails: 'Warning Signs: You receive a call from someone claiming to be from a reputed bank or finance company offering a massive loan at incredibly low interest rates, even without checking your CIBIL score. They then demand a "file charge" or "processing fee" via UPI before disbursing the loan. \n\nWhat to do: Disconnect immediately. Genuine banks deduct processing fees directly from the approved loan amount, they NEVER ask you to pay it upfront via UPI.'
  },
  { 
    id: 'f2', 
    category: 'fraud', 
    subCategory: 'Online/Digital Scams', 
    title: 'KYC Update Scams', 
    description: 'Fraudsters send messages claiming your account will be blocked unless you click a link to update KYC. Always contact your bank directly.',
    fullDetails: 'Warning Signs: An urgent SMS or WhatsApp message warning that your bank account, SIM card, or electricity connection will be blocked today if you don\'t update your KYC by clicking a provided link. The link often leads to a fake login page designed to steal your net banking credentials or asks you to download a screen-sharing app like AnyDesk.\n\nWhat to do: Do not click the link or download any app. Banks never send links to update KYC. Visit your home branch or use the official banking app.'
  },
  { 
    id: 'f3', 
    category: 'fraud', 
    subCategory: 'Message/SMS Scams', 
    title: 'Fake Job Offers', 
    description: 'Scammers offer high-paying jobs via SMS or WhatsApp but ask for a "registration fee" first.',
    fullDetails: 'Warning Signs: You receive an unsolicited message offering a part-time job (like liking YouTube videos or reviewing hotels) that pays thousands of rupees a day. They might even pay you a small amount initially to build trust. Then, they ask you to deposit money for "premium tasks" or a "security deposit".\n\nWhat to do: Block the sender. Legitimate employers pay you for work; they never ask you to pay them to start working.'
  },
  { 
    id: 'f4', 
    category: 'fraud', 
    subCategory: 'Online/Digital Scams', 
    title: 'SIM Swap Fraud', 
    description: 'Scammers upgrade your SIM to get access to your OTPs. Beware if your phone suddenly loses signal for a long time.',
    fullDetails: 'Warning Signs: Your mobile phone network suddenly disappears for an extended period, especially in an area where you usually have good coverage. This might mean a scammer has convinced your telecom provider to issue a duplicate SIM in your name, rendering your active SIM useless. They now receive all your banking OTPs.\n\nWhat to do: Immediately contact your telecom operator using another phone to verify your SIM status. If compromised, contact your bank instantly to freeze your accounts.'
  },
  { 
    id: 'f5', 
    category: 'fraud', 
    subCategory: 'Message/SMS Scams', 
    title: 'OTP Sharing Scams', 
    description: 'Never share your OTP with anyone over a call. Bank officials will never ask for your OTP.',
    fullDetails: 'Warning Signs: Someone calls posing as a bank official, police officer, or telecom executive, creating a sense of panic (e.g., "your card is blocked" or "suspicious activity detected"). To "verify" your identity or "cancel" a transaction, they ask for the OTP sent to your phone.\n\nWhat to do: Hang up. OTP (One Time Password) is your digital signature. No legitimate institution will ever ask you to read out an OTP over the phone. Sharing it gives the scammer direct access to your money.'
  },

  // Banking Safety
  { 
    id: 'b1', 
    category: 'banking', 
    subCategory: 'Digital Payments', 
    title: 'UPI Safety', 
    description: 'You only need to enter your UPI PIN to SEND money, never to receive money. Do not enter your PIN to receive a payment.',
    fullDetails: 'Key Rule: UPI PIN is strictly for debiting (sending) money from your account. If someone wants to send you money, you only need to provide your UPI ID or phone number. If an app prompts you to enter your 4 or 6 digit UPI PIN and the button says "Pay", money will be deducted from your account, regardless of what the person on the phone claims.'
  },
  { 
    id: 'b2', 
    category: 'banking', 
    subCategory: 'Accounts & Deposits', 
    title: 'Fixed vs Recurring Deposits', 
    description: 'Fixed Deposits (FD) are a lump-sum investment, while Recurring Deposits (RD) involve depositing a fixed amount every month.',
    fullDetails: 'Fixed Deposit (FD): You deposit a large sum of money once for a fixed tenure (e.g., 1 year, 5 years) and earn a higher interest rate than a savings account. It\'s ideal if you have a lump sum saved up.\n\nRecurring Deposit (RD): You deposit a fixed, smaller amount every month for a set tenure. It earns interest similar to an FD and is a great way to build a habit of saving regularly if you don\'t have a lump sum.'
  },
  { 
    id: 'b3', 
    category: 'banking', 
    subCategory: 'Credit & Loans', 
    title: 'CIBIL Score', 
    description: 'A 3-digit number summarizing your credit history. A higher score (above 750) improves your chances of loan approval.',
    fullDetails: 'Your CIBIL score ranges from 300 to 900. It tracks how responsibly you handle credit (loans and credit cards). \n\nHow to keep it high: Always pay your EMIs and credit card bills on or before the due date. Don\'t exhaust your entire credit card limit every month. A score above 750 makes it much easier to get loans approved quickly and at lower interest rates.'
  },
  { 
    id: 'b4', 
    category: 'banking', 
    subCategory: 'Accounts & Deposits', 
    title: 'Minimum Balance', 
    description: 'Many savings accounts require you to maintain a minimum average balance to avoid penalty charges.',
    fullDetails: 'Most regular bank accounts require an Average Monthly Balance (AMB). If your balance falls below this limit, the bank charges a penalty fee. \n\nTip: If you cannot maintain a balance, ask your bank to convert your account to a Basic Savings Bank Deposit Account (BSBDA) or open a PM Jan Dhan account, which strictly have zero minimum balance requirements.'
  },
  { 
    id: 'b5', 
    category: 'banking', 
    subCategory: 'Digital Payments', 
    title: 'NEFT, RTGS, IMPS', 
    description: 'NEFT is for regular transfers, RTGS is for large amounts (2 lakh+), and IMPS is for instant 24x7 transfers.',
    fullDetails: 'IMPS (Immediate Payment Service): Instant transfer, available 24x7. Usually has a lower maximum transfer limit and might incur a small fee.\n\nNEFT (National Electronic Funds Transfer): Transfers happen in batches throughout the day. No minimum limit, but it may take a few hours for the money to reflect.\n\nRTGS (Real Time Gross Settlement): Used for high-value transactions. The minimum transfer amount must be ₹2 lakhs. The transfer is continuous and real-time during banking hours.'
  },
  { 
    id: 'b6', 
    category: 'banking', 
    subCategory: 'Accounts & Deposits', 
    title: 'Bank Lockers', 
    description: 'A secure facility provided by banks to store your valuables and important documents for an annual fee.',
    fullDetails: 'Banks offer safe deposit lockers in various sizes. You pay an annual rent based on the size and location. You get one key, and the bank keeps the master key—both are needed to open it.\n\nImportant: The RBI mandates that banks have a board-approved policy for lockers, but banks generally bear limited liability for the contents inside. It is still much safer than keeping valuables at home.'
  },

  // Complaint Helpline
  { 
    id: 'h1', 
    category: 'helpline', 
    subCategory: 'Cyber Crime', 
    title: 'National Cyber Fraud Helpline', 
    description: 'Dial 1930 immediately if you suspect any financial cyber fraud to report the incident and attempt to freeze the funds.',
    fullDetails: 'The 1930 helpline is a critical resource managed by the Ministry of Home Affairs. If you realize you have been scammed online (money deducted without your consent), call 1930 immediately. The faster you call (ideally within 2-3 hours), the higher the chance that the authorities can trace the transaction and freeze the stolen funds in the scammer\'s account before they withdraw it.'
  },
  { 
    id: 'h2', 
    category: 'helpline', 
    subCategory: 'Cyber Crime', 
    title: 'Cybercrime Portal', 
    description: 'Register cyber complaints officially at cybercrime.gov.in.',
    fullDetails: 'The National Cyber Crime Reporting Portal (cybercrime.gov.in) is an initiative of the Government of India. You can file complaints about financial fraud, identity theft, cyberbullying, or any other cyber crime online. Keep evidence like screenshots, bank statements, and transaction IDs ready when filing your report.'
  },
  { 
    id: 'h3', 
    category: 'helpline', 
    subCategory: 'Financial Fraud', 
    title: 'Block Lost Cards', 
    description: 'Immediately call your bank\'s customer care to block your debit/credit card if it is lost or stolen.',
    fullDetails: 'If you lose your debit or credit card, do not wait. Call your bank\'s official toll-free customer care number immediately to block it permanently. You can also block it using your mobile banking app or net banking portal under the "Card Services" section. This prevents unauthorized contactless (tap-and-pay) or international transactions.'
  },
  { 
    id: 'h4', 
    category: 'helpline', 
    subCategory: 'Banking Complaint', 
    title: 'Banking Ombudsman', 
    description: 'If your bank doesn\'t resolve your complaint within 30 days, you can file a complaint with the RBI Banking Ombudsman.',
    fullDetails: 'The Reserve Bank of India (RBI) operates the Banking Ombudsman scheme. If you have a grievance against a bank (e.g., unauthorized charges, failed ATM transaction but money deducted, rude behavior) and the bank hasn\'t resolved it or replied satisfactorily within 30 days of your written complaint, you can escalate it to the Ombudsman for free online via the RBI CMS portal (cms.rbi.org.in).'
  },
];
