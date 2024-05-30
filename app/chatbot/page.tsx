"use client";

import axios from 'axios';
import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';

interface Message {
    text: string;
    sender: 'user' | 'bot';
}

const ChatBotPage: React.FC = () => {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState('');
    const router = useRouter();

    useEffect(() => {
        const startConversation = async () => {
            try {
                const response = await axios.post('/api/chatbot/start');
                setMessages([{ text: response.data.message, sender: 'bot' }]);
            } catch (error) {
                console.error('Error starting conversation:', error);
            }
        };

        startConversation();
    }, []);

    const handleInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        setInput(event.target.value);
    };

    const handleSubmit = async (event: React.FormEvent) => {
        event.preventDefault();
        if (!input.trim()) return;

        const userMessage: Message = { text: input, sender: 'user' };
        setMessages((prevMessages) => [...prevMessages, userMessage]);
        setInput('');

        try {
            const response = await axios.post('/api/chatbot/conv', { message: input });
            console.log(response)
            setMessages((prevMessages) => [
                ...prevMessages,
                userMessage,
                { text: response.data.message, sender: 'bot' }
            ]);
        } catch (error) {
            console.error('Error sending message:', error);
        }
    };

    const handleEndConversation = async () => {
        try {
            await axios.post('/api/chatbot/end');
            router.push('/fileLoading');
        } catch (error) {
            console.error('Error ending conversation:', error);
        }
    };

    return (
        <main className="flex justify-center items-center h-screen">
            <div className="bg-gradient-to-r from-green-400 via-transparent to-transparent rounded-lg shadow-lg p-10 w-3/4 max-w-3xl">
                <div className="chat-container mb-4 overflow-y-auto h-96">
                    {messages.map((msg, index) => (
                        <div key={index} className={`message p-2 mb-2 rounded ${msg.sender === 'user' ? 'bg-green-200 text-right' : 'bg-gray-200'}`}>
                            {msg.text}
                        </div>
                    ))}
                </div>
                <form onSubmit={handleSubmit} className="flex">
                    <input
                        type="text"
                        value={input}
                        onChange={handleInputChange}
                        className="flex-grow p-2 border border-gray-300 rounded-l-md text-black"
                        placeholder="Type your message..."
                    />
                    <button type="submit" className="bg-green-500 text-white p-2 rounded-r-md">Send</button>
                </form>
                <button onClick={handleEndConversation} className="bg-red-500 text-white p-2 rounded mt-4">End Conversation</button>
            </div>
        </main>
    );
};

export default ChatBotPage;