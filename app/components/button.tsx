import React from 'react';

interface ButtonProps {
    children: React.ReactNode;
    onClick?: (e: any) => void;
    className?: string;
}

const Button: React.FC<ButtonProps> = ({ children, onClick, className = '' }) => {
    return (
        <div className="relative">
            <button
                onClick={onClick}
                className={`inline-block px-6 py-2.5 text-white font-medium text-xs leading-tight uppercase rounded shadow-[rgba(179,227,185,_0.4)_0px_0px_0px_2px,_rgba(179,227,185,_0.65)_0px_4px_6px_-1px,_rgba(179,227,185,_0.08)_0px_1px_0px_inset] relative z-10 ${className}`}
            >
                {children}
            </button>
        </div>
    );
};

export default Button;
