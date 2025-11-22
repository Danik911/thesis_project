export interface ComplianceCard {
    id: string;
    title: string;
    status: 'implemented' | 'planned';
}

export interface Framework {
    id: string;
    fullName: string;
    description: string;
    icon: string;
    cards: ComplianceCard[];
}

export const allFrameworks: Framework[] = [
    {
        id: 'gamp5',
        fullName: 'ISPE GAMP 5 (2nd Edition)',
        description: 'Risk-based approach to compliant GxP computerized systems.',
        icon: '📘',
        cards: [
            { id: 'cat', title: 'Software Categorization', status: 'implemented' },
            { id: 'risk', title: 'Risk Assessment', status: 'implemented' },
            { id: 'trace', title: 'Traceability Matrix', status: 'implemented' },
            { id: 'spec', title: 'Design Specs', status: 'implemented' },
            { id: 'vplan', title: 'Validation Plan', status: 'implemented' },
        ]
    },
    {
        id: 'alcoa',
        fullName: 'ALCOA+ Principles',
        description: 'Data integrity standards for complete, consistent, and accurate data.',
        icon: '🛡️',
        cards: [
            { id: 'att', title: 'Attributable', status: 'implemented' },
            { id: 'leg', title: 'Legible', status: 'implemented' },
            { id: 'con', title: 'Contemporaneous', status: 'implemented' },
            { id: 'org', title: 'Original', status: 'implemented' },
            { id: 'acc', title: 'Accurate', status: 'implemented' },
            { id: 'com', title: 'Complete', status: 'implemented' },
        ]
    },
    {
        id: '21cfr11',
        fullName: 'FDA 21 CFR Part 11',
        description: 'Regulations on electronic records and electronic signatures.',
        icon: '🏛️',
        cards: [
            { id: 'esig', title: 'Electronic Signatures', status: 'implemented' },
            { id: 'audit', title: 'Audit Trails', status: 'implemented' },
            { id: 'sec', title: 'Security Controls', status: 'implemented' },
            { id: 'rec', title: 'Record Retention', status: 'implemented' },
        ]
    },
    {
        id: 'euannex11',
        fullName: 'EU Annex 11',
        description: 'Computerised Systems guideline for GMP in the EU.',
        icon: '🇪🇺',
        cards: [
            { id: 'val', title: 'Validation', status: 'implemented' },
            { id: 'arch', title: 'Archiving', status: 'planned' },
            { id: 'sec', title: 'Security', status: 'implemented' },
        ]
    }
];
