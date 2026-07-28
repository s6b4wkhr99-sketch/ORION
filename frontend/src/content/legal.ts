/**
 * Legal & Privacy — Le Frame Inc.
 * Adapted from Le Frame V2 (`Le Frame V2/src/content/legal.ts`) for CIOS/ORION platforms.
 */

import type { LegalPageContent } from "./legal-types";

export const LEGAL_CONTACT_EMAIL = "Infor@leframeworks.com" as const;
export const LEGAL_ENTITY_NAME = "Le Frame Inc." as const;

export const legalMeta = {
  lastUpdated: "July 25, 2026",
};

export const legalPages = {
  privacy: { title: "Privacy Policy", slug: "privacy" },
  terms: { title: "Terms of Use", slug: "terms" },
  legal: { title: "Legal Notice", slug: "legal" },
};

export const privacyPolicy: LegalPageContent = {
  lastUpdated: legalMeta.lastUpdated,
  sections: [
    {
      title: "Introduction",
      content: [
        `PLEASE READ THIS PRIVACY POLICY ("POLICY") CAREFULLY. ${LEGAL_ENTITY_NAME} ("Le Frame," "we," "our," or "us") respects your privacy and is committed to protecting personal information processed through the Customer Intelligence Operating System (CIOS) and related authorized Le Frame intelligence platforms (collectively, the "Platform").`,
        "This Policy explains how we collect, use, disclose, retain, and safeguard personal information when authorized users access the Platform. By accessing or using the Platform, you confirm that you have read, understand, and acknowledge this Policy.",
        "This Policy is written to align with modern U.S. privacy expectations and, where applicable, state privacy laws including CCPA/CPRA-style consumer rights for individuals whose information is processed through the Platform.",
      ],
    },
    {
      title: "1. Who Is Responsible for Personal Information",
      content: [
        `${LEGAL_ENTITY_NAME} is responsible for operating CIOS and for personal information collected through or in connection with the Platform, except where your organization acts as the controller of uploaded customer records and Le Frame processes such data solely on your organization's instructions under applicable agreement.`,
        `For privacy-related inquiries, contact: ${LEGAL_CONTACT_EMAIL}. Data-subject requests relating to information your organization uploaded should generally be directed to your organization's system administrator first.`,
      ],
    },
    {
      title: "2. Personal Information We Collect",
      content: [
        'When we refer to "personal information" in this Policy, we mean information that relates to an identifiable individual (for example, name, contact details, account identifiers, or customer records that contain personal information).',
        "a. Information You Provide Directly — When you use the Platform, you may provide: name, company name, job title, email address, account credentials, role and permission settings, support inquiries, and configuration choices.",
        "b. Business Customer Data (CIOS) — Where authorized by your organization, users may upload or process business customer records for intelligence analysis. This may include contact identifiers (such as email), geographic attributes (state, ZIP), segment classifications, commercial attributes, and derived intelligence outputs (scores, recommendations, campaign priorities).",
        "c. Information Collected Automatically — When you access the Platform, we may automatically collect: IP address, browser type, device type, operating system, session identifiers, pages or modules viewed, date and time of access, authentication events, and error or performance logs.",
        "d. Cookies and Similar Technologies — We may use cookies, local storage, or similar technologies necessary for authentication, session management, security, and Platform functionality. We do not use the Platform primarily for consumer advertising profiles.",
      ],
    },
    {
      title: "3. How We Use Personal Information",
      content: [
        "We use personal information for the following purposes:",
        "a. Provide the Platform — authenticate users, enforce role-based access, operate dashboards and intelligence modules, process uploads, generate rollups and recommendations, and deliver exports or reports authorized by your organization.",
        "b. Security and Integrity — monitor for unauthorized access, investigate suspicious activity, maintain audit logs, protect accounts, and preserve Platform availability.",
        "c. Improve and Support the Platform — troubleshoot errors, analyze aggregated usage patterns, improve performance, and respond to support requests.",
        "d. Legal and Compliance — comply with applicable laws, respond to lawful requests, enforce our terms, and protect the rights, safety, and property of Le Frame, our clients, and Platform users.",
        "We do not sell personal information processed through CIOS. We do not use uploaded customer records for unrelated third-party marketing.",
      ],
    },
    {
      title: "4. Disclosure and Sharing",
      content: [
        "We may share personal information in limited circumstances:",
        "a. Service Providers — hosting, database, backup, monitoring, email, or professional services vendors that help us operate the Platform under contractual confidentiality and security obligations.",
        "b. Your Organization — information uploaded or generated within your organization's workspace is available to authorized users and administrators within that deployment, subject to role permissions.",
        "c. Legal Requirements — where required by law, regulation, legal process, or governmental request, or where necessary to investigate fraud, security incidents, or violations of applicable terms.",
        "d. Business Transfers — in connection with a merger, acquisition, reorganization, or sale of assets, subject to applicable law and notice requirements.",
        "Links to third-party websites or services may appear in the Platform. Those third parties have their own privacy practices, which we do not control.",
      ],
    },
    {
      title: "5. Retention of Personal Information",
      content: [
        "We retain personal information only for as long as reasonably necessary for the purposes described in this Policy, including to provide the Platform, maintain business records, fulfill legal or regulatory obligations, resolve disputes, and enforce agreements.",
        "Retention of uploaded customer datasets may depend on your organization's deployment settings, backup policy, and contractual requirements. When information is no longer needed, we may delete or anonymize it subject to applicable legal and operational requirements.",
      ],
    },
    {
      title: "6. Your Choices",
      content: [
        "Account information may be updated by your organization's administrator or, where permitted, by you through account settings.",
        "If your organization provides opt-out or scope controls for certain processing, those controls will be described in your internal deployment policy or administrator documentation.",
        `You may contact ${LEGAL_CONTACT_EMAIL} with privacy questions. Requests relating to customer records uploaded by your employer or client should generally be routed through that organization's administrator.`,
      ],
    },
    {
      title: "7. Your Rights",
      content: [
        "To the extent required by applicable law, individuals may have rights regarding personal information about them, which may include rights to access, correct, delete, restrict processing, or opt out of certain sharing where applicable.",
        "We will not discriminate against you for exercising privacy rights where prohibited by law. Requests are subject to identity verification, organizational authorization checks, and applicable legal exceptions (for example, where retention is required for security, audit, or legal compliance).",
        `To submit a privacy-related request, contact ${LEGAL_CONTACT_EMAIL}.`,
      ],
    },
    {
      title: "8. How We Protect Personal Information",
      content: [
        "We use reasonable administrative, technical, and organizational safeguards designed to protect personal information from unauthorized access, disclosure, alteration, or destruction, including access controls, authenticated sessions, and operational monitoring appropriate to an enterprise platform.",
        "No method of transmission over the Internet or electronic storage is completely secure. We cannot guarantee absolute security.",
      ],
    },
    {
      title: "9. International Transfer of Information",
      content:
        "If you access the Platform from outside the United States, personal information may be transferred to, stored in, or processed in jurisdictions where data protection laws may differ from those in your location. By using the Platform, you acknowledge such transfers where permitted by applicable law and organizational policy.",
    },
    {
      title: "10. Updates to This Privacy Policy",
      content: [
        "We may update this Policy from time to time to reflect legal, operational, or business changes.",
        'When we do, we will revise the "Last Updated" date above. Continued use of the Platform after changes become effective constitutes acknowledgment of the updated Policy, subject to applicable law.',
      ],
    },
    {
      title: "11. Personal Information of Children",
      content:
        "The Platform is intended for authorized business and professional users and is not directed to children. We do not knowingly collect personal information from children through CIOS.",
    },
    {
      title: "12. Contact Us",
      content: [
        "If you have questions about this Privacy Policy or wish to make a privacy-related request, please contact:",
        LEGAL_ENTITY_NAME,
        `Email: ${LEGAL_CONTACT_EMAIL}`,
      ],
    },
  ],
};

