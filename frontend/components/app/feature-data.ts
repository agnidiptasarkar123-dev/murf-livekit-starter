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
    description: 'National mission for financial inclusion to ensure access to financial services in an affordable manner.',
    fullDetails: 'The Pradhan Mantri Jan Dhan Yojana (PMJDY) is a national mission to ensure every Indian household has at least one basic banking account. Any Indian citizen aged 10 years and above is eligible to open an account. The key benefits include zero minimum balance requirement, a free RuPay debit card, and built-in accident insurance cover of ₹2 lakh. To apply, you can visit any bank branch or a designated Business Correspondent (Bank Mitra) outlet with basic KYC documents like your Aadhaar card.'
  },
  { 
    id: 's2', 
    category: 'schemes', 
    subCategory: 'Credit & Loans', 
    title: 'Mudra Yojana (PMMY)', 
    description: 'Provides loans up to 10 lakhs to non-corporate, non-farm small/micro enterprises.',
    fullDetails: 'The Pradhan Mantri Mudra Yojana (PMMY) helps individuals and small business owners get collateral-free loans to start or expand their businesses. It is available to any Indian citizen who has a business plan for a non-farm income-generating activity. The scheme offers three loan categories: Shishu (up to ₹50,000), Kishore (₹50,000 to ₹5 lakh), and Tarun (₹5 lakh to ₹10 lakh). You can apply for a Mudra loan at any commercial bank, Regional Rural Bank (RRB), small finance bank, or directly through the Udyamimitra portal.'
  },
  { 
    id: 's3', 
    category: 'schemes', 
    subCategory: 'Pension', 
    title: 'Atal Pension Yojana', 
    description: 'A pension scheme primarily focused on unorganized sector workers, providing a guaranteed minimum pension.',
    fullDetails: 'The Atal Pension Yojana (APY) provides a guaranteed minimum monthly pension ranging from ₹1,000 to ₹5,000 after reaching the age of 60. It is open to all bank account holders aged between 18 and 40 years. The key benefit is financial security in old age, with the added guarantee that if the subscriber passes away, the spouse will continue to receive the pension. To apply, simply contact the bank where you hold your savings account and fill out the APY registration form.'
  },
  { 
    id: 's4', 
    category: 'schemes', 
    subCategory: 'Housing', 
    title: 'PM Awas Yojana', 
    description: 'Provides affordable housing subsidies to the urban and rural poor.',
    fullDetails: 'The Pradhan Mantri Awas Yojana (PMAY) aims to provide affordable housing for all by offering upfront interest subsidies on housing loans. It is targeted at Economically Weaker Sections (EWS), Lower Income Groups (LIG), and Middle Income Groups (MIG) who do not already own a pucca house. The main benefit is a significant reduction in the EMI burden, as the subsidy is credited directly to the loan account. You can apply for PMAY through your lending bank or housing finance company when taking a home loan.'
  },
  { 
    id: 's5', 
    category: 'schemes', 
    subCategory: 'Women-focused', 
    title: 'PM Ujjwala Yojana', 
    description: 'Provides LPG connection subsidies to women from below poverty line (BPL) households.',
    fullDetails: 'The Pradhan Mantri Ujjwala Yojana safeguards the health of women and children by providing them with clean cooking fuel. It offers a deposit-free LPG connection in the name of an adult woman belonging to a Below Poverty Line (BPL) household. The primary benefit is reducing health hazards associated with cooking based on fossil fuels. Eligible women can apply by submitting a filled-in application form at any authorized LPG distributor along with their Aadhaar card, ration card, and bank account details.'
  },
  { 
    id: 's6', 
    category: 'schemes', 
    subCategory: 'Pension', 
    title: 'PM Vaya Vandana Yojana', 
    description: 'A pension scheme exclusively for senior citizens providing an assured return.',
    fullDetails: 'The Pradhan Mantri Vaya Vandana Yojana (PMVVY) is a retirement scheme operated by the Life Insurance Corporation of India (LIC). It is exclusively available to senior citizens aged 60 years and above. The scheme offers a guaranteed pension payout at a specified interest rate for a tenure of 10 years, ensuring regular income security. It also allows for premature withdrawal for medical emergencies. You can purchase this policy directly through LIC, either online or offline.'
  },
  { 
    id: 's7', 
    category: 'schemes', 
    subCategory: 'Insurance', 
    title: 'PM Fasal Bima Yojana', 
    description: 'Crop insurance service for farmers for their yields, aiming to stabilize farmer income.',
    fullDetails: 'The Pradhan Mantri Fasal Bima Yojana (PMFBY) is a comprehensive crop insurance scheme that protects farmers against crop failure due to natural calamities, pests, or diseases. All farmers, including sharecroppers and tenant farmers growing notified crops, are eligible. Farmers pay a very low premium (2% for Kharif, 1.5% for Rabi crops), with the government covering the remaining cost, ensuring financial stability during bad agricultural seasons. Farmers can apply through their bank branches, Common Service Centres (CSCs), or the official PMFBY portal.'
  },
  { 
    id: 's8', 
    category: 'schemes', 
    subCategory: 'Insurance', 
    title: 'PM Suraksha Bima Yojana', 
    description: 'Accident insurance scheme offering accidental death and disability cover at a very low premium.',
    fullDetails: 'The Pradhan Mantri Suraksha Bima Yojana (PMSBY) provides highly affordable accident insurance cover. It is available to people between 18 and 70 years of age who have a bank or post office account. The scheme offers a cover of ₹2 lakh for accidental death and full disability, and ₹1 lakh for partial disability, for an annual premium of just ₹20. The premium is automatically deducted from your bank account every year. You can enroll by submitting a consent form at your bank branch.'
  },
  { 
    id: 's9', 
    category: 'schemes', 
    subCategory: 'Pension', 
    title: 'National Pension System (NPS)', 
    description: 'A voluntary, defined contribution retirement savings scheme.',
    fullDetails: 'The National Pension System (NPS) is a regulated, low-cost retirement savings scheme. Any Indian citizen between the ages of 18 and 70 can join. You contribute regularly during your working life, and upon retirement, you can withdraw a portion as a lump sum while the rest is used to buy an annuity for a regular monthly pension. It offers significant tax benefits under Section 80C and Section 80CCD(1B). You can open an NPS account online via the eNPS portal or through authorized banks and post offices.'
  },

  // Fraud Protection
  { 
    id: 'f1', 
    category: 'fraud', 
    subCategory: 'Call Scams', 
    title: 'Fake Loan Approval Calls', 
    description: 'Scammers call offering instant loan approvals but demand an upfront "processing fee".',
    fullDetails: 'In this scam, fraudsters call pretending to be from a reputed bank or finance company, offering a massive loan at incredibly low interest rates, often claiming no CIBIL score check is required. The major warning sign is when they demand an upfront "file charge" or "processing fee" via UPI before they can disburse the loan amount. If this happens, disconnect immediately. Genuine banks always deduct processing fees directly from the approved loan amount and will never ask you to pay it upfront via a UPI transfer.'
  },
  { 
    id: 'f2', 
    category: 'fraud', 
    subCategory: 'Online/Digital Scams', 
    title: 'KYC Update Scams', 
    description: 'Fraudsters send urgent messages claiming your account will be blocked unless you click a link to update KYC.',
    fullDetails: 'This fraud pattern involves receiving an urgent SMS or WhatsApp message warning that your bank account, SIM card, or electricity connection will be blocked today if you do not click a link to update your KYC. The link often leads to a fake login page designed to steal your net banking credentials, or they may ask you to download a screen-sharing app. The key warning sign is the manufactured sense of urgency and the inclusion of a suspicious link. Do not click any links or download apps; instead, directly contact your bank or visit your home branch.'
  },
  { 
    id: 'f3', 
    category: 'fraud', 
    subCategory: 'Message/SMS Scams', 
    title: 'Fake Job Offers', 
    description: 'Scammers offer high-paying jobs via SMS or WhatsApp but ask for a "registration fee" first.',
    fullDetails: 'Scammers send unsolicited messages offering easy, high-paying part-time jobs, such as liking YouTube videos or reviewing hotels online. They often pay you a small amount initially to build trust, which is a major warning sign. Eventually, they will ask you to deposit a "registration fee" or pay for "premium tasks" to unlock larger earnings, and then disappear with your money. If you receive such offers, block the sender immediately. Remember that legitimate employers pay you for your work and will never ask you to pay them to start working.'
  },
  { 
    id: 'f4', 
    category: 'fraud', 
    subCategory: 'Online/Digital Scams', 
    title: 'SIM Swap Fraud', 
    description: 'Scammers upgrade or clone your SIM card to get access to your banking OTPs.',
    fullDetails: 'In a SIM swap fraud, a scammer convinces your telecom provider to issue a duplicate SIM in your name, which instantly deactivates your current SIM card. The critical warning sign is if your mobile phone network suddenly disappears completely for an extended period, especially in an area where you normally have coverage. The scammer does this so they can receive all your banking OTPs. If you lose signal unexpectedly, immediately contact your telecom operator from another phone to verify your SIM status, and call your bank to freeze your accounts if compromised.'
  },
  { 
    id: 'f5', 
    category: 'fraud', 
    subCategory: 'Message/SMS Scams', 
    title: 'OTP Sharing Scams', 
    description: 'Fraudsters call to panic you and ask for an OTP. Bank officials will never ask for your OTP.',
    fullDetails: 'Fraudsters call posing as a bank official, police officer, or telecom executive, trying to create a sense of panic by claiming your card is blocked or suspicious activity was detected. The warning sign is when they ask you to read out an OTP sent to your phone to "verify" your identity or "cancel" a transaction. If this happens, hang up the phone immediately. An OTP is your digital signature, and no legitimate institution will ever ask you to read it out over a call. Sharing it gives the scammer direct access to your funds.'
  },

  // Banking Safety
  { 
    id: 'b1', 
    category: 'banking', 
    subCategory: 'Digital Payments', 
    title: 'UPI Safety', 
    description: 'You only need to enter your UPI PIN to SEND money, never to receive money.',
    fullDetails: 'UPI (Unified Payments Interface) is a system that powers multiple bank accounts into a single mobile application, allowing instant fund routing. The most important safety concept to understand is that your UPI PIN is strictly used for debiting (sending) money from your account. It matters because scammers often trick people into entering their PIN by claiming it is required to receive a refund or payment. The key practical tip is: if you are receiving money, you only need to provide your phone number or UPI ID. Never enter your PIN to receive funds.'
  },
  { 
    id: 'b2', 
    category: 'banking', 
    subCategory: 'Accounts & Deposits', 
    title: 'Fixed vs Recurring Deposits', 
    description: 'Fixed Deposits are a lump-sum investment, while Recurring Deposits involve depositing a fixed amount monthly.',
    fullDetails: 'A Fixed Deposit (FD) requires you to deposit a large, lump sum of money once for a fixed tenure, earning a higher interest rate than a regular savings account. A Recurring Deposit (RD) allows you to deposit a fixed, smaller amount every month for a set tenure, earning similar interest rates to an FD. Understanding the difference matters for planning your savings. Use an FD if you already have a lump sum saved up, and use an RD to build a habit of saving regularly out of your monthly income.'
  },
  { 
    id: 'b3', 
    category: 'banking', 
    subCategory: 'Credit & Loans', 
    title: 'CIBIL Score', 
    description: 'A 3-digit number summarizing your credit history. A higher score improves loan approval chances.',
    fullDetails: 'Your CIBIL score is a 3-digit number, ranging from 300 to 900, that summarizes your credit history and tracks how responsibly you handle loans and credit cards. It matters immensely because banks use this score to decide whether to approve your loan applications and at what interest rate. A higher score (above 750) makes it much easier to get loans approved quickly and cheaply. To keep your score high, always pay your EMIs and credit card bills on or before the due date, and avoid exhausting your entire credit limit.'
  },
  { 
    id: 'b4', 
    category: 'banking', 
    subCategory: 'Accounts & Deposits', 
    title: 'Minimum Balance', 
    description: 'Many savings accounts require you to maintain a minimum average balance to avoid penalty charges.',
    fullDetails: 'Most regular bank accounts require you to maintain an Average Monthly Balance (AMB). This concept matters because if your account balance falls below this stipulated limit, the bank will charge you a penalty fee, slowly eating into your savings. A practical tip: if you find it difficult to maintain a minimum balance, ask your bank to convert your account to a Basic Savings Bank Deposit Account (BSBDA) or open a PM Jan Dhan account, both of which legally have strict zero minimum balance requirements.'
  },
  { 
    id: 'b5', 
    category: 'banking', 
    subCategory: 'Digital Payments', 
    title: 'NEFT, RTGS, IMPS', 
    description: 'Different methods for electronic money transfer, each with specific limits and timings.',
    fullDetails: 'These are the three main systems for transferring money electronically in India. IMPS offers instant, 24x7 transfers for everyday amounts. NEFT transfers happen in batches throughout the day with no minimum limit, so it may take a few hours for the money to reflect. RTGS is used exclusively for high-value transactions, requiring a minimum transfer amount of ₹2 lakhs, and settles in real-time during banking hours. Understanding these helps you choose the right transfer method based on how urgently the money needs to reach the recipient and the transfer amount.'
  },
  { 
    id: 'b6', 
    category: 'banking', 
    subCategory: 'Accounts & Deposits', 
    title: 'Bank Lockers', 
    description: 'A secure facility provided by banks to store your valuables and important documents.',
    fullDetails: 'Banks offer safe deposit lockers in various sizes where you can store valuables and important documents for an annual rent. This matters because it provides a much more secure environment than keeping valuables at home, protecting them from theft or natural disasters. You are provided with one key, and the bank keeps a master key; both are required to open the locker. A practical tip is to ensure you nominate a family member for the locker and visit it at least once a year to keep it active as per banking regulations.'
  },

  // Complaint Helpline
  { 
    id: 'h1', 
    category: 'helpline', 
    subCategory: 'Cyber Crime', 
    title: 'National Cyber Fraud Helpline', 
    description: 'Dial 1930 immediately if you suspect any financial cyber fraud to report the incident.',
    fullDetails: 'The 1930 helpline is a critical, rapid-response resource managed by the Ministry of Home Affairs specifically for financial cyber frauds. It covers incidents where money has been deducted from your account without your consent via UPI, credit cards, or net banking. You should use it the moment you realize you have been scammed. By calling 1930 quickly (ideally within 2 to 3 hours), the authorities can trace the electronic transaction and attempt to freeze the stolen funds in the scammer\'s account before they can withdraw it.'
  },
  { 
    id: 'h2', 
    category: 'helpline', 
    subCategory: 'Cyber Crime', 
    title: 'Cybercrime Portal', 
    description: 'Register cyber complaints officially online at cybercrime.gov.in.',
    fullDetails: 'The National Cyber Crime Reporting Portal (cybercrime.gov.in) is an official initiative of the Government of India. It covers all forms of cyber crime, including financial fraud, identity theft, and cyberbullying. You should use this portal to file a formal, detailed written complaint after calling 1930, or if you need to report non-financial cyber crimes. You can reach it by visiting the website from any browser. Be sure to keep evidence like screenshots, bank statements, and transaction IDs ready to upload when filing your report.'
  },
  { 
    id: 'h3', 
    category: 'helpline', 
    subCategory: 'Financial Fraud', 
    title: 'Block Lost Cards', 
    description: 'Immediately call your bank\'s customer care to block your debit/credit card if it is lost or stolen.',
    fullDetails: 'This is the immediate action you must take if you lose your physical debit or credit card, or if you suspect its details have been compromised. This process covers permanently blocking the card from any further use, preventing unauthorized contactless (tap-and-pay) or international transactions. You should use this the exact moment you realize your card is missing. You can reach this service by calling your specific bank\'s official toll-free customer care number, or by using the "Card Services" section within your mobile banking app.'
  },
  { 
    id: 'h4', 
    category: 'helpline', 
    subCategory: 'Banking Complaint', 
    title: 'Banking Ombudsman', 
    description: 'If your bank doesn\'t resolve your complaint within 30 days, file a complaint with the RBI.',
    fullDetails: 'The Banking Ombudsman scheme is operated by the Reserve Bank of India (RBI) to resolve customer grievances. It covers issues like unauthorized charges, failed ATM transactions where money was deducted, or unsatisfactory customer service by your bank. You should use this only if you have already filed a formal written complaint with your bank and they have either rejected it or failed to provide a satisfactory resolution within 30 days. You can reach the Ombudsman and file a complaint for free online via the RBI CMS portal (cms.rbi.org.in).'
  },
];
