import React, { createContext, useContext, useState, ReactNode } from 'react';
import HowItWorksModal from '@/components/HowItWorksModal';

interface ModalContextType {
    openHowItWorks: () => void;
    closeHowItWorks: () => void;
}

const ModalContext = createContext<ModalContextType | undefined>(undefined);

export function ModalProvider({ children }: { children: ReactNode }) {
    const [isOpen, setIsOpen] = useState(false);

    const openHowItWorks = () => setIsOpen(true);
    const closeHowItWorks = () => setIsOpen(false);

    return (
        <ModalContext.Provider value={{ openHowItWorks, closeHowItWorks }}>
            {children}
            <HowItWorksModal isOpen={isOpen} onClose={closeHowItWorks} />
        </ModalContext.Provider>
    );
}

export function useModal() {
    const context = useContext(ModalContext);
    if (context === undefined) {
        throw new Error('useModal must be used within a ModalProvider');
    }
    return context;
}