export const termsOfUse: LegalPageContent = {
  lastUpdated: legalMeta.lastUpdated,
  sections: [
    {
      title: "Introduction",
      content: [
        'PLEASE READ THESE TERMS CAREFULLY. THIS IS A BINDING LEGAL AGREEMENT.',
        `These Terms of Use ("Terms") between you ("User" or "you") and ${LEGAL_ENTITY_NAME} ("Le Frame," "we," or "us") govern your access to and use of CIOS and related authorized Le Frame intelligence modules, content, and services enabled through the Platform (collectively, the "Platform Services").`,
        "By accessing or using the Platform Services, you represent that (1) you have read, understand, and agree to be bound by these Terms, (2) you are of legal age to form a binding contract, and (3) you have authority to use the Platform on behalf of yourself or your organization.",
        "IF YOU DO NOT AGREE TO THESE TERMS, YOU MAY NOT ACCESS OR USE THE PLATFORM SERVICES.",
        "We may change these Terms from time to time. When we do, we will revise the Last Updated date above. Material changes may be communicated through the Platform or by email where appropriate. Continued use after changes become effective constitutes acceptance of the revised Terms.",
      ],
    },
    {
      title: "1. Platform Services",
      content: [
        "CIOS provides authorized users with customer intelligence, market analytics, campaign decision support, dashboards, exports, and related enterprise tools.",
        "Features may vary by deployment, role, license, and organization policy. Le Frame does not warrant that all features will be available in every environment or remain available without change.",
        "Supplemental terms applicable to a specific module, upload, or organization agreement take precedence over these Terms if inconsistent.",
      ],
    },
    {
      title: "2. License Grant and Restrictions",
      content: [
        "Subject to your ongoing compliance with these Terms, Le Frame grants you a limited, non-exclusive, non-transferable, non-sublicensable, revocable license to access and use the Platform Services solely for authorized internal business purposes.",
        "You shall not: (a) license, sell, rent, lease, or commercially exploit the Platform Services; (b) copy, modify, reverse engineer, decompile, or create derivative works of the Platform except as permitted by law; (c) scrape, harvest, or use automated means to extract Platform data without authorization; (d) frame or misrepresent Le Frame branding; (e) interfere with Platform security or availability; or (f) use the Platform in violation of applicable law or your organization's policies.",
        "You must provide your own equipment, network access, and supported browser environment necessary to connect to the Platform Services.",
      ],
    },
    {
      title: "3. Account Registration",
      content: [
        "Access to certain Platform features requires an authenticated account. You agree to provide accurate, current, and complete registration information and to keep it updated.",
        "You are responsible for safeguarding your credentials and for all activities under your account. You must notify your administrator or Le Frame promptly if you suspect unauthorized access.",
        "Le Frame may suspend or terminate accounts that provide false information, violate these Terms, or pose a security risk.",
      ],
    },
    {
      title: "4. User Content and Uploaded Data",
      content: [
        '"User Content" includes customer files, records, notes, configurations, and other materials you or your organization upload or submit through the Platform.',
        "You represent that you have all rights necessary to provide User Content and that its use through the Platform does not violate law or third-party rights, including privacy and intellectual property rights.",
        "You are responsible for the accuracy, legality, and appropriateness of User Content. Le Frame may remove or restrict User Content that violates these Terms or applicable law, but has no obligation to monitor all User Content.",
        "Le Frame is not responsible for backup of User Content unless expressly agreed in writing. Your organization is responsible for maintaining appropriate backups and export copies where required.",
      ],
    },
    {
      title: "5. Intelligence Outputs and AI-Based Features",
      content: [
        "The Platform may generate scores, rankings, recommendations, forecasts, and other analytical outputs ('Outputs') using statistical models, rules, metadata, and automated processing.",
        "Outputs are provided for authorized business decision-support purposes only. They may be incomplete, inaccurate, outdated, or not suitable for a particular use case. Outputs do not constitute legal, medical, financial, or other professional advice.",
        "You are solely responsible for independently verifying Outputs before relying on them for commercial, compliance, or customer-facing decisions.",
        "You agree not to represent Outputs as guaranteed facts or human-authored determinations where such representation would be misleading.",
      ],
    },
    {
      title: "6. Intellectual Property Rights",
      content: [
        "The Platform Services, including software, dashboards, frameworks, logos, documentation, visual systems, and underlying methodology, are owned by or licensed to Le Frame and protected by applicable intellectual property laws.",
        "Except for the limited license granted herein, no rights are transferred to you. You may not remove proprietary notices or use Le Frame marks without prior written permission.",
      ],
    },
    {
      title: "7. Third-Party Services",
      content:
        "The Platform may integrate with or link to third-party services, datasets, or websites. Third-party services are not controlled by Le Frame. Your use of third-party services is at your own risk and subject to their terms and privacy policies.",
    },
    {
      title: "8. Enforcement",
      content:
        "If we become aware of possible violations of these Terms, we may investigate and take appropriate action, including suspension of access, removal of User Content, or referral to legal authorities where required. We may disclose information where necessary to comply with law, enforce these Terms, respond to security incidents, or protect users and the Platform.",
    },
    {
      title: "9. Indemnification",
      content:
        "You agree to indemnify and hold harmless Le Frame and its affiliates, officers, employees, and agents from claims, losses, and expenses (including reasonable attorneys' fees) arising from your User Content, your use of the Platform, your violation of these Terms, or your violation of any rights of another party or applicable law, to the extent permitted by law.",
    },
    {
      title: "10. Disclaimer of Warranties",
      content: [
        'TO THE EXTENT PERMITTED BY LAW, THE PLATFORM SERVICES AND OUTPUTS ARE PROVIDED ON AN "AS IS" AND "AS AVAILABLE" BASIS.',
        "LE FRAME DISCLAIMS ALL WARRANTIES, EXPRESS OR IMPLIED, INCLUDING MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, AND NON-INFRINGEMENT.",
        "WE DO NOT WARRANT THAT THE PLATFORM WILL BE UNINTERRUPTED, ERROR-FREE, SECURE, OR THAT RESULTS WILL BE ACCURATE OR RELIABLE.",
      ],
    },
    {
      title: "11. Limitation of Liability",
      content: [
        "TO THE EXTENT PERMITTED BY LAW, LE FRAME WILL NOT BE LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, OR PUNITIVE DAMAGES, OR FOR LOSS OF PROFITS, REVENUE, DATA, OR BUSINESS INTERRUPTION, ARISING FROM OR RELATED TO THE PLATFORM SERVICES.",
        "TO THE EXTENT PERMITTED BY LAW, LE FRAME'S TOTAL LIABILITY FOR ANY CLAIM ARISING OUT OF OR RELATING TO THE PLATFORM SERVICES WILL NOT EXCEED THE GREATER OF (A) AMOUNTS PAID BY YOUR ORGANIZATION TO LE FRAME FOR THE PLATFORM SERVICES IN THE TWELVE (12) MONTHS PRECEDING THE CLAIM, OR (B) ONE HUNDRED U.S. DOLLARS (US $100).",
        "Some jurisdictions do not allow certain limitations; in those cases, limitations apply to the maximum extent permitted by law.",
      ],
    },
    {
      title: "12. Term, Termination, and Survival",
      content: [
        "These Terms remain in effect while you access or use the Platform Services. Your organization or Le Frame may suspend or terminate access in accordance with applicable agreement, security policy, or these Terms.",
        "Upon termination, your right to use the Platform Services ends immediately. Provisions that by their nature should survive termination will survive, including intellectual property, disclaimers, limitations of liability, and indemnification.",
      ],
    },
    {
      title: "13. Governing Law",
      content:
        "These Terms are governed by the laws of the State of New Jersey, United States, without regard to conflict-of-law principles, except where prohibited by applicable law.",
    },
    {
      title: "14. Contact",
      content: [
        "Questions regarding these Terms or the Platform Services may be directed to:",
        LEGAL_ENTITY_NAME,
        `Email: ${LEGAL_CONTACT_EMAIL}`,
      ],
    },
  ],
};

