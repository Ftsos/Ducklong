"use client";
import axios from 'axios';
import React from 'react';
import Button from '../components/button';
import { useRouter } from 'next/navigation';

const activitiesPage = () => {
    const router = useRouter(); // Initialize useRouter

    // Handle button clicks
    const handleChatbotClick = () => {
        // Redirect to the chatbot page
        router.push('/chatbot');
    };

    const handleQuizClick = () => {
        // Redirect to the quiz page
        router.push('/quiz');
    };


    return (
        <main>
            <div className="flex justify-center items-center h-screen">
                <div className="bg-gradient-radial from-green-400 via-transparent to-transparent rounded-lg shadow-lg p-20">
                    <h1 className="text-4xl font-bold text-center text-white-600 mb-8">
                        Choose your Practice Activity
                    </h1>
                    <div className="flex justify-center space-x-4">
                        <Button onClick={handleChatbotClick} className={'hover:bg-green-700 transition duration-300'}>Chat-bot</Button>
                        <Button onClick={handleQuizClick} className={'hover:bg-green-700 transition duration-300'}>Quiz</Button>
                    </div>
                </div>
            </div>
        </main>
    );
};

export default activitiesPage;