export const legalNotice: LegalPageContent = {
  lastUpdated: legalMeta.lastUpdated,
  sections: [
    {
      title: "1. Platform Owner",
      content: [
        `CIOS and related Le Frame intelligence platforms are owned and operated by ${LEGAL_ENTITY_NAME}.`,
        `For legal or compliance inquiries, contact: ${LEGAL_CONTACT_EMAIL}`,
      ],
    },
    {
      title: "2. Intellectual Property Notice",
      content: [
        "Unless otherwise stated, all materials in this platform—including company name, logos, brand statements, framework language, diagrams, visual systems, text content, software, graphic assets, and interface elements—are the property of Le Frame Inc. or used under appropriate license.",
        "Unauthorized reproduction, distribution, republication, transmission, modification, or commercial exploitation of platform content is prohibited without prior written consent.",
      ],
    },
    {
      title: "3. Trademark Notice",
      content: [
        '"Le Frame," "CIOS," "ORION," and related brand expressions, taglines, frameworks, and graphic identifiers may constitute trademarks, service marks, or proprietary brand assets of Le Frame Inc., whether registered or unregistered, subject to applicable law.',
        "Nothing on this platform should be interpreted as granting any license or right to use such marks without prior written permission.",
      ],
    },
    {
      title: "4. Platform Content Disclaimer",
      content: [
        "Platform content, intelligence outputs, and recommendations are provided for authorized business decision-support purposes and may be modified, updated, or removed at any time without notice.",
        "Le Frame Inc. makes no guarantee that all information presented is complete, current, or free of error.",
      ],
    },
    {
      title: "5. External Links",
      content:
        "Where this platform links to third-party websites or resources, such links are provided for convenience only. Le Frame Inc. does not control and is not responsible for the content, privacy policies, or practices of third-party websites.",
    },
    {
      title: "6. Contact Information",
      content: [
        "For legal or compliance-related inquiries, please contact:",
        LEGAL_ENTITY_NAME,
        `Email: ${LEGAL_CONTACT_EMAIL}`,
        `© ${new Date().getFullYear()} ${LEGAL_ENTITY_NAME} All rights reserved.`,
      ],
    },
  ],
};

export const legalContent = {
  privacy: privacyPolicy,
  terms: termsOfUse,
  legal: legalNotice,
};